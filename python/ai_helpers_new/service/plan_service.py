"""
Plan 비즈니스 로직 서비스
"""
from typing import Dict, List, Optional
from datetime import datetime
import uuid

from ..domain.models import Flow, Plan, Task, TaskStatus
from .flow_service import FlowService


class PlanService:
    """Plan 관련 비즈니스 로직"""

    def __init__(self, flow_service: FlowService):
        self.flow_service = flow_service

    def create_plan(self, flow_id: str, name: str) -> Optional[Plan]:
        """새 Plan 생성"""
        flow = self.flow_service.get_flow(flow_id)
        if not flow:
            return None

        plan_id = f"plan_{int(datetime.now().timestamp() * 1e7)}_{uuid.uuid4().hex[:6]}"
        plan = Plan(id=plan_id, name=name)

        # Flow에 추가
        self.flow_service.add_plan_to_flow(flow_id, plan)

        return plan

    def get_plan(self, flow_id: str, plan_id: str) -> Optional[Plan]:
        """특정 Plan 조회"""
        flow = self.flow_service.get_flow(flow_id)
        if flow:
            return flow.plans.get(plan_id)
        return None

    def update_plan(self, flow_id: str, plan: Plan) -> bool:
        """Plan 업데이트"""
        flow = self.flow_service.get_flow(flow_id)
        if flow and plan.id in flow.plans:
            flow.plans[plan.id] = plan
            self.flow_service.update_flow(flow)
            return True
        return False

    def delete_plan(self, flow_id: str, plan_id: str) -> bool:
        """Plan 삭제"""
        return self.flow_service.remove_plan_from_flow(flow_id, plan_id)

    def complete_plan(self, flow_id: str, plan_id: str) -> bool:
        """Plan 완료 처리"""
        plan = self.get_plan(flow_id, plan_id)
        if plan:
            plan.completed = True
            plan.completed_at = datetime.now()

            # 모든 미완료 Task도 완료 처리
            for task in plan.tasks.values():
                if task.status not in [TaskStatus.COMPLETED, TaskStatus.SKIP]:
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.now()

            return self.update_plan(flow_id, plan)
        return False

    def reopen_plan(self, flow_id: str, plan_id: str) -> bool:
        """Plan 재오픈"""
        plan = self.get_plan(flow_id, plan_id)
        if plan:
            plan.completed = False
            plan.completed_at = None
            return self.update_plan(flow_id, plan)
        return False

    def check_auto_complete(self, flow_id: str, plan_id: str) -> bool:
        """모든 Task가 완료되면 Plan 자동 완료"""
        plan = self.get_plan(flow_id, plan_id)
        if not plan or plan.completed:
            return False

        # 모든 Task가 완료/리뷰중/스킵 상태인지 확인
        all_done = all(
            task.status in [TaskStatus.COMPLETED, TaskStatus.REVIEWING, TaskStatus.SKIP]
            for task in plan.tasks.values()
        )

        if all_done and plan.tasks:  # Task가 하나라도 있고 모두 완료
            plan.completed = True
            plan.completed_at = datetime.now()
            self.update_plan(flow_id, plan)
            return True

        return False
