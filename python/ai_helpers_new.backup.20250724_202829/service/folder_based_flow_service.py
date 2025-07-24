"""
폴더 기반 Flow Service with 캐싱
- LRU 캐시를 사용한 성능 최적화
- Flow와 Plan을 별도로 캐싱
"""
from typing import Optional, List, Dict, Any
import os
from pathlib import Path

from .lru_cache import LRUCache
from ..repository.folder_based_repository import (
    FileFlowRepository, 
    FilePlanRepository,
    FlowRepository,
    PlanRepository
)
from ..domain.models import Flow, Plan, Task


class FolderBasedFlowService:
    """폴더 기반 Flow 서비스 (캐싱 포함)"""

    def __init__(self, base_path: str = None):
        """
        Args:
            base_path: 기본 경로 (None이면 현재 프로젝트의 .ai-brain/flow)
        """
        if base_path is None:
            # 현재 프로젝트 기준
            base_path = os.path.join(os.getcwd(), '.ai-brain', 'flow')

        self.base_path = Path(base_path)

        # Repository 초기화
        self._flow_repo: FlowRepository = FileFlowRepository(str(self.base_path))
        self._plan_repo: PlanRepository = FilePlanRepository(str(self.base_path))

        # 캐시 초기화
        self._flow_cache = LRUCache(max_size=64, ttl=30)  # Flow는 적게, 자주 변경
        self._plan_cache = LRUCache(max_size=256, ttl=60)  # Plan은 많이, 덜 변경

        # 통계
        self._stats = {
            'flow_hits': 0,
            'flow_misses': 0,
            'plan_hits': 0,
            'plan_misses': 0
        }

    # --- Flow 관련 메서드 ---

    def create_flow(self, name: str, project: Optional[str] = None) -> Flow:
        """새 Flow 생성"""
        flow_id = self._generate_flow_id(name)

        # 기본 구조로 Flow 생성
        flow = Flow(
            id=flow_id,
            name=name,
            plans={},  # 빈 딕셔너리로 시작
            project=project
        )

        # Repository에 저장
        self._flow_repo.save_flow(flow)

        # 캐시에 추가
        self._flow_cache.set(flow_id, flow)

        return flow

    def load_flow(self, flow_id: str) -> Optional[Flow]:
        """Flow 로드 (캐시 우선)"""
        # 캐시 확인
        cached = self._flow_cache.get(flow_id)
        if cached:
            self._stats['flow_hits'] += 1
            return cached

        # Repository에서 로드
        self._stats['flow_misses'] += 1
        flow = self._flow_repo.load_flow(flow_id)

        if flow:
            # plan_ids가 있으면 처리
            if hasattr(flow, 'plan_ids') and not hasattr(flow, '_plan_ids'):
                flow._plan_ids = getattr(flow, 'plan_ids', [])

            # 캐시에 저장
            self._flow_cache.set(flow_id, flow)

        return flow

    def save_flow(self, flow: Flow) -> None:
        """Flow 저장"""
        self._flow_repo.save_flow(flow)
        self._flow_cache.invalidate(flow.id)

    def list_flows(self, project: Optional[str] = None) -> List[Flow]:
        """Flow 목록"""
        return self._flow_repo.list_flows(project)

    def delete_flow(self, flow_id: str) -> None:
        """Flow 삭제"""
        self._flow_repo.delete_flow(flow_id)
        self._flow_cache.invalidate(flow_id)
        # 관련 Plan 캐시도 정리
        self._plan_cache.invalidate_pattern(f"{flow_id}:")

    # --- Plan 관련 메서드 ---

    def create_plan(self, flow_id: str, plan_id: str, plan: Plan) -> None:
        """Plan 생성 및 저장"""
        # flow_id 설정
        if not hasattr(plan, 'flow_id'):
            plan.flow_id = flow_id

        # Repository에 저장
        self._plan_repo.save_plan(plan)

        # 캐시 무효화
        cache_key = f"{flow_id}:{plan_id}"
        self._plan_cache.set(cache_key, plan)

        # Flow 캐시도 무효화 (plan_ids 변경)
        self._flow_cache.invalidate(flow_id)

    def load_plan(self, flow_id: str, plan_id: str) -> Optional[Plan]:
        """Plan 로드 (캐시 우선)"""
        cache_key = f"{flow_id}:{plan_id}"

        # 캐시 확인
        cached = self._plan_cache.get(cache_key)
        if cached:
            self._stats['plan_hits'] += 1
            return cached

        # Repository에서 로드
        self._stats['plan_misses'] += 1
        plan = self._plan_repo.load_plan(flow_id, plan_id)

        if plan:
            # 캐시에 저장
            self._plan_cache.set(cache_key, plan)

        return plan

    def save_plan(self, plan: Plan) -> None:
        """Plan 저장"""
        if not hasattr(plan, 'flow_id'):
            raise ValueError("Plan must have flow_id")

        self._plan_repo.save_plan(plan)

        # 캐시 무효화
        cache_key = f"{plan.flow_id}:{plan.id}"
        self._plan_cache.invalidate(cache_key)

    def list_plan_ids(self, flow_id: str) -> List[str]:
        """Flow의 Plan ID 목록"""
        return self._plan_repo.list_plans(flow_id)

    def delete_plan(self, flow_id: str, plan_id: str) -> None:
        """Plan 삭제"""
        self._plan_repo.delete_plan(flow_id, plan_id)

        # 캐시 무효화
        cache_key = f"{flow_id}:{plan_id}"
        self._plan_cache.invalidate(cache_key)
        self._flow_cache.invalidate(flow_id)

    # --- 유틸리티 메서드 ---

    def _generate_flow_id(self, name: str) -> str:
        """Flow ID 생성"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
        return f"flow_{safe_name}_{timestamp}"

    def get_stats(self) -> Dict[str, Any]:
        """서비스 통계"""
        return {
            'cache_stats': self._stats,
            'flow_cache': self._flow_cache.stats(),
            'plan_cache': self._plan_cache.stats()
        }

    def clear_cache(self) -> None:
        """전체 캐시 클리어"""
        self._flow_cache.invalidate()
        self._plan_cache.invalidate()
