"""
극단적으로 단순화된 Flow Manager
- Flow 개념 자체가 없음
- 프로젝트 = Plan들의 컬렉션
"""
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from .repository import UltraSimpleRepository, EnhancedUltraSimpleRepository
from .domain.models import Plan, Task, TaskStatus
from .decorators import auto_record
from .service.lru_cache import LRUCache
from .task_logger import EnhancedTaskLogger


class UltraSimpleFlowManager:
    """극단적으로 단순한 Flow 관리자"""

    def __init__(self, project_path: Optional[str] = None, use_enhanced: bool = True):
        """
        Args:
            project_path: 프로젝트 경로 (None이면 현재 디렉토리)
            use_enhanced: 폴더 기반 저장소 사용 여부 (기본값: True)
        """
        self.project_path = Path(project_path or os.getcwd())
        self.project_name = self.project_path.name

        # Repository 초기화
        base_path = self.project_path / '.ai-brain' / 'flow'
        # Repository 초기화 (폴더 기반 or 단일 파일)
        if use_enhanced:
            # 상대경로로 전달 (Repository에서 resolve 처리)
            self._repo = EnhancedUltraSimpleRepository('.ai-brain/flow')
        else:
            self._repo = UltraSimpleRepository(str(base_path))

        # 캐시
        self._plan_cache = LRUCache(max_size=50, ttl=60)

    # --- Plan 관리 (핵심 API) ---

    @auto_record()
    def create_plan(self, name: str, description: str = "") -> Plan:
        """Plan 생성"""
        plan_id = self._generate_plan_id(name)

        plan = Plan(
            id=plan_id,
            name=name,
            tasks={},
            metadata={'description': description}
        )

        self._repo.save_plan(plan)
        return plan

    def get_plan(self, plan_id: str) -> Optional[Plan]:
        """Plan 조회"""
        # 캐시 확인 (dict와 LRUCache 모두 호환)
        if hasattr(self._plan_cache, 'get'):
            cached = self._plan_cache.get(plan_id)
        else:
            cached = self._plan_cache.get(plan_id) if isinstance(self._plan_cache, dict) else None

        if cached:
            return cached

        # Repository에서 로드
        plan = self._repo.load_plan(plan_id)
        if plan:
            # 캐시에 저장 (dict와 LRUCache 모두 호환)
            if hasattr(self._plan_cache, 'set'):
                self._plan_cache.set(plan_id, plan)
            elif isinstance(self._plan_cache, dict):
                self._plan_cache[plan_id] = plan

        return plan

    def list_plans(self) -> List[Plan]:
        """모든 Plan 목록"""
        plan_ids = self._repo.list_plan_ids()
        plans = []
        for pid in plan_ids:
            plan = self.get_plan(pid)
            if plan is not None:  # None 체크를 명시적으로
                plans.append(plan)
        return plans

    @auto_record()
    def update_plan(self, plan_id: str, **updates) -> bool:
        """Plan 업데이트"""
        plan = self.get_plan(plan_id)
        if plan is None:
            return False

        for key, value in updates.items():
            if hasattr(plan, key):
                setattr(plan, key, value)

        plan.updated_at = datetime.now().isoformat()

        self._repo.save_plan(plan)
        self._plan_cache.invalidate(plan_id)

        return True

    @auto_record()
    def delete_plan(self, plan_id: str) -> bool:
        """Plan 삭제"""
        self._repo.delete_plan(plan_id)
        self._plan_cache.invalidate(plan_id)
        return True

    # --- Task 관리 ---

    @auto_record()
    def create_task(self, plan_id: str, name: str) -> Optional[Task]:
        """Task 생성"""
        plan = self.get_plan(plan_id)
        if plan is None:
            return None

        task_id = self._generate_task_id()
        task = Task(
            id=task_id,
            title=name,
            status=TaskStatus.TODO
        )

        plan.tasks[task_id] = task
        plan.updated_at = datetime.now().isoformat()

        self._repo.save_plan(plan)
        self._plan_cache.invalidate(plan_id)


        # TaskLogger 자동 생성
        try:
            task_number = len(plan.tasks)
            logger = EnhancedTaskLogger(plan_id, task_number, name)
            logger.task_info(title=name)
            logger.design("Task가 생성되었습니다.")
            print(f"[OK] TaskLogger 자동 생성: {task_number}.{name}")
        except Exception as e:
            print(f"[WARNING] TaskLogger 자동 생성 실패: {e}")

        return task

    @auto_record()
    def update_task_status(self, plan_id: str, task_id: str, status: str) -> bool:
        """Task 상태 업데이트"""
        plan = self.get_plan(plan_id)
        if not plan or task_id not in plan.tasks:
            return False

        task = plan.tasks[task_id]
        # status가 문자열인 경우 enum으로 변환
        if isinstance(status, str):
            task.status = TaskStatus(status)
        else:
            task.status = status
        task.updated_at = datetime.now().isoformat()

        if task.status == TaskStatus.IN_PROGRESS:
            task.started_at = datetime.now().isoformat()
        elif task.status == TaskStatus.DONE:
            task.completed_at = datetime.now().isoformat()

        plan.updated_at = datetime.now().isoformat()
        self._repo.save_plan(plan)
        self._plan_cache.invalidate(plan_id)


        # TaskLogger에 상태 변경 기록
        try:
            task_num = list(plan.tasks.keys()).index(task_id) + 1
            task_logger = EnhancedTaskLogger(plan_id, task_num, task.title)
            
            if task.status == TaskStatus.IN_PROGRESS:
                task_logger.note(f"Task 시작: {task.title}")
            elif task.status == TaskStatus.DONE:
                task_logger.complete(f"Task 완료: {task.title}")
            else:
                task_logger.note(f"상태 변경: → {status}")
                
            print(f"[OK] 상태 변경 기록: Task {task_num} → {task.status.value}")
        except Exception as e:
            print(f"[WARNING] 상태 변경 로깅 실패: {e}")

        return True

    # --- 통계 ---


    def get_task_by_number(self, plan_id: str, task_number: int) -> Optional[Task]:
        """Task를 번호로 조회 (1부터 시작)

        Args:
            plan_id: Plan ID
            task_number: Task 번호 (1-indexed)

        Returns:
            Task 객체 또는 None
        """
        plan = self.get_plan(plan_id)
        if not plan or not plan.tasks:
            return None

        # 생성 시간 순으로 정렬
        sorted_tasks = sorted(
            plan.tasks.values(), 
            key=lambda t: t.created_at
        )

        # 번호는 1부터 시작
        if 1 <= task_number <= len(sorted_tasks):
            return sorted_tasks[task_number - 1]

        return None

    def get_stats(self) -> Dict[str, Any]:
        """프로젝트 통계"""
        repo_stats = self._repo.get_stats()

        return {
            'project': self.project_name,
            'project_path': str(self.project_path),
            **repo_stats,
            'cache_size': self._plan_cache.size()
        }

    # --- 유틸리티 ---

    def _generate_plan_id(self, name: str = "") -> str:
        """Plan ID 생성 (이름 포함)"""
        import re
        timestamp = datetime.now().strftime("%Y%m%d")
        existing = self._repo.list_plan_ids()

        # 오늘 날짜의 plan들에서 순번 추출 (정규식 사용)
        pattern = f"^plan_{timestamp}_(\d{{3}})(_|$)"
        seq_numbers = []
        for plan_id in existing:
            match = re.match(pattern, plan_id)
            if match:
                seq_numbers.append(int(match.group(1)))

        seq = max(seq_numbers) + 1 if seq_numbers else 1

        # Plan 이름을 안전한 문자열로 변환
        safe_name = name.strip()[:30]  # 최대 30자
        safe_name = re.sub(r'[^a-zA-Z0-9가-힣_-]', '_', safe_name)
        safe_name = re.sub(r'_+', '_', safe_name)  # 연속된 _를 하나로
        safe_name = safe_name.strip('_')  # 앞뒤 _ 제거

        if safe_name:
            return f"plan_{timestamp}_{seq:03d}_{safe_name}"
        else:
            return f"plan_{timestamp}_{seq:03d}"
    def _generate_task_id(self) -> str:
        """Task ID 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique = str(uuid.uuid4())[:6]
        return f"task_{timestamp}_{unique}"
