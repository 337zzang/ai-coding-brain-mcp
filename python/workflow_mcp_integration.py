
# python/workflow_mcp_integration.py
"""
MCP 서버와 workflow 명령어 통합
"""

from workflow_commands import workflow_manager, handle_plan, handle_task, handle_next, handle_status
import re
from typing import Tuple, Optional

class WorkflowMCPHandler:
    """MCP 명령어 처리기"""
    
    def __init__(self):
        self.command_patterns = {
            '/plan': r'^/plan\s+(.+?)(?:\s*\|\s*(.+?))?(?:\s+--reset)?$',
            '/task': r'^/task\s+(.+?)(?:\s*\|\s*(.+?))?$',
            '/next': r'^/next(?:\s+(.+))?$',
            '/status': r'^/status$'
        }
    
    def parse_command(self, input_text: str) -> Tuple[Optional[str], dict]:
        """명령어 파싱"""
        input_text = input_text.strip()
        
        # /plan 명령어
        if input_text.startswith('/plan'):
            match = re.match(self.command_patterns['/plan'], input_text)
            if match:
                name = match.group(1).strip()
                description = match.group(2).strip() if match.group(2) else ""
                reset = '--reset' in input_text
                return 'plan', {'name': name, 'description': description, 'reset': reset}
        
        # /task 명령어
        elif input_text.startswith('/task'):
            match = re.match(self.command_patterns['/task'], input_text)
            if match:
                title = match.group(1).strip()
                description = match.group(2).strip() if match.group(2) else ""
                return 'task', {'title': title, 'description': description}
        
        # /next 명령어
        elif input_text.startswith('/next'):
            match = re.match(self.command_patterns['/next'], input_text)
            if match:
                notes = match.group(1).strip() if match.group(1) else ""
                return 'next', {'notes': notes}
        
        # /status 명령어
        elif input_text == '/status':
            return 'status', {}
        
        return None, {}
    
    def execute_command(self, command: str, params: dict) -> str:
        """명령어 실행"""
        try:
            if command == 'plan':
                return handle_plan(**params)
            elif command == 'task':
                return handle_task(**params)
            elif command == 'next':
                return handle_next(**params)
            elif command == 'status':
                return handle_status()
            else:
                return "❌ 알 수 없는 명령어입니다."
        except Exception as e:
            return f"❌ 오류: {str(e)}"
    
    def process_input(self, input_text: str) -> Tuple[bool, str]:
        """입력 처리 - 명령어면 처리하고 True, 아니면 False 반환"""
        command, params = self.parse_command(input_text)
        if command:
            result = self.execute_command(command, params)
            return True, result
        return False, ""

# 전역 핸들러
workflow_handler = WorkflowMCPHandler()

# execute_code에서 사용할 수 있는 헬퍼 함수
def process_workflow_command(input_text: str) -> Optional[str]:
    """워크플로우 명령어 처리 헬퍼"""
    is_command, result = workflow_handler.process_input(input_text)
    return result if is_command else None
