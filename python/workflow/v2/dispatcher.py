"""
워크플로우 명령어 중앙 디스패처 v3
문자열 명령어를 파싱하여 적절한 핸들러 함수로 라우팅
간소화된 7개 핵심 명령어 체계
"""

from typing import Dict, Callable, Optional, Any, Tuple
from python.ai_helpers.helper_result import HelperResult
from .handlers import *
import re

class WorkflowDispatcher:
    """워크플로우 명령어 중앙 처리기 v3"""

    def __init__(self):
        # 7개 핵심 명령어로 간소화
        self.command_map: Dict[str, Callable] = {
            'start': workflow_start,
            'focus': workflow_focus,  
            'plan': workflow_plan,      # list 기능 통합
            'task': workflow_task,      # tasks, current 기능 통합  
            'next': workflow_next,      # done, complete 기능 통합
            'build': workflow_build,    # review 기능 통합
            'status': workflow_status,  # history 기능 통합
        }

        # 짧은 별칭 지원
        self.aliases = {
            's': 'start',
            'f': 'focus', 
            'p': 'plan',
            't': 'task',
            'n': 'next',
            'b': 'build',
        }

        # 레거시 명령어 -> 새 명령어 매핑 (하위 호환성)
        self.legacy_map = {
            'list': ('plan', 'list'),
            'current': ('focus', ''),
            'tasks': ('task', ''),
            'done': ('next', ''),
            'complete': ('next', ''),
            'history': ('status', 'history'),
            'review': ('build', 'review'),
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

            # 별칭 처리
            if cmd in self.aliases:
                cmd = self.aliases[cmd]

            # 레거시 명령어 처리
            if cmd in self.legacy_map:
                new_cmd, extra_args = self.legacy_map[cmd]
                cmd = new_cmd
                if extra_args:
                    args = f"{extra_args} {args}".strip()

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
                # 파이프(|)로 제목과 설명 분리
                if '|' in args:
                    parts = [p.strip() for p in args.split('|', 1)]
                    title = parts[0]
                    description = parts[1] if len(parts) > 1 else ""
                else:
                    title = args.strip()
                    description = ""

                # 하위 명령어 처리 (예: /plan list, /task current)
                if cmd == 'plan' and title.lower() == 'list':
                    return workflow_list_plans()
                elif cmd == 'task' and title.lower() == 'current':
                    return workflow_current()
                elif cmd == 'task' and not title:
                    return workflow_tasks()  # /task만 입력시 목록 표시

                return func(title, description)

            elif cmd == 'status':
                # /status history 처리
                if args.lower().strip() == 'history':
                    return workflow_history()
                return func()

            elif cmd == 'build':
                # /build review 처리
                if args.lower().strip() == 'review':
                    return workflow_review()
                elif args.lower().strip() == 'task':
                    # 현재 태스크 문서화
                    return func('task')
                return func()

            elif cmd in ['done', 'complete', 'next']:
                # 완료 메모와 함께
                note = args.strip() if args else ""
                return func(note)

            elif cmd == 'focus':
                # 태스크 번호 또는 빈 값
                return func(args.strip() if args else "")

            elif cmd == 'start':
                # 새 플랜 이름 또는 빈 값
                return func(args.strip() if args else "")

            else:
                # 기본: 전체 인자를 그대로 전달
                return func(args) if args else func()

        except TypeError as e:
            # 함수 시그니처 불일치
            return HelperResult(False,
                error=f"Invalid arguments for /{cmd}: {str(e)}",
                data={"usage": self._get_command_usage(cmd)})

    def _get_command_usage(self, cmd: str) -> str:
        """명령어별 사용법 안내"""
        usage_map = {
            'start': "/start [플랜명] - 새 플랜 시작 또는 재개",
            'focus': "/focus [태스크번호] - 특정 태스크 선택",
            'plan': "/plan [이름 | 설명] 또는 /plan list",
            'task': "/task [제목 | 설명] 또는 /task (목록)",
            'next': "/next [완료메모] - 완료 후 다음으로",
            'build': "/build 또는 /build task 또는 /build review",
            'status': "/status 또는 /status history"
        }
        return usage_map.get(cmd, f"/{cmd} [arguments]")
