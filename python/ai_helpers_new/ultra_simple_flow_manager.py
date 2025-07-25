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

from .repository.ultra_simple_repository import UltraSimpleRepository
from .domain.models import Plan, Task, TaskStatus
from .decorators import auto_record
from .service.lru_cache import LRUCache


class UltraSimpleFlowManager:
    """극단적으로 단순한 Flow 관리자"""

    def __init__(self, project_path: Optional[str] = None):
        """
        Args:
            project_path: 프로젝트 경로 (None이면 현재 디렉토리)
        """
        self.project_path = Path(project_path or os.getcwd())
        self.project_name = self.project_path.name

        # Repository 초기화
        base_path = self.project_path / '.ai-brain' / 'flow'
        self._repo = UltraSimpleRepository(str(base_path))

        # 캐시
        self._plan_cache = LRUCache(max_size=50, ttl=60)

    # --- Plan 관리 (핵심 API) ---

    @auto_record()
    def create_plan(self, name: str, description: str = "") -> Plan:
        """Plan 생성"""
        plan_id = self._generate_plan_id()

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
        # 캐시 확인
        cached = self._plan_cache.get(plan_id)
        if cached:
            return cached

        # Repository에서 로드
        plan = self._repo.load_plan(plan_id)
        if plan:
            self._plan_cache.set(plan_id, plan)

        return plan

    def list_plans(self) -> List[Plan]:
        """모든 Plan 목록"""
        plan_ids = self._repo.list_plan_ids()
        return [self.get_plan(pid) for pid in plan_ids if self.get_plan(pid)]

    @auto_record()
    def update_plan(self, plan_id: str, **updates) -> bool:
        """Plan 업데이트"""
        plan = self.get_plan(plan_id)
        if not plan:
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
        if not plan:
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

        if status == TaskStatus.IN_PROGRESS.value:
            task.started_at = datetime.now().isoformat()
        elif status == TaskStatus.DONE.value:
            task.completed_at = datetime.now().isoformat()

        plan.updated_at = datetime.now().isoformat()
        self._repo.save_plan(plan)
        self._plan_cache.invalidate(plan_id)

        return True

    # --- 통계 ---

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

    def _generate_plan_id(self) -> str:
        """Plan ID 생성"""
        timestamp = datetime.now().strftime("%Y%m%d")
        existing = self._repo.list_plan_ids()
        today_plans = [p for p in existing if p.startswith(f"plan_{timestamp}_")]
        seq = len(today_plans) + 1
        return f"plan_{timestamp}_{seq:03d}"

    def _generate_task_id(self) -> str:
        """Task ID 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique = str(uuid.uuid4())[:6]
        return f"task_{timestamp}_{unique}"
