"""
Workflow v3 Dispatcher
명령어 라우팅 및 실행
"""
from typing import Dict, Any
import os

from .manager import WorkflowManager
from .parser import CommandParser
from .storage import FileStorage
from .errors import WorkflowError


class WorkflowDispatcher:
    """워크플로우 명령어 디스패처"""
    
    def __init__(self, storage_path: str = None):
        if storage_path is None:
            storage_path = os.path.join('memory', 'workflow_v3')
        
        self.storage = FileStorage(storage_path)
        self.manager = WorkflowManager(storage=self.storage)
        self.parser = CommandParser()
        
    def execute(self, command: str) -> Dict[str, Any]:
        """명령어 실행"""
        try:
            # 명령어 파싱
            parsed = self.parser.parse(command)
            
            # 매니저로 실행
            result = self.manager.execute(parsed)
            
            return result
            
        except WorkflowError as e:
            return {
                'success': False,
                'error': str(e),
                'error_code': e.code.value
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


# 전역 디스패처 인스턴스
_dispatcher = None


def get_dispatcher() -> WorkflowDispatcher:
    """전역 디스패처 인스턴스 가져오기"""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = WorkflowDispatcher()
    return _dispatcher


def execute_workflow_command(command: str) -> Dict[str, Any]:
    """워크플로우 명령어 실행 (공개 API)"""
    dispatcher = get_dispatcher()
    return dispatcher.execute(command)
