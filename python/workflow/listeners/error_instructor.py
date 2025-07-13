"""
Error Instructor for AI Actions
에러 발생 시 AI에게 즉각적인 해결 지시를 내리는 리스너
"""
from python.workflow.listeners.base import BaseEventListener
from python.workflow.listeners.ai_instruction_base import AIInstruction, ActionType, Priority
from python.workflow.events import EventType, WorkflowEvent
from typing import List, Dict, Any
import os
import traceback

class ErrorInstructor(BaseEventListener):
    """에러 발생 시 AI에게 해결 지시"""

    def __init__(self):
        super().__init__()
        self.instruction_path = "logs/ai_instructions.json"

    def get_subscribed_events(self) -> List[EventType]:
        return [EventType.TASK_FAILED]

    def handle_event(self, event: WorkflowEvent) -> bool:
        """에러 이벤트를 AI 해결 지시로 변환"""
        try:
            error_type = event.details.get('error_type', 'UnknownError')
            error_message = event.details.get('message', 'No error message')

            # AI 지시서 생성 (긴급)
            instruction = AIInstruction(
                event_type="error_occurred",
                context={
                    "task_id": event.task_id,
                    "task_title": event.details.get('title', 'Unknown Task'),
                    "error_type": error_type,
                    "error_message": error_message,
                    "stack_trace": event.details.get('stack_trace', ''),
                    "timestamp": event.timestamp.isoformat()
                }
            )

            # 에러 타입별 해결 지시
            if "FileNotFound" in error_type:
                self._add_file_not_found_actions(instruction, event)
            elif "Permission" in error_type:
                self._add_permission_error_actions(instruction, event)
            elif "Import" in error_type or "Module" in error_type:
                self._add_import_error_actions(instruction, event)
            elif "Syntax" in error_type:
                self._add_syntax_error_actions(instruction, event)
            elif "Connection" in error_type or "Network" in error_type:
                self._add_network_error_actions(instruction, event)
            else:
                self._add_generic_error_actions(instruction, event)

            # 공통 작업: 에러 보고
            instruction.add_action(
                ActionType.REPORT_USER,
                params={
                    "message": f"⚠️ 에러 발생: {error_type}\n{error_message}\n\n해결 작업을 진행합니다...",
                    "format": "markdown",
                    "level": "error"
                },
                order=1  # 가장 먼저 실행
            )

            # 긴급 우선순위 설정
            instruction.set_priority(Priority.CRITICAL)

            # 지시서 저장
            instruction.save()

            print(f"🚨 ErrorInstructor: {error_type} 해결 지시 생성")
            print(f"   - {len(instruction.actions)}개 해결 작업 지시")

            return True

        except Exception as e:
            print(f"❌ ErrorInstructor 자체 오류: {e}")
            return False

    def _add_file_not_found_actions(self, instruction: AIInstruction, event: WorkflowEvent):
        """파일 없음 에러 해결 지시"""
        file_path = self._extract_file_path(event.details.get('message', ''))

        # 1. 파일 존재 확인
        instruction.add_action(
            ActionType.WORKFLOW_COMMAND,
            params={
                "command": f"helpers.file_exists('{file_path}')",
                "purpose": "파일 존재 여부 재확인"
            }
        )

        # 2. 파일 생성 지시
        instruction.add_action(
            ActionType.CREATE_FILE,
            params={
                "path": file_path,
                "content": "# Auto-generated file\n# TODO: Add content",
                "reason": "FileNotFoundError 해결을 위한 자동 생성"
            }
        )

        # 3. 작업 재시도 지시
        instruction.add_action(
            ActionType.WORKFLOW_COMMAND,
            params={
                "command": f"/retry {event.task_id}",
                "reason": "파일 생성 후 태스크 재시도"
            }
        )

    def _add_permission_error_actions(self, instruction: AIInstruction, event: WorkflowEvent):
        """권한 에러 해결 지시"""
        # 1. 권한 확인
        instruction.add_action(
            ActionType.WORKFLOW_COMMAND,
            params={
                "command": "import os; os.access(path, os.W_OK)",
                "purpose": "쓰기 권한 확인"
            }
        )

        # 2. 대안 경로 사용
        instruction.add_action(
            ActionType.WORKFLOW_COMMAND,
            params={
                "command": "# 임시 디렉토리 사용",
                "alternative_path": "temp/",
                "reason": "권한 문제 우회"
            }
        )

    def _add_import_error_actions(self, instruction: AIInstruction, event: WorkflowEvent):
        """Import 에러 해결 지시"""
        module_name = self._extract_module_name(event.details.get('message', ''))

        # 1. 모듈 설치 시도
        instruction.add_action(
            ActionType.WORKFLOW_COMMAND,
            params={
                "command": f"pip install {module_name}",
                "purpose": "누락된 모듈 설치"
            }
        )

        # 2. requirements.txt 업데이트
        instruction.add_action(
            ActionType.UPDATE_FILE,
            params={
                "path": "requirements.txt",
                "content": f"\n{module_name}",
                "mode": "append"
            }
        )

        # 3. 대체 import 경로 확인
        instruction.add_action(
            ActionType.ANALYZE_CODE,
            params={
                "action": "find_alternative_import",
                "module": module_name
            }
        )

    def _add_syntax_error_actions(self, instruction: AIInstruction, event: WorkflowEvent):
        """문법 에러 해결 지시"""
        # 1. 문법 검사
        instruction.add_action(
            ActionType.ANALYZE_CODE,
            params={
                "action": "check_syntax",
                "file": event.details.get('file', ''),
                "line": event.details.get('line', 0)
            }
        )

        # 2. 자동 수정 시도
        instruction.add_action(
            ActionType.FIX_ERROR,
            params={
                "error_type": "syntax",
                "auto_fix": True
            }
        )

    def _add_network_error_actions(self, instruction: AIInstruction, event: WorkflowEvent):
        """네트워크 에러 해결 지시"""
        # 1. 연결 재시도
        instruction.add_action(
            ActionType.WORKFLOW_COMMAND,
            params={
                "command": "# 3초 대기 후 재시도",
                "wait": 3,
                "retry": True
            }
        )

        # 2. 오프라인 모드 전환
        instruction.add_action(
            ActionType.WORKFLOW_COMMAND,
            params={
                "command": "# 오프라인 모드로 전환",
                "offline_mode": True
            }
        )

    def _add_generic_error_actions(self, instruction: AIInstruction, event: WorkflowEvent):
        """일반 에러 해결 지시"""
        # 1. 상세 분석
        instruction.add_action(
            ActionType.ANALYZE_CODE,
            params={
                "action": "analyze_error",
                "error_message": event.details.get('message', ''),
                "context": event.details
            }
        )

        # 2. 스택 트레이스 분석
        instruction.add_action(
            ActionType.WORKFLOW_COMMAND,
            params={
                "command": "# 스택 트레이스 분석 및 원인 파악",
                "analyze_stack": True
            }
        )

        # 3. 일반적인 해결 시도
        instruction.add_action(
            ActionType.FIX_ERROR,
            params={
                "strategy": "generic",
                "fallback": True
            }
        )

    def _extract_file_path(self, error_message: str) -> str:
        """에러 메시지에서 파일 경로 추출"""
        import re
        # 파일 경로 패턴 매칭
        patterns = [
            r"'([^']+\.\w+)'",  # 'file.ext' 형태
            r'"([^"]+\.\w+)"',  # "file.ext" 형태
            r'\b([\w/\\]+\.\w+)\b'  # path/file.ext 형태
        ]

        for pattern in patterns:
            match = re.search(pattern, error_message)
            if match:
                return match.group(1)

        return "unknown_file"

    def _extract_module_name(self, error_message: str) -> str:
        """에러 메시지에서 모듈명 추출"""
        import re
        # 모듈명 패턴 매칭
        patterns = [
            r"No module named '([^']+)'",
            r'No module named "([^"]+)"',
            r"cannot import name '([^']+)'"
        ]

        for pattern in patterns:
            match = re.search(pattern, error_message)
            if match:
                return match.group(1).split('.')[0]  # 최상위 모듈명만

        return "unknown_module"
