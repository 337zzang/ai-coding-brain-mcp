"""
Flow 관련 명령어 구현
"""
from typing import Dict, Any, List
import uuid
from datetime import datetime

from .command_interface import Command
from ..service.flow_service import FlowService
from ..service.plan_service import PlanService


class CreateFlowCommand(Command):
    """Flow 생성 명령어"""

    def __init__(self, flow_service: FlowService):
        self.flow_service = flow_service

    @property
    def name(self) -> str:
        return "create"

    @property
    def aliases(self) -> List[str]:
        return ["new", "c"]

    def execute(self, args: str) -> Dict[str, Any]:
        if not args:
            return {'ok': False, 'error': 'Flow 이름을 입력하세요'}

        flow_name = args.strip()
        flow = self.flow_service.create_flow(flow_name)

        # 자동으로 현재 Flow로 설정
        self.flow_service.set_current_flow(flow.id)

        return {
            'ok': True,
            'data': f"✅ Flow '{flow.name}' 생성됨\nID: {flow.id}\n현재 Flow로 설정되었습니다."
        }

    def get_help(self) -> str:
        return "새 Flow 생성: /flow create <이름>"


class ListFlowsCommand(Command):
    """Flow 목록 명령어"""

    def __init__(self, flow_service: FlowService):
        self.flow_service = flow_service

    @property
    def name(self) -> str:
        return "list"

    @property
    def aliases(self) -> List[str]:
        return ["ls", "l"]

    def execute(self, args: str) -> Dict[str, Any]:
        flows = self.flow_service.list_flows()

        if not flows:
            return {'ok': True, 'data': "생성된 Flow가 없습니다"}

        current_flow = self.flow_service.get_current_flow()
        current_id = current_flow.id if current_flow else None

        result = "📋 Flow 목록:\n"
        for i, flow in enumerate(flows, 1):
            is_current = "👉 " if flow.id == current_id else "   "
            plans_count = len(flow.plans)
            result += f"{is_current}{i}. {flow.name} (Plans: {plans_count})\n"
            result += f"      ID: {flow.id}\n"

        return {'ok': True, 'data': result.strip()}

    def get_help(self) -> str:
        return "Flow 목록 보기: /flow list"


class SwitchFlowCommand(Command):
    """Flow 전환 명령어"""

    def __init__(self, flow_service: FlowService):
        self.flow_service = flow_service

    @property
    def name(self) -> str:
        return "switch"

    @property
    def aliases(self) -> List[str]:
        return ["use", "checkout"]

    def execute(self, args: str) -> Dict[str, Any]:
        if not args:
            return {'ok': False, 'error': 'Flow ID 또는 이름을 입력하세요'}

        flow_ref = args.strip()

        # ID로 찾기
        flow = self.flow_service.get_flow(flow_ref)

        # 이름으로 찾기
        if not flow:
            flows = self.flow_service.list_flows()
            for f in flows:
                if f.name.lower() == flow_ref.lower():
                    flow = f
                    break

        if not flow:
            return {'ok': False, 'error': f"Flow '{flow_ref}'를 찾을 수 없습니다"}

        if self.flow_service.set_current_flow(flow.id):
            return {
                'ok': True,
                'data': f"✅ Flow '{flow.name}'로 전환했습니다"
            }
        else:
            return {'ok': False, 'error': '전환 실패'}

    def get_help(self) -> str:
        return "Flow 전환: /flow switch <ID 또는 이름>"


class SelectPlanCommand(Command):
    """Plan 선택 명령어 (숫자 입력 처리)"""

    def __init__(self, flow_service: FlowService, plan_service: PlanService):
        self.flow_service = flow_service
        self.plan_service = plan_service

    @property
    def name(self) -> str:
        return "select_plan"

    def execute(self, args: str) -> Dict[str, Any]:
        try:
            # 현재 Flow 확인
            current_flow = self.flow_service.get_current_flow()
            if not current_flow:
                return {'ok': False, 'error': '현재 활성화된 Flow가 없습니다'}

            # Plan 목록 가져오기
            plans = list(current_flow.plans.values())
            if not plans:
                return {'ok': False, 'error': '현재 Flow에 Plan이 없습니다'}

            # Plan 번호로 선택
            plan_idx = int(args) - 1
            if plan_idx < 0 or plan_idx >= len(plans):
                return {'ok': False, 'error': f'잘못된 Plan 번호입니다. 1-{len(plans)} 범위에서 선택하세요.'}

            selected_plan = plans[plan_idx]

            # Plan 분석 결과 생성
            return self._analyze_plan(current_flow.id, selected_plan)

        except ValueError:
            return {'ok': False, 'error': '올바른 Plan 번호를 입력하세요'}
        except Exception as e:
            return {'ok': False, 'error': f'Plan 선택 중 오류: {str(e)}'}

    def _analyze_plan(self, flow_id: str, plan) -> Dict[str, Any]:
        """Plan 분석 결과 생성"""
        # 완료된 Task 찾기
        completed_tasks = [
            task for task in plan.tasks.values()
            if task.status.value in ['completed', 'reviewing']
        ]

        # 미완료 Task 찾기
        incomplete_tasks = [
            task for task in plan.tasks.values()
            if task.status.value not in ['completed', 'reviewing', 'skip']
        ]

        # 결과 메시지 생성
        result_message = f"""
📊 Plan '{plan.name}' 분석 결과

## ✅ 완료된 작업 요약
"""

        if completed_tasks:
            for task in completed_tasks:
                result_message += f"- {task.name}: {task.status.value}\n"
        else:
            result_message += "아직 완료된 작업이 없습니다.\n"

        total_tasks = len(plan.tasks)
        completed_count = len(completed_tasks)

        result_message += f"""
## 🔍 현재 상태 분석
- Plan 진행률: {completed_count}/{total_tasks} Tasks 완료 ({int(completed_count/total_tasks*100) if total_tasks > 0 else 0}%)
- 주요 이슈: 0개 발견

## 💡 다음 단계 권장사항
"""

        for i, task in enumerate(incomplete_tasks[:3], 1):
            result_message += f"{i}. **{task.name}** (상태: {task.status.value})\n"
            result_message += f"   - 시작하려면: `/start {task.id}`\n"

        result_message += f"""
## 🚀 시작하려면
- 특정 Task 시작: `/start task_xxx`
- 새 Task 추가: `/task add {plan.id} 작업명`
- Plan 완료: `/plan complete {plan.id}` (모든 Task 완료 시)

**어떤 작업부터 시작하시겠습니까?**
"""

        return {'ok': True, 'data': result_message.strip()}

    def get_help(self) -> str:
        return "Plan 선택: 숫자 입력 (1, 2, 3...) 또는 'Plan 1 선택'"



class StatusCommand(Command):
    """현재 상태 조회 명령어"""

    def __init__(self, flow_service: FlowService):
        self.flow_service = flow_service

    @property
    def name(self) -> str:
        return "status"

    def execute(self, args: str) -> Dict[str, Any]:
        current_flow = self.flow_service.get_current_flow()

        if not current_flow:
            return {
                'ok': True,
                'data': "현재 활성화된 Flow가 없습니다.\n/flow create 명령으로 새 Flow를 생성하세요."
            }

        # 통계 계산
        total_plans = len(current_flow.plans)
        completed_plans = sum(1 for p in current_flow.plans.values() if p.completed)

        total_tasks = 0
        completed_tasks = 0
        for plan in current_flow.plans.values():
            total_tasks += len(plan.tasks)
            completed_tasks += sum(1 for t in plan.tasks.values() 
                                 if t.status.value in ['completed', 'reviewing'])

        status = f"""📊 현재 상태

Flow: {current_flow.name}
Plans: {completed_plans}/{total_plans} 완료
Tasks: {completed_tasks}/{total_tasks} 완료

다음 명령어를 사용할 수 있습니다:
- /plan list - Plan 목록 보기
- /task list - Task 목록 보기
- 숫자 입력 (1, 2, 3...) - Plan 선택"""

        return {'ok': True, 'data': status}

    def get_help(self) -> str:
        return "현재 상태 조회: /status"
