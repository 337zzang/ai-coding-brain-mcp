"""
Plan 관련 명령어 구현
"""
from typing import Dict, Any, List

from .command_interface import Command
from ..service.flow_service import FlowService
from ..service.plan_service import PlanService


class AddPlanCommand(Command):
    """Plan 추가 명령어"""

    def __init__(self, flow_service: FlowService, plan_service: PlanService):
        self.flow_service = flow_service
        self.plan_service = plan_service

    @property
    def name(self) -> str:
        return "add"

    def execute(self, args: str) -> Dict[str, Any]:
        if not args:
            return {'ok': False, 'error': 'Plan 이름을 입력하세요'}

        current_flow = self.flow_service.get_current_flow()
        if not current_flow:
            return {'ok': False, 'error': '현재 활성화된 Flow가 없습니다'}

        plan_name = args.strip()
        plan = self.plan_service.create_plan(current_flow.id, plan_name)

        if plan:
            return {
                'ok': True,
                'data': f"✅ Plan '{plan.name}' 추가됨\nID: {plan.id}"
            }
        else:
            return {'ok': False, 'error': 'Plan 추가 실패'}

    def get_help(self) -> str:
        return "Plan 추가: /plan add <이름>"


class ListPlansCommand(Command):
    """Plan 목록 명령어"""

    def __init__(self, flow_service: FlowService):
        self.flow_service = flow_service

    @property
    def name(self) -> str:
        return "list"

    @property
    def aliases(self) -> List[str]:
        return ["ls"]

    def execute(self, args: str) -> Dict[str, Any]:
        current_flow = self.flow_service.get_current_flow()
        if not current_flow:
            return {'ok': False, 'error': '현재 활성화된 Flow가 없습니다'}

        if not current_flow.plans:
            return {'ok': True, 'data': "생성된 Plan이 없습니다"}

        result = f"📋 Plans in '{current_flow.name}':\n"
        result += "-" * 50 + "\n"

        for i, (plan_id, plan) in enumerate(current_flow.plans.items(), 1):
            status_icon = "✅" if plan.completed else "⏳"
            tasks_count = len(plan.tasks)
            completed_tasks = sum(1 for t in plan.tasks.values() 
                                 if t.status.value in ['completed', 'reviewing'])

            result += f"\n{i}. {status_icon} {plan.name}\n"
            result += f"   ID: {plan_id}\n"
            result += f"   Tasks: {completed_tasks}/{tasks_count} 완료"

            if tasks_count > 0:
                progress = int(completed_tasks / tasks_count * 100)
                result += f" ({progress}%)"

            result += "\n"

        return {'ok': True, 'data': result.strip()}

    def get_help(self) -> str:
        return "Plan 목록: /plan list"


class CompletePlanCommand(Command):
    """Plan 완료 명령어"""

    def __init__(self, flow_service: FlowService, plan_service: PlanService):
        self.flow_service = flow_service
        self.plan_service = plan_service

    @property
    def name(self) -> str:
        return "complete"

    def execute(self, args: str) -> Dict[str, Any]:
        if not args:
            return {'ok': False, 'error': 'Plan ID를 입력하세요'}

        current_flow = self.flow_service.get_current_flow()
        if not current_flow:
            return {'ok': False, 'error': '현재 활성화된 Flow가 없습니다'}

        plan_id = args.strip()

        if self.plan_service.complete_plan(current_flow.id, plan_id):
            plan = self.plan_service.get_plan(current_flow.id, plan_id)
            return {
                'ok': True,
                'data': f"✅ Plan '{plan.name}' 완료 처리되었습니다\n모든 미완료 Task도 완료 처리되었습니다."
            }
        else:
            return {'ok': False, 'error': f"Plan '{plan_id}'를 찾을 수 없습니다"}

    def get_help(self) -> str:
        return "Plan 완료: /plan complete <plan_id>"


class ReopenPlanCommand(Command):
    """Plan 재오픈 명령어"""

    def __init__(self, flow_service: FlowService, plan_service: PlanService):
        self.flow_service = flow_service
        self.plan_service = plan_service

    @property
    def name(self) -> str:
        return "reopen"

    def execute(self, args: str) -> Dict[str, Any]:
        if not args:
            return {'ok': False, 'error': 'Plan ID를 입력하세요'}

        current_flow = self.flow_service.get_current_flow()
        if not current_flow:
            return {'ok': False, 'error': '현재 활성화된 Flow가 없습니다'}

        plan_id = args.strip()

        if self.plan_service.reopen_plan(current_flow.id, plan_id):
            plan = self.plan_service.get_plan(current_flow.id, plan_id)
            return {
                'ok': True,
                'data': f"✅ Plan '{plan.name}' 재오픈되었습니다"
            }
        else:
            return {'ok': False, 'error': f"Plan '{plan_id}'를 찾을 수 없습니다"}

    def get_help(self) -> str:
        return "Plan 재오픈: /plan reopen <plan_id>"
