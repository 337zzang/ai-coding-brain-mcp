"""
Task 비즈니스 로직 서비스
"""
from typing import Dict, List, Optional
from datetime import datetime
import uuid

from ..domain.models import Task, TaskStatus
from .plan_service import PlanService


class TaskService:
    """Task 관련 비즈니스 로직"""

    def __init__(self, plan_service: PlanService):
        self.plan_service = plan_service

    def create_task(self, flow_id: str, plan_id: str, name: str) -> Optional[Task]:
        """새 Task 생성"""
        plan = self.plan_service.get_plan(flow_id, plan_id)
        if not plan:
            return None

        task_id = f"task_{int(datetime.now().timestamp() * 1e7)}_{uuid.uuid4().hex[:6]}"
        task = Task(
            id=task_id,
            name=name,
            context={
                'plan': '',
                'actions': [],
                'results': {},
                'files': {'created': [], 'modified': [], 'analyzed': []},
                'errors': [],
                'notes': []
            }
        )

        # Plan에 추가
        plan.tasks[task_id] = task
        self.plan_service.update_plan(flow_id, plan)

        return task

    def get_task(self, flow_id: str, plan_id: str, task_id: str) -> Optional[Task]:
        """특정 Task 조회"""
        plan = self.plan_service.get_plan(flow_id, plan_id)
        if plan:
            return plan.tasks.get(task_id)
        return None

    def update_task_status(self, flow_id: str, plan_id: str, task_id: str, 
                          new_status: TaskStatus) -> bool:
        """Task 상태 업데이트"""
        plan = self.plan_service.get_plan(flow_id, plan_id)
        if not plan or task_id not in plan.tasks:
            return False

        task = plan.tasks[task_id]
        old_status = task.status

        # 상태 전환 검증
        if not self._is_valid_transition(old_status, new_status):
            return False

        # 상태 업데이트
        task.status = new_status
        task.updated_at = datetime.now()

        # 상태별 추가 처리
        if new_status in [TaskStatus.PLANNING, TaskStatus.IN_PROGRESS]:
            if not task.started_at:
                task.started_at = datetime.now()
        elif new_status in [TaskStatus.COMPLETED, TaskStatus.SKIP]:
            task.completed_at = datetime.now()

        # Plan 업데이트
        self.plan_service.update_plan(flow_id, plan)

        # Plan 자동 완료 체크
        if new_status in [TaskStatus.COMPLETED, TaskStatus.REVIEWING, TaskStatus.SKIP]:
            self.plan_service.check_auto_complete(flow_id, plan_id)

        return True

    def update_task_context(self, flow_id: str, plan_id: str, task_id: str,
                           context_updates: Dict) -> bool:
        """Task 컨텍스트 업데이트"""
        task = self.get_task(flow_id, plan_id, task_id)
        if not task:
            return False

        # 컨텍스트 병합
        for key, value in context_updates.items():
            if key in ['actions', 'errors', 'notes'] and isinstance(value, list):
                # 리스트는 추가
                task.context.setdefault(key, []).extend(value)
            elif key == 'files' and isinstance(value, dict):
                # 파일 정보는 병합
                files = task.context.setdefault('files', {})
                for fkey, fvalue in value.items():
                    if isinstance(fvalue, list):
                        files.setdefault(fkey, []).extend(fvalue)
            else:
                # 나머지는 덮어쓰기
                task.context[key] = value

        task.updated_at = datetime.now()

        # Plan 업데이트
        plan = self.plan_service.get_plan(flow_id, plan_id)
        self.plan_service.update_plan(flow_id, plan)

        return True

    def add_task_action(self, flow_id: str, plan_id: str, task_id: str,
                       action: str) -> bool:
        """Task에 액션 추가"""
        return self.update_task_context(flow_id, plan_id, task_id, {
            'actions': [f"[{datetime.now().strftime('%H:%M:%S')}] {action}"]
        })

    def _is_valid_transition(self, from_status: TaskStatus, to_status: TaskStatus) -> bool:
        """상태 전환 유효성 검증"""
        # 동일 상태로의 전환은 항상 허용
        if from_status == to_status:
            return True

        # 유효한 전환 정의
        valid_transitions = {
            TaskStatus.TODO: [TaskStatus.PLANNING, TaskStatus.IN_PROGRESS, TaskStatus.SKIP, TaskStatus.COMPLETED],
            TaskStatus.PLANNING: [TaskStatus.IN_PROGRESS, TaskStatus.TODO, TaskStatus.SKIP],
            TaskStatus.IN_PROGRESS: [TaskStatus.REVIEWING, TaskStatus.COMPLETED, TaskStatus.ERROR, TaskStatus.TODO],
            TaskStatus.REVIEWING: [TaskStatus.COMPLETED, TaskStatus.IN_PROGRESS],
            TaskStatus.COMPLETED: [TaskStatus.IN_PROGRESS],  # 재작업 허용
            TaskStatus.SKIP: [TaskStatus.TODO],  # 스킵 취소 허용
            TaskStatus.ERROR: [TaskStatus.TODO, TaskStatus.IN_PROGRESS]
        }

        return to_status in valid_transitions.get(from_status, [])
