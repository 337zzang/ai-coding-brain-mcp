"""
Task 관련 명령어 구현
"""
from typing import Dict, Any, List

from .command_interface import Command
from ..domain.models import TaskStatus
from ..service.flow_service import FlowService
from ..service.plan_service import PlanService
from ..service.task_service import TaskService


class AddTaskCommand(Command):
    """Task 추가 명령어"""

    def __init__(self, flow_service: FlowService, plan_service: PlanService, task_service: TaskService):
        self.flow_service = flow_service
        self.plan_service = plan_service
        self.task_service = task_service

    @property
    def name(self) -> str:
        return "add"

    def execute(self, args: str) -> Dict[str, Any]:
        if not args:
            return {'ok': False, 'error': 'Task 이름을 입력하세요'}

        current_flow = self.flow_service.get_current_flow()
        if not current_flow:
            return {'ok': False, 'error': '현재 활성화된 Flow가 없습니다'}

        # plan_id와 task 이름 파싱
        parts = args.split(maxsplit=1)
        if len(parts) == 2 and parts[0].startswith('plan_'):
            plan_id = parts[0]
            task_name = parts[1]
        else:
            # Plan ID가 없으면 첫 번째 Plan 사용
            if not current_flow.plans:
                return {'ok': False, 'error': 'Plan이 없습니다. 먼저 Plan을 생성하세요'}

            plan_id = list(current_flow.plans.keys())[0]
            task_name = args

        # Task 생성
        task = self.task_service.create_task(current_flow.id, plan_id, task_name)

        if task:
            return {
                'ok': True,
                'data': {
                    'id': task.id,
                    'name': task.name,
                    'message': f'태스크 추가됨: {task.name} (기본 모드)'
                }
            }
        else:
            return {'ok': False, 'error': 'Task 추가 실패'}

    def get_help(self) -> str:
        return "Task 추가: /task add [plan_id] <이름>"


class ListTasksCommand(Command):
    """Task 목록 명령어"""

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

        # 특정 Plan의 Task만 보기
        plan_filter = args.strip() if args else None

        result = f"📋 Tasks in '{current_flow.name}':\n"
        result += "=" * 50 + "\n"

        task_count = 0
        for plan in current_flow.plans.values():
            if plan_filter and plan_filter not in [plan.id, plan.name]:
                continue

            result += f"\n📁 Plan: {plan.name}\n"
            result += "-" * 40 + "\n"

            if not plan.tasks:
                result += "   (No tasks)\n"
                continue

            for task in plan.tasks.values():
                task_count += 1
                status_icon = {
                    'todo': '⚪',
                    'planning': '📝',
                    'in_progress': '🔄',
                    'reviewing': '🔍',
                    'completed': '✅',
                    'skip': '⏭️',
                    'error': '❌'
                }.get(task.status.value, '❓')

                result += f"   {status_icon} {task.name}\n"
                result += f"      ID: {task.id}\n"
                result += f"      Status: {task.status.value}\n"

                if task.started_at:
                    result += f"      Started: {task.started_at.strftime('%Y-%m-%d %H:%M')}\n"
                if task.completed_at:
                    result += f"      Completed: {task.completed_at.strftime('%Y-%m-%d %H:%M')}\n"

                result += "\n"

        if task_count == 0:
            result = "생성된 Task가 없습니다"
        else:
            result += f"\n총 {task_count}개의 Task"

        return {'ok': True, 'data': result.strip()}

    def get_help(self) -> str:
        return "Task 목록: /task list [plan_id]"


class StartTaskCommand(Command):
    """Task 시작 명령어"""

    def __init__(self, flow_service: FlowService, task_service: TaskService):
        self.flow_service = flow_service
        self.task_service = task_service

    @property
    def name(self) -> str:
        return "start"

    def execute(self, args: str) -> Dict[str, Any]:
        if not args:
            return {'ok': False, 'error': 'Task ID를 입력하세요'}

        current_flow = self.flow_service.get_current_flow()
        if not current_flow:
            return {'ok': False, 'error': '현재 활성화된 Flow가 없습니다'}

        task_id = args.strip()

        # Task 찾기
        for plan in current_flow.plans.values():
            if task_id in plan.tasks:
                task = plan.tasks[task_id]

                # 상태에 따라 다른 상태로 전환
                if task.status == TaskStatus.TODO:
                    new_status = TaskStatus.PLANNING
                else:
                    new_status = TaskStatus.IN_PROGRESS

                if self.task_service.update_task_status(
                    current_flow.id, plan.id, task_id, new_status
                ):
                    return {
                        'ok': True,
                        'data': f"✅ Task '{task.name}' 시작됨 (상태: {new_status.value})"
                    }
                else:
                    return {'ok': False, 'error': '상태 변경 실패'}

        return {'ok': False, 'error': f"Task '{task_id}'를 찾을 수 없습니다"}

    def get_help(self) -> str:
        return "Task 시작: /start <task_id>"


class CompleteTaskCommand(Command):
    """Task 완료 명령어"""

    def __init__(self, flow_service: FlowService, task_service: TaskService):
        self.flow_service = flow_service
        self.task_service = task_service

    @property
    def name(self) -> str:
        return "complete"

    def execute(self, args: str) -> Dict[str, Any]:
        if not args:
            return {'ok': False, 'error': 'Task ID를 입력하세요'}

        current_flow = self.flow_service.get_current_flow()
        if not current_flow:
            return {'ok': False, 'error': '현재 활성화된 Flow가 없습니다'}

        # Task ID와 메시지 파싱
        parts = args.split(maxsplit=1)
        task_id = parts[0]
        message = parts[1] if len(parts) > 1 else ''

        # Task 찾기
        for plan in current_flow.plans.values():
            if task_id in plan.tasks:
                task = plan.tasks[task_id]

                # 메시지가 있으면 context에 추가
                if message:
                    self.task_service.update_task_context(
                        current_flow.id, plan.id, task_id,
                        {'results': message}
                    )

                # 상태를 reviewing으로 변경
                if self.task_service.update_task_status(
                    current_flow.id, plan.id, task_id, TaskStatus.REVIEWING
                ):
                    return {
                        'ok': True,
                        'data': f"✅ Task '{task.name}' 완료 (reviewing)\n{message if message else ''}"
                    }
                else:
                    return {'ok': False, 'error': '상태 변경 실패'}

        return {'ok': False, 'error': f"Task '{task_id}'를 찾을 수 없습니다"}

    def get_help(self) -> str:
        return "Task 완료: /complete <task_id> [메시지]"
