"""
Workflow v3 명령어 파서
개선된 명령어 파싱 및 검증 로직
"""
from typing import Dict, Tuple, Optional, List, Any
from dataclasses import dataclass
import re


@dataclass
class ParsedCommand:
    """파싱된 명령어 구조"""
    command: str  # 주 명령어 (예: 'task', 'plan')
    subcommand: Optional[str] = None  # 하위 명령어 (예: 'list', 'add')
    title: str = ""  # 제목/이름
    description: str = ""  # 설명
    args: Dict[str, Any] = None  # 추가 인자
    raw: str = ""  # 원본 명령어
    
    def __post_init__(self):
        if self.args is None:
            self.args = {}


class CommandParser:
    """워크플로우 명령어 파서"""
    
    # 7개 핵심 명령어
    CORE_COMMANDS = {
        'start', 'focus', 'plan', 'task', 
        'next', 'build', 'status'
    }
    
    # 명령어 별칭
    ALIASES = {
        's': 'start',
        'f': 'focus',
        'p': 'plan', 
        't': 'task',
        'n': 'next',
        'b': 'build',
        'st': 'status'
    }
    
    # 레거시 명령어 매핑
    LEGACY_MAP = {
        'list': ('plan', 'list'),
        'current': ('focus', None),
        'tasks': ('task', None),
        'done': ('next', None),
        'complete': ('next', None),
        'history': ('status', 'history'),
        'review': ('build', 'review')
    }
    
    # 서브커맨드 정의
    SUBCOMMANDS = {
        'plan': ['list'],
        'task': ['add', 'current'],
        'status': ['history'],
        'build': ['review', 'task']
    }

    
    # 제거해야 할 키워드
    REMOVE_KEYWORDS = {
        'task': ['add'],  # /task add -> add 제거
    }
    
    def parse(self, command_str: str) -> ParsedCommand:
        """명령어 문자열 파싱
        
        Args:
            command_str: 슬래시로 시작하는 명령어 문자열
            
        Returns:
            ParsedCommand: 파싱된 명령어 객체
            
        Raises:
            ValueError: 잘못된 명령어 형식
        """
        # 기본 검증
        if not command_str:
            raise ValueError("명령어가 비어있습니다")
            
        command_str = command_str.strip()
        if not command_str.startswith('/'):
            raise ValueError("명령어는 '/'로 시작해야 합니다")
            
        # 슬래시 제거하고 파싱
        cmd_parts = command_str[1:].strip()
        if not cmd_parts:
            raise ValueError("명령어가 비어있습니다")
            
        # 공백으로 분리
        parts = cmd_parts.split(None, 2)  # 최대 3개로 분리 (명령, 서브커맨드, 나머지)
        main_cmd = parts[0].lower()
        
        # 별칭 처리
        if main_cmd in self.ALIASES:
            main_cmd = self.ALIASES[main_cmd]
            
        # 레거시 명령어 처리
        if main_cmd in self.LEGACY_MAP:
            main_cmd, subcommand = self.LEGACY_MAP[main_cmd]
            parsed = ParsedCommand(
                command=main_cmd,
                subcommand=subcommand,
                raw=command_str
            )
            # 레거시 명령어는 추가 파싱 없이 반환
            if len(parts) > 1:
                parsed.title = ' '.join(parts[1:])
            return parsed
            
        # 유효한 명령어인지 확인
        if main_cmd not in self.CORE_COMMANDS:
            raise ValueError(f"알 수 없는 명령어: {main_cmd}")
            
        # ParsedCommand 객체 생성
        parsed = ParsedCommand(command=main_cmd, raw=command_str)
        
        # 서브커맨드 우선 체크
        subcommand = None
        remaining = ""
        
        if len(parts) > 1:
            # 두 번째 단어가 서브커맨드인지 확인
            potential_subcmd = parts[1].lower()
            if main_cmd in self.SUBCOMMANDS and potential_subcmd in self.SUBCOMMANDS[main_cmd]:
                subcommand = potential_subcmd
                parsed.subcommand = subcommand
                # 나머지 인자는 세 번째부터
                remaining = ' '.join(parts[2:]) if len(parts) > 2 else ""
            else:
                # 서브커맨드가 아니면 두 번째부터 모두 인자로 처리
                remaining = ' '.join(parts[1:])
        
        # 명령어별 파싱
        if main_cmd in ['start', 'plan']:
            self._parse_start(remaining, parsed)
        elif main_cmd == 'focus':
            self._parse_focus(remaining, parsed)
        elif main_cmd == 'plan':
            self._parse_plan(remaining, parsed)
        elif main_cmd == 'task':
            self._parse_task(remaining, parsed)
        elif main_cmd == 'next':
            self._parse_next(remaining, parsed)
        elif main_cmd == 'build':
            self._parse_build(remaining, parsed)
        elif main_cmd == 'status':
            self._parse_status(remaining, parsed)
            
        return parsed

        
    def _parse_title_description(self, text: str) -> Tuple[str, str]:
        """제목과 설명 파싱 (파이프 구분)"""
        if '|' in text:
            parts = text.split('|', 1)
            title = parts[0].strip()
            description = parts[1].strip() if len(parts) > 1 else ""
        else:
            title = text.strip()
            description = ""
        return title, description
        
    def _parse_start(self, args: str, parsed: ParsedCommand) -> None:
        """start/plan 명령어 파싱"""
        if args:
            parsed.title, parsed.description = self._parse_title_description(args)
            # 플랜 이름 검증
            if not parsed.title:
                raise ValueError("플랜 이름을 입력해주세요")
            if len(parsed.title) > 200:
                raise ValueError("플랜 이름은 200자를 초과할 수 없습니다")
                
    def _parse_focus(self, args: str, parsed: ParsedCommand) -> None:
        """focus 명령어 파싱"""
        if args:
            # 태스크 번호 또는 ID
            parsed.title = args.strip()
            # 숫자인지 확인
            if parsed.title.isdigit():
                parsed.args['task_number'] = int(parsed.title)
            else:
                parsed.args['task_id'] = parsed.title
                
    def _parse_plan(self, args: str, parsed: ParsedCommand) -> None:
        """plan 명령어 파싱"""
        # 서브커맨드가 이미 설정된 경우 (우선 처리됨)
        if parsed.subcommand:
            if parsed.subcommand == 'list':
                # list는 추가 인자 필요 없음
                return
            # 다른 서브커맨드 처리...
            return
            
        if not args:
            # 인자 없으면 현재 플랜 조회
            return
            
        # 새 플랜 생성
        parsed.title, parsed.description = self._parse_title_description(args)
        if not parsed.title:
            raise ValueError("플랜 이름을 입력해주세요")
        if len(parsed.title) > 200:
            raise ValueError("플랜 이름은 200자를 초과할 수 없습니다")
        
        # --reset 옵션 확인
        if '--reset' in parsed.description:
            parsed.args['reset'] = True
            parsed.description = parsed.description.replace('--reset', '').strip()

                
    def _parse_task(self, args: str, parsed: ParsedCommand) -> None:
        """task 명령어 파싱"""
        if not args:
            # 인자 없으면 오류 발생
            raise ValueError("태스크 제목을 입력해주세요. 예: /task 새로운 작업")
            
        args_lower = args.lower()
        
        # current 서브커맨드 확인
        if args_lower == 'current':
            parsed.subcommand = 'current'
            return
            
        # note 서브커맨드 확인
        if args_lower.startswith('note '):
            parsed.subcommand = 'note'
            note_text = args[5:].strip()  # 'note ' 제거
            # 따옴표 제거
            if note_text.startswith('"') and note_text.endswith('"'):
                note_text = note_text[1:-1]
            elif note_text.startswith("'") and note_text.endswith("'"):
                note_text = note_text[1:-1]
            if not note_text:
                raise ValueError("노트 내용을 입력해주세요")
            parsed.title = note_text  # 노트 내용을 title에 저장
            parsed.args['note'] = note_text
            return
            
        # add 키워드 제거
        if args_lower.startswith('add '):
            args = args[4:].strip()
            if not args:
                raise ValueError("태스크 제목을 입력해주세요")
        elif args_lower == 'add':
            raise ValueError("태스크 제목을 입력해주세요. 예: /task add 데이터베이스 설계")
            
        # 제목과 설명 파싱
        parsed.title, parsed.description = self._parse_title_description(args)
        if not parsed.title:
            raise ValueError("태스크 제목을 입력해주세요")
        if len(parsed.title) > 200:
            raise ValueError("태스크 제목은 200자를 초과할 수 없습니다")
            
    def _parse_next(self, args: str, parsed: ParsedCommand) -> None:
        """next 명령어 파싱"""
        if args:
            # 완료 메모
            parsed.title = args.strip()
            parsed.args['note'] = parsed.title
            
    def _parse_build(self, args: str, parsed: ParsedCommand) -> None:
        """build 명령어 파싱"""
        if not args:
            return
            
        args_lower = args.lower().strip()
        if args_lower == 'review':
            parsed.subcommand = 'review'
        elif args_lower == 'task':
            parsed.subcommand = 'task'
        else:
            # 기타 빌드 옵션
            parsed.title = args
            
    def _parse_status(self, args: str, parsed: ParsedCommand) -> None:
        """status 명령어 파싱"""
        if args:
            args_lower = args.lower().strip()
            if args_lower == 'history':
                parsed.subcommand = 'history'

                
    def validate_title(self, title: str, field_name: str = "제목") -> str:
        """제목 검증 및 정규화"""
        if not title:
            raise ValueError(f"{field_name}을(를) 입력해주세요")
            
        title = title.strip()
        if not title:
            raise ValueError(f"{field_name}은(는) 공백만으로 구성될 수 없습니다")
            
        if len(title) > 200:
            raise ValueError(f"{field_name}은(는) 200자를 초과할 수 없습니다")
            
        return title
        
    @staticmethod
    def extract_command(text: str) -> Optional[str]:
        """텍스트에서 명령어 추출 (슬래시로 시작하는 부분)"""
        # 줄 시작 또는 공백 후 /로 시작하는 패턴 찾기
        match = re.search(r'(?:^|\s)(/\S+(?:\s+[^/]*)?)', text)
        if match:
            return match.group(1).strip()
        return None
        
    def get_help(self, command: Optional[str] = None) -> str:
        """명령어 도움말"""
        if not command:
            # 전체 명령어 도움말
            help_text = "📚 워크플로우 명령어 도움말\n\n"
            help_text += "🎯 7개 핵심 명령어:\n"
            help_text += "  /start [플랜명] - 새 플랜 시작\n"
            help_text += "  /focus [번호] - 특정 태스크 선택\n"
            help_text += "  /plan [list|플랜명] - 플랜 관리\n"
            help_text += "  /task [제목] - 태스크 추가/목록\n"
            help_text += "  /next [메모] - 완료 및 다음\n"
            help_text += "  /build [review] - 문서화\n"
            help_text += "  /status [history] - 상태 확인\n\n"
            help_text += "🔤 별칭: s, f, p, t, n, b\n"
            return help_text
            
        # 특정 명령어 도움말
        cmd = command.lower()
        if cmd in self.ALIASES:
            cmd = self.ALIASES[cmd]
            
        help_map = {
            'plan': "/plan [플랜명 | 설명] - 새로운 워크플로우 플랜 생성",
            'focus': "/focus [태스크 번호 또는 ID] - 특정 태스크로 포커스 이동",
            'plan': "/plan [list] 또는 /plan [플랜명 | 설명] - 플랜 조회/생성",
            'task': "/task [제목 | 설명] - 새 태스크 추가 또는 목록 조회",
            'next': "/next [완료 메모] - 현재 태스크 완료하고 다음으로",
            'build': "/build [review|task] - 코드/결과물 문서화",
            'status': "/status [history] - 현재 상태 또는 히스토리 조회"
        }
        
        return help_map.get(cmd, f"❌ 알 수 없는 명령어: {command}")
