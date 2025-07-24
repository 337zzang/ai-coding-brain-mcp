"""
명령어 라우터 - 데코레이터 기반
"""
from typing import Dict, List, Callable, Any, Optional
import re
import logging

logger = logging.getLogger(__name__)

# 전역 명령어 맵
_command_map: Dict[str, Callable] = {}
_aliases: Dict[str, str] = {}


def command(*names: str, description: str = ""):
    """명령어 등록 데코레이터"""
    def decorator(func: Callable) -> Callable:
        # 첫 번째 이름이 기본
        primary = names[0]
        _command_map[primary] = func

        # 나머지는 별칭
        for name in names[1:]:
            _aliases[name] = primary

        # 설명 저장
        func.__command_desc__ = description
        func.__command_names__ = names

        return func
    return decorator


class CommandRouter:
    """명령어 라우터"""

    def __init__(self, flow_manager):
        self.manager = flow_manager
        self._history = []

    def execute(self, line: str) -> Dict[str, Any]:
        """명령어 실행"""
        line = line.strip()
        if not line:
            return {'ok': False, 'error': '빈 명령어'}

        # 히스토리 저장
        self._history.append(line)

        # /로 시작하면 제거
        if line.startswith('/'):
            line = line[1:]

        # 명령어와 인자 분리
        parts = self._parse_command(line)
        if not parts:
            return {'ok': False, 'error': '명령어 파싱 실패'}

        cmd_name = parts[0]
        args = parts[1:]

        # 별칭 확인
        if cmd_name in _aliases:
            cmd_name = _aliases[cmd_name]

        # 명령어 찾기
        handler = _command_map.get(cmd_name)
        if not handler:
            return {'ok': False, 'error': f'알 수 없는 명령어: {cmd_name}'}

        try:
            # 핸들러 실행
            result = handler(self.manager, args)
            return result if isinstance(result, dict) else {'ok': True, 'data': result}

        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {'ok': False, 'error': str(e)}

    def _parse_command(self, line: str) -> List[str]:
        """명령어 파싱 - 따옴표 처리"""
        # 간단한 따옴표 처리
        parts = []
        current = []
        in_quote = False
        quote_char = None

        for char in line:
            if not in_quote:
                if char in '"\'':  # 따옴표 문자 체크
                    in_quote = True
                    quote_char = char
                elif char.isspace():
                    if current:
                        parts.append(''.join(current))
                        current = []
                else:
                    current.append(char)
            else:
                if char == quote_char:
                    in_quote = False
                    quote_char = None
                else:
                    current.append(char)

        if current:
            parts.append(''.join(current))

        return parts

    def get_commands(self) -> Dict[str, Dict[str, Any]]:
        """등록된 명령어 목록"""
        commands = {}
        for name, func in _command_map.items():
            commands[name] = {
                'names': getattr(func, '__command_names__', [name]),
                'description': getattr(func, '__command_desc__', ''),
                'handler': func.__name__
            }
        return commands

    def help(self, command: Optional[str] = None) -> str:
        """도움말"""
        if command:
            # 특정 명령어 도움말
            if command in _aliases:
                command = _aliases[command]

            func = _command_map.get(command)
            if not func:
                return f"명령어를 찾을 수 없습니다: {command}"

            names = getattr(func, '__command_names__', [command])
            desc = getattr(func, '__command_desc__', '설명 없음')
            return f"명령어: {', '.join(names)}\n설명: {desc}"

        else:
            # 전체 명령어 목록
            lines = ["사용 가능한 명령어:", "-" * 40]

            for name, info in sorted(self.get_commands().items()):
                names_str = ', '.join(info['names'])
                desc = info['description'] or '설명 없음'
                lines.append(f"{names_str:<20} - {desc}")

            return '\n'.join(lines)
