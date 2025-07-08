"""
워크플로우 명령어 중앙 디스패처
문자열 명령어를 파싱하여 적절한 핸들러 함수로 라우팅
"""

from typing import Dict, Callable, Optional, Any
from python.ai_helpers.helper_result import HelperResult
from .handlers import *
import re

class WorkflowDispatcher:
    """워크플로우 명령어 중앙 처리기"""

    def __init__(self):
        # 명령어 -> 함수 매핑
        self.command_map: Dict[str, Callable] = {
            'plan': workflow_plan,
            'task': workflow_task,
            'done': workflow_done,
            'complete': workflow_done,  # alias
            'next': workflow_next,
            'current': workflow_current,
            'tasks': workflow_tasks,
            'status': workflow_status,
            'history': workflow_history,
            'start': workflow_start,
            'focus': workflow_focus,
            'list': workflow_list_plans,
            'build': workflow_build,
            'review': workflow_review,
        }

    def execute(self, command: str) -> HelperResult:
        """명령어 문자열 실행

        Args:
            command: 슬래시 명령어 (예: "/plan 새 프로젝트 | 설명")

        Returns:
            HelperResult: 실행 결과
        """
        try:
            # 빈 명령어 체크
            if not command or not command.strip():
                return HelperResult(False, error="Empty command")

            command = command.strip()

            # 슬래시 확인
            if not command.startswith('/'):
                return HelperResult(False, 
                    error="Commands must start with '/'",
                    data={"example": "/plan My Project | Description"})

            # 명령어와 인자 분리
            parts = command[1:].split(None, 1)  # '/' 제거 후 분리
            if not parts:
                return HelperResult(False, error="Invalid command format")

            cmd = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""

            # 함수 찾기
            func = self.command_map.get(cmd)
            if not func:
                available = list(self.command_map.keys())
                return HelperResult(False, 
                    error=f"Unknown command: /{cmd}",
                    data={
                        "available_commands": available,
                        "suggestion": f"Did you mean: /{self._find_similar_command(cmd, available)}?"
                    })

            # 함수별 인자 파싱 및 실행
            return self._execute_function(func, cmd, args)

        except Exception as e:
            return HelperResult(False, 
                error=f"Command execution failed: {str(e)}",
                data={"command": command})

    def _find_similar_command(self, cmd: str, available: list) -> str:
        """유사한 명령어 찾기 (오타 수정용)"""
        # 간단한 유사도 체크
        for valid_cmd in available:
            if cmd in valid_cmd or valid_cmd in cmd:
                return valid_cmd
            if abs(len(cmd) - len(valid_cmd)) <= 2:
                # 레벤슈타인 거리 간단 체크
                common = sum(c1 == c2 for c1, c2 in zip(cmd, valid_cmd))
                if common >= len(cmd) * 0.6:
                    return valid_cmd
        return available[0] if available else "help"

    def _execute_function(self, func: Callable, cmd: str, args: str) -> HelperResult:
        """함수별 맞춤 인자 파싱 및 실행"""

        try:
            # 명령어별 파싱 로직
            if cmd in ['plan', 'task']:
                # "제목 | 설명" 형식 파싱
                if '|' in args:
                    parts = args.split('|', 1)
                    title = parts[0].strip()
                    desc = parts[1].strip()
                else:
                    title = args.strip()
                    desc = ""

                if not title:
                    return HelperResult(False, error=f"/{cmd} requires a title")

                if cmd == 'plan':
                    # --reset 옵션 체크
                    reset = '--reset' in args
                    if reset:
                        title = title.replace('--reset', '').strip()
                    return func(title, desc, reset=reset)
                else:
                    return func(title, desc)

            elif cmd in ['done', 'complete']:
                # 완료 메모
                notes = args.strip()
                return func(notes=notes)

            elif cmd in ['start']:
                # "프로젝트명 | 설명" 형식
                if '|' in args:
                    parts = args.split('|', 1)
                    name = parts[0].strip()
                    desc = parts[1].strip()
                    return func(name, desc)
                else:
                    name = args.strip()
                    if not name:
                        return HelperResult(False, error="/start requires a project name")
                    return func(name)

            elif cmd in ['focus']:
                # 프로젝트명만
                project = args.strip()
                if not project:
                    return HelperResult(False, error="/focus requires a project name")
                return func(project)

            elif cmd == 'review':
                # scope 옵션
                scope = args.strip() if args else "current"
                return func(scope=scope)

            elif cmd == 'build':
                # --no-readme 옵션
                update_readme = '--no-readme' not in args
                return func(update_readme=update_readme)

            else:
                # 인자 없는 명령어들
                if args:
                    return HelperResult(False, 
                        error=f"/{cmd} does not accept arguments",
                        data={"provided_args": args})
                return func()

        except TypeError as e:
            # 함수 시그니처 불일치
            return HelperResult(False,
                error=f"Invalid arguments for /{cmd}: {str(e)}",
                data={"usage": self._get_command_usage(cmd)})
        except Exception as e:
            return HelperResult(False, error=str(e))

    def _get_command_usage(self, cmd: str) -> str:
        """명령어 사용법 반환"""
        usage_map = {
            'plan': "/plan <name> | <description> [--reset]",
            'task': "/task <title> | <description>",
            'done': "/done [notes]",
            'complete': "/complete [notes]",
            'start': "/start <project_name> [| description]",
            'focus': "/focus <project_name>",
            'review': "/review [scope]",
            'build': "/build [--no-readme]",
            'next': "/next",
            'current': "/current",
            'tasks': "/tasks",
            'status': "/status",
            'history': "/history",
            'list': "/list"
        }
        return usage_map.get(cmd, f"/{cmd}")

# 글로벌 디스패처 인스턴스
_dispatcher = WorkflowDispatcher()

def execute_workflow_command(command: str) -> HelperResult:
    """워크플로우 명령어 실행 (외부 인터페이스)

    Args:
        command: 실행할 명령어 (예: "/plan My Project")

    Returns:
        HelperResult: 실행 결과
    """
    return _dispatcher.execute(command)

# Export
__all__ = ['WorkflowDispatcher', 'execute_workflow_command']
