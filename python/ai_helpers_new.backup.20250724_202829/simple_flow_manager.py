"""
단순화된 Flow Manager
- Flow ID 없음
- 프로젝트당 하나의 Flow
- 더 직관적인 API
"""
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from .repository.simplified_repository import (
    SimplifiedFlowRepository,
    SimplifiedPlanRepository
)
from .domain.models import Plan, Task, TaskStatus
from .decorators import auto_record
from .service.lru_cache import LRUCache


class SimpleFlowManager:
    """단순화된 Flow 관리자"""

    def __init__(self, project_path: Optional[str] = None):
        """
        Args:
            project_path: 프로젝트 경로 (None이면 현재 디렉토리)
        """
        # 프로젝트 설정
        self.project_path = Path(project_path or os.getcwd())
        self.project_name = self.project_path.name

        # Repository 초기화
        base_path = self.project_path / '.ai-brain' / 'flow'
        self._flow_repo = SimplifiedFlowRepository(str(base_path))
        self._plan_repo = SimplifiedPlanRepository(str(base_path))

        # 캐시 초기화
        self._plan_cache = LRUCache(max_size=50, ttl=60)

        # Flow 초기화
        self._initialize_flow()

    def _initialize_flow(self):
        """Flow 초기화 (자동 생성)"""
        if not self._flow_repo.exists():
            self._flow_repo.create_default_flow(self.project_name)

    # --- Flow 정보 (읽기 전용) ---

    @property
    def flow(self) -> Dict[str, Any]:
        """현재 Flow 정보"""
        return self._flow_repo.load_flow()

    @property
    def project(self) -> str:
        """프로젝트 이름"""
        return self.project_name

    def get_stats(self) -> Dict[str, Any]:
        """통계 정보"""
        flow_data = self.flow
        plan_count = self._plan_repo.get_plan_count()

        return {
            'project': self.project_name,
            'project_path': str(self.project_path),
            'created_at': flow_data.get('created_at'),
            'updated_at': flow_data.get('updated_at'),
            'plan_count': plan_count,
            'cache_size': self._plan_cache.size()
        }

    # --- Plan 관리 (핵심 API) ---

    @auto_record
    def create_plan(self, name: str, description: str = "") -> Plan:
        """Plan 생성"""
        # Plan ID 생성
        plan_id = self._generate_plan_id()

        # Plan 객체 생성
        plan = Plan(
            id=plan_id,
            name=name,
            tasks={},
            metadata={'description': description}
        )

        # 저장
        self._plan_repo.save_plan(plan)

        # Flow 업데이트
        self._update_flow_timestamp()

        return plan

    def get_plan(self, plan_id: str) -> Optional[Plan]:
        """Plan 조회 (캐시 사용)"""
        # 캐시 확인
        cached = self._plan_cache.get(plan_id)
        if cached:
            return cached

        # Repository에서 로드
        plan = self._plan_repo.load_plan(plan_id)
        if plan:
            self._plan_cache.set(plan_id, plan)

        return plan

    def list_plans(self) -> List[Plan]:
        """모든 Plan 목록"""
        plan_ids = self._plan_repo.list_plan_ids()
        plans = []

        for plan_id in plan_ids:
            plan = self.get_plan(plan_id)
            if plan:
                plans.append(plan)

        return plans

    @auto_record
    def update_plan(self, plan_id: str, **updates) -> bool:
        """Plan 업데이트"""
        plan = self.get_plan(plan_id)
        if not plan:
            return False

        # 업데이트 적용
        for key, value in updates.items():
            if hasattr(plan, key):
                setattr(plan, key, value)

        plan.updated_at = datetime.now().isoformat()

        # 저장
        self._plan_repo.save_plan(plan)
        self._plan_cache.invalidate(plan_id)
        self._update_flow_timestamp()

        return True

    @auto_record
    def delete_plan(self, plan_id: str) -> bool:
        """Plan 삭제"""
        self._plan_repo.delete_plan(plan_id)
        self._plan_cache.invalidate(plan_id)
        self._update_flow_timestamp()
        return True

    # --- Task 관리 ---

    @auto_record
    def create_task(self, plan_id: str, name: str) -> Optional[Task]:
        """Task 생성"""
        plan = self.get_plan(plan_id)
        if not plan:
            return None

        # Task 생성
        task_id = self._generate_task_id()
        task = Task(
            id=task_id,
            name=name,
            status=TaskStatus.TODO.value
        )

        # Plan에 추가
        plan.tasks[task_id] = task
        plan.updated_at = datetime.now().isoformat()

        # 저장
        self._plan_repo.save_plan(plan)
        self._plan_cache.invalidate(plan_id)

        return task

    @auto_record
    def update_task_status(self, plan_id: str, task_id: str, status: str) -> bool:
        """Task 상태 업데이트"""
        plan = self.get_plan(plan_id)
        if not plan or task_id not in plan.tasks:
            return False

        task = plan.tasks[task_id]
        task.status = status
        task.updated_at = datetime.now().isoformat()

        # 상태별 시간 기록
        if status == TaskStatus.IN_PROGRESS.value:
            task.started_at = datetime.now().isoformat()
        elif status == TaskStatus.DONE.value:
            task.completed_at = datetime.now().isoformat()

        # 저장
        plan.updated_at = datetime.now().isoformat()
        self._plan_repo.save_plan(plan)
        self._plan_cache.invalidate(plan_id)

        return True

    @auto_record
    def delete_task(self, plan_id: str, task_id: str) -> bool:
        """Task 삭제"""
        plan = self.get_plan(plan_id)
        if not plan or task_id not in plan.tasks:
            return False

        del plan.tasks[task_id]
        plan.updated_at = datetime.now().isoformat()

        # 저장
        self._plan_repo.save_plan(plan)
        self._plan_cache.invalidate(plan_id)

        return True

    # --- 유틸리티 ---

    def _update_flow_timestamp(self):
        """Flow 타임스탬프 업데이트"""
        flow_data = self._flow_repo.load_flow()
        if flow_data:
            flow_data['updated_at'] = datetime.now().isoformat()
            flow_data['plan_count'] = self._plan_repo.get_plan_count()
            self._flow_repo.save_flow(flow_data)

    def _generate_plan_id(self) -> str:
        """Plan ID 생성"""
        timestamp = datetime.now().strftime("%Y%m%d")
        existing = self._plan_repo.list_plan_ids()
        today_plans = [p for p in existing if p.startswith(f"plan_{timestamp}_")]
        seq = len(today_plans) + 1
        return f"plan_{timestamp}_{seq:03d}"

    def _generate_task_id(self) -> str:
        """Task ID 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique = str(uuid.uuid4())[:6]
        return f"task_{timestamp}_{unique}"

    def clear_cache(self):
        """캐시 클리어"""
        self._plan_cache.invalidate()


# 편의 함수 - 전역 접근
_manager_instance = None

def get_flow_manager(project_path: Optional[str] = None) -> SimpleFlowManager:
    """Flow Manager 인스턴스 가져오기"""
    global _manager_instance

    current_path = project_path or os.getcwd()

    # 같은 프로젝트면 기존 인스턴스 반환
    if _manager_instance and str(_manager_instance.project_path) == str(current_path):
        return _manager_instance

    # 새 인스턴스 생성
    _manager_instance = SimpleFlowManager(current_path)
    return _manager_instance
