"""
통합 명령어 프로세서
"""
from typing import Dict, Any, Optional
import difflib

from .command_interface import Command, CommandRegistry, CommandParser
from .flow_commands import (
    CreateFlowCommand, ListFlowsCommand, SwitchFlowCommand, SelectPlanCommand
)
from .plan_commands import (
    AddPlanCommand, ListPlansCommand, CompletePlanCommand, ReopenPlanCommand
)
from .task_commands import (
    AddTaskCommand, ListTasksCommand, StartTaskCommand, CompleteTaskCommand
)
from ..service.flow_service import FlowService
from ..service.plan_service import PlanService
from ..service.task_service import TaskService


class CommandProcessor:
    """통합 명령어 처리기"""

    def __init__(self, flow_service: FlowService, plan_service: PlanService, 
                 task_service: TaskService):
        self.flow_service = flow_service
        self.plan_service = plan_service
        self.task_service = task_service

        self.registry = CommandRegistry()
        self._register_commands()

    def _register_commands(self) -> None:
        """모든 명령어 등록"""
        # Flow 명령어
        self.flow_commands = {
            'create': CreateFlowCommand(self.flow_service),
            'list': ListFlowsCommand(self.flow_service),
            'switch': SwitchFlowCommand(self.flow_service),
        }

        # Plan 명령어
        self.plan_commands = {
            'add': AddPlanCommand(self.flow_service, self.plan_service),
            'list': ListPlansCommand(self.flow_service),
            'complete': CompletePlanCommand(self.flow_service, self.plan_service),
            'reopen': ReopenPlanCommand(self.flow_service, self.plan_service),
        }

        # Task 명령어
        self.task_commands = {
            'add': AddTaskCommand(self.flow_service, self.plan_service, self.task_service),
            'list': ListTasksCommand(self.flow_service),
        }

        # 개별 Task 명령어 (별도 등록)
        self.registry.register(StartTaskCommand(self.flow_service, self.task_service))
        self.registry.register(CompleteTaskCommand(self.flow_service, self.task_service))

        # Plan 선택 명령어
        self.registry.register(SelectPlanCommand(self.flow_service, self.plan_service))

        # Status 명령어
        from .flow_commands import StatusCommand
        self.registry.register(StatusCommand(self.flow_service))

    def process(self, command_string: str) -> Dict[str, Any]:
        """명령어 처리"""
        # 명령어 파싱
        cmd_name, args = CommandParser.parse(command_string)

        if cmd_name is None:
            return {'ok': False, 'error': args}  # args는 에러 메시지

        # 직접 등록된 명령어 처리
        command = self.registry.get(cmd_name)
        if command:
            return command.execute(args)

        # 특수 명령어 처리
        if cmd_name == 'status':
            return self.get_current_status()

        # 복합 명령어 처리 (flow, plan, task)
        if cmd_name in ['flow', 'plan', 'task']:
            return self._handle_compound_command(cmd_name, args)

        # 알 수 없는 명령어
        similar = self._find_similar_commands(cmd_name)
        error_msg = f"알 수 없는 명령어: {cmd_name}"
        if similar:
            error_msg += f"\n혹시 이것을 찾으셨나요? {', '.join(similar)}"

        return {'ok': False, 'error': error_msg}

    def _handle_compound_command(self, cmd_type: str, args: str) -> Dict[str, Any]:
        """복합 명령어 처리 (flow add, plan list 등)"""
        parts = args.split(maxsplit=1)
        if not parts:
            return self._show_help(cmd_type)

        sub_cmd = parts[0].lower()
        sub_args = parts[1] if len(parts) > 1 else ''

        # 명령어 타입별 처리
        commands_map = {
            'flow': self.flow_commands,
            'plan': self.plan_commands,
            'task': self.task_commands,
        }

        commands = commands_map.get(cmd_type, {})

        if sub_cmd in commands:
            return commands[sub_cmd].execute(sub_args)

        # 서브 명령어를 찾을 수 없음
        available = list(commands.keys())
        return {
            'ok': False,
            'error': f"알 수 없는 {cmd_type} 명령어: {sub_cmd}\n"
                    f"사용 가능한 명령어: {', '.join(available)}"
        }

    def _show_help(self, cmd_type: str) -> Dict[str, Any]:
        """도움말 표시"""
        help_text = {
            'flow': """Flow 명령어:
  /flow create <이름>  - 새 Flow 생성
  /flow list          - Flow 목록 보기
  /flow switch <ID>   - Flow 전환""",

            'plan': """Plan 명령어:
  /plan add <이름>       - Plan 추가
  /plan list            - Plan 목록
  /plan complete <ID>   - Plan 완료
  /plan reopen <ID>     - Plan 재오픈""",

            'task': """Task 명령어:
  /task add [plan_id] <이름>  - Task 추가
  /task list [plan_id]        - Task 목록
  /start <task_id>            - Task 시작
  /complete <task_id> [메시지] - Task 완료"""
        }

        return {
            'ok': True,
            'data': help_text.get(cmd_type, f"{cmd_type} 도움말이 없습니다")
        }

    def _find_similar_commands(self, cmd: str) -> list[str]:
        """유사한 명령어 찾기"""
        all_commands = ['flow', 'plan', 'task', 'start', 'complete', 'status', 'help']
        similar = difflib.get_close_matches(cmd, all_commands, n=3, cutoff=0.6)
        return similar

    def get_current_status(self) -> Dict[str, Any]:
        """현재 상태 조회"""
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
