"""
명령어 처리 인터페이스 및 기본 클래스
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import re


class Command(ABC):
    """명령어 추상 클래스"""

    @abstractmethod
    def execute(self, args: str) -> Dict[str, Any]:
        """명령어 실행"""
        pass

    @abstractmethod
    def get_help(self) -> str:
        """도움말 반환"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """명령어 이름"""
        pass

    @property
    def aliases(self) -> List[str]:
        """명령어 별칭"""
        return []


class CommandRegistry:
    """명령어 레지스트리"""

    def __init__(self):
        self.commands: Dict[str, Command] = {}
        self.aliases: Dict[str, str] = {}

    def register(self, command: Command) -> None:
        """명령어 등록"""
        self.commands[command.name] = command

        # 별칭 등록
        for alias in command.aliases:
            self.aliases[alias] = command.name

    def get(self, name: str) -> Optional[Command]:
        """명령어 조회"""
        # 직접 이름으로 찾기
        if name in self.commands:
            return self.commands[name]

        # 별칭으로 찾기
        if name in self.aliases:
            return self.commands[self.aliases[name]]

        return None

    def list_commands(self) -> List[str]:
        """모든 명령어 목록"""
        return list(self.commands.keys())


class CommandParser:
    """명령어 파서"""

    @staticmethod
    def parse(command_string: str) -> tuple[Optional[str], str]:
        """명령어 문자열 파싱

        Returns:
            (command_name, args) 또는 (None, error_message)
        """
        if not command_string:
            return None, "빈 명령어입니다"

        # Plan 선택 패턴 체크 (숫자만)
        if re.match(r'^\d+$', command_string.strip()):
            return 'select_plan', command_string.strip()

        # Plan 선택 다른 패턴들
        plan_patterns = [
            (r'^[Pp]lan\s+(\d+)$', 'select_plan'),
            (r'^[Pp]lan\s+(\d+)\s*선택', 'select_plan'),
            (r'^(\d+)번\s*[Pp]lan', 'select_plan')
        ]

        for pattern, cmd_name in plan_patterns:
            match = re.match(pattern, command_string.strip())
            if match:
                return cmd_name, match.group(1)

        # 일반 명령어 (/ 로 시작)
        if not command_string.startswith('/'):
            return None, "명령어는 /로 시작해야 합니다"

        # 명령어와 인자 분리
        parts = command_string[1:].split(maxsplit=1)
        if not parts:
            return None, "빈 명령어입니다"

        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ''

        return cmd, args
