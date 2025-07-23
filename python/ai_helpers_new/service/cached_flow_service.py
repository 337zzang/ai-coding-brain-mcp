import threading
import time
import os
import json
import tempfile
from typing import Dict, Optional, Any, Tuple, List
from datetime import datetime, timedelta
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

from ai_helpers_new.domain.models import Flow, Plan, Task
from ai_helpers_new.exceptions import StorageError, ValidationError

@dataclass
class CacheEntry:
    """캐시 엔트리"""
    data: Any
    mtime: float
    access_time: float
    access_count: int = 0


class FlowCache:
    """Thread-safe Flow 캐시 with TTL, LRU, and statistics"""

    def __init__(self, ttl_seconds: float = 3600, max_size: int = 1000):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._ttl_seconds = ttl_seconds
        self._max_size = max_size

        # 통계
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, flow_id: str) -> Optional[Any]:
        with self._lock:
            entry = self._cache.get(flow_id)

            if entry is None:
                self._misses += 1
                return None

            # TTL 체크
            if self._is_expired(entry):
                self._cache.pop(flow_id, None)
                self._misses += 1
                self._evictions += 1
                return None

            # LRU 업데이트
            entry.access_time = time.time()
            entry.access_count += 1
            self._cache.move_to_end(flow_id)

            self._hits += 1
            return entry.data

    def put(self, flow_id: str, data: Any, mtime: float):
        with self._lock:
            # 크기 제한 체크
            if len(self._cache) >= self._max_size and flow_id not in self._cache:
                # LRU 제거
                oldest = next(iter(self._cache))
                self._cache.pop(oldest)
                self._evictions += 1

            entry = CacheEntry(
                data=data,
                mtime=mtime,
                access_time=time.time()
            )
            self._cache[flow_id] = entry
            self._cache.move_to_end(flow_id)

    def invalidate(self, flow_id: str = None):
        with self._lock:
            if flow_id:
                self._cache.pop(flow_id, None)
            else:
                self._cache.clear()

    def is_valid(self, flow_id: str, current_mtime: float) -> bool:
        with self._lock:
            entry = self._cache.get(flow_id)
            if entry is None:
                return False

            # TTL 체크
            if self._is_expired(entry):
                self._cache.pop(flow_id, None)
                self._evictions += 1
                return False

            # mtime 체크
            return entry.mtime >= current_mtime

    def _is_expired(self, entry: CacheEntry) -> bool:
        """TTL 만료 체크"""
        if self._ttl_seconds <= 0:  # TTL 비활성화
            return False
        return time.time() - entry.access_time > self._ttl_seconds

    def get_statistics(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

            return {
                'hits': self._hits,
                'misses': self._misses,
                'evictions': self._evictions,
                'hit_rate': hit_rate,
                'size': len(self._cache),
                'max_size': self._max_size,
                'ttl_seconds': self._ttl_seconds
            }

    def reset_statistics(self):
        """통계 초기화"""
        with self._lock:
            self._hits = 0
            self._misses = 0
            self._evictions = 0


class CachedFlowService:
    """캐시를 활용한 고성능 Flow Service"""

    def __init__(self, storage_path: str = ".ai-brain", base_path: str = None, 
                 cache_ttl: float = 3600, 
                 cache_size: int = 1000):
        # base_path가 제공되면 storage_path 대신 사용 (하위 호환성)
        if base_path is not None:
            storage_path = base_path
        
        self.storage_path = Path(storage_path)
        self._ensure_directory()

        # 개선된 캐시 초기화
        self.cache = FlowCache(ttl_seconds=cache_ttl, max_size=cache_size)

        # 파일 감시를 위한 수정 시간 추적
        self._file_watchers: Dict[str, float] = {}
        self._lock = threading.RLock()

        # 성능 메트릭
        self._operation_count = 0
        self._cache_warming_enabled = True

    def _ensure_directory(self):
        """저장 디렉토리 확인 및 생성"""
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _get_file_mtime(self, flow_id: str) -> float:
        """파일 수정 시간 조회"""
        file_path = self.storage_path / f"{flow_id}.json"
        try:
            return file_path.stat().st_mtime
        except FileNotFoundError:
            return 0

    def _check_file_changes(self, flow_id: str) -> bool:
        """파일 변경 감지"""
        current_mtime = self._get_file_mtime(flow_id)

        with self._lock:
            last_mtime = self._file_watchers.get(flow_id, 0)
            if current_mtime > last_mtime:
                self._file_watchers[flow_id] = current_mtime
                self.cache.invalidate(flow_id)
                return True
        return False

    def list_flows(self) -> List[Flow]:
        """모든 Flow 목록 조회 (캐시 활용)"""
        # 특별 키로 전체 목록 캐싱
        cache_key = "__all_flows__"

        # 캐시 확인
        cached_flows = self.cache.get(cache_key)
        if cached_flows is not None:
            return cached_flows

        # 캐시 미스 - 파일에서 로드
        flows = []
        for file_path in self.storage_path.glob("*.json"):
            if file_path.stem != "__all_flows__":  # 특별 키 제외
                try:
                    flow = self.get_flow(file_path.stem)
                    if flow:
                        flows.append(flow)
                except Exception:
                    continue

        # 결과 캐싱 (짧은 TTL)
        self.cache.put(cache_key, flows, time.time())
        return flows

    def get_flow(self, flow_id: str) -> Optional[Flow]:
        """Flow 조회 (캐시 우선)"""
        # 파일 변경 체크
        self._check_file_changes(flow_id)

        # 캐시 조회
        cached_flow = self.cache.get(flow_id)
        if cached_flow is not None:
            return cached_flow

        # 캐시 미스 - 파일에서 로드
        file_path = self.storage_path / f"{flow_id}.json"
        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Flow 객체 재구성
            flow = Flow(
                id=data['id'],
                name=data['name'],
                created_at=data.get('created_at'),
                updated_at=data.get('updated_at'),
                metadata=data.get('metadata', {})
            )

            # Plans 재구성
            for plan_data in data.get('plans', {}).values():
                plan = Plan(
                    id=plan_data['id'],
                    name=plan_data['name'],
                    tasks={},  # 나중에 채워짐
                    completed=plan_data.get('completed', False),
                    created_at=plan_data.get('created_at'),
                    updated_at=plan_data.get('updated_at'),
                    metadata=plan_data.get('metadata', {})
                )

                # Tasks 재구성
                for task_data in plan_data.get('tasks', {}).values():
                    task = Task(
                        id=task_data['id'],
                        name=task_data['name'],
                        status=task_data.get('status', 'todo'),
                        created_at=task_data.get('created_at'),
                        updated_at=task_data.get('updated_at'),
                        started_at=task_data.get('started_at'),
                        completed_at=task_data.get('completed_at'),
                        context=task_data.get('context', {})
                    )
                    plan.tasks[task.id] = task

                flow.plans[plan.id] = plan

            # 캐시에 저장
            mtime = self._get_file_mtime(flow_id)
            self.cache.put(flow_id, flow, mtime)

            return flow

        except Exception as e:
            raise StorageError(f"Failed to load flow {flow_id}: {str(e)}")

    def save_flow(self, flow: Flow) -> None:
        """Flow 저장 (원자적 쓰기)"""
        if not flow or not flow.id:
            raise ValidationError("Invalid flow object")

        # 데이터 직렬화
        data = {
            'id': flow.id,
            'name': flow.name,
            'created_at': flow.created_at or datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'metadata': flow.metadata,
            'plans': {}
        }

        # Plans 직렬화
        for plan_id, plan in flow.plans.items():
            plan_data = {
                'id': plan.id,
                'name': plan.name,
                'flow_id': plan.flow_id,
                'created_at': plan.created_at or datetime.now().isoformat(),
                'completed': plan.completed,
                'tasks': {}
            }

            # Tasks 직렬화
            for task_id, task in plan.tasks.items():
                task_data = {
                    'id': task.id,
                    'name': task.name,
                    'plan_id': task.plan_id,
                    'status': task.status,
                    'created_at': task.created_at or datetime.now().isoformat(),
                    'updated_at': task.updated_at or datetime.now().isoformat(),
                    'context': task.context
                }
                plan_data['tasks'][task_id] = task_data

            data['plans'][plan_id] = plan_data

        # 원자적 저장
        file_path = self.storage_path / f"{flow.id}.json"
        self._save_atomic(file_path, data)

        # 캐시 업데이트
        mtime = self._get_file_mtime(flow.id)
        self.cache.put(flow.id, flow, mtime)

        # 전체 목록 캐시 무효화
        self.cache.invalidate("__all_flows__")

    def _save_atomic(self, file_path: Path, data: dict) -> None:
        """원자적 파일 저장"""
        # 임시 파일에 먼저 저장
        with tempfile.NamedTemporaryFile(
            mode='w',
            dir=self.storage_path,
            delete=False,
            suffix='.tmp',
            encoding='utf-8'
        ) as tmp_file:
            json.dump(data, tmp_file, indent=2, ensure_ascii=False)
            tmp_path = Path(tmp_file.name)

        # 원자적 교체 (Windows 호환)
        try:
            if file_path.exists():
                file_path.unlink()
            tmp_path.rename(file_path)
        except Exception as e:
            tmp_path.unlink()  # 임시 파일 정리
            raise StorageError(f"Failed to save file atomically: {str(e)}")

    def update_task_status(self, flow_id: str, task_id: str, status: str) -> bool:
        """Task 상태 업데이트 (최적화)"""
        flow = self.get_flow(flow_id)
        if not flow:
            return False

        # Task 찾기 및 업데이트
        for plan in flow.plans.values():
            if task_id in plan.tasks:
                plan.tasks[task_id].status = status
                plan.tasks[task_id].updated_at = datetime.now().isoformat()

                # Flow 저장
                self.save_flow(flow)
                return True

        return False

    def get_cache_statistics(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        stats = self.cache.get_statistics()
        stats['operation_count'] = self._operation_count
        return stats

    def warm_cache(self) -> None:
        """캐시 워밍업"""
        if not self._cache_warming_enabled:
            return

        # 모든 Flow를 미리 로드
        for file_path in self.storage_path.glob("*.json"):
            if file_path.stem != "__all_flows__":
                try:
                    self.get_flow(file_path.stem)
                except Exception:
                    continue
if __name__ == '__main__':
    # 캐시가 적용된 서비스 생성
    service = CachedFlowService()

    # Flow 조회 (첫 번째는 파일에서, 두 번째부터는 캐시에서)
    flow = service.get_flow('flow_20250722_231255_29220a')
    flow2 = service.get_flow('flow_20250722_231255_29220a')  # 캐시 히트!

    # Task 상태 업데이트 (해당 Flow만 캐시 무효화)
    service.update_task_status(
        'flow_20250722_231255_29220a',
        'plan_20250722_233222_51e098',
        'task_20250722_233222_abc123',
        'completed'
    )