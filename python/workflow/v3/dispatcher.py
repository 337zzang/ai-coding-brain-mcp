"""
Workflow v3 Dispatcher
명령어 라우팅 및 실행
"""
from typing import Dict, Any
import os

from .manager import WorkflowManager
from .parser import CommandParser
from .storage import WorkflowStorage
from .errors import WorkflowError


class WorkflowDispatcher:
    """워크플로우 명령어 디스패처"""
    
    def __init__(self, project_name: str = "default", storage_path: str = None):
        if storage_path is None:
            storage_path = os.path.join('memory', 'workflow_v3')
        
        self.project_name = project_name
        # 싱글톤 패턴 사용
        self.manager = WorkflowManager.get_instance(project_name)
        self.parser = CommandParser()
        
    def execute(self, command: str) -> Dict[str, Any]:
        """명령어 실행"""
        try:
            # 매니저로 실행
            result = self.manager.execute_command(command)
            
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


def get_current_project_name() -> str:
    """현재 프로젝트 이름 가져오기"""
    # 1. 환경 변수에서 확인
    project_name = os.environ.get('CURRENT_PROJECT')
    if project_name:
        return project_name
    
    # 2. 현재 작업 디렉토리에서 추정
    cwd = os.getcwd()
    project_name = os.path.basename(cwd)
    
    # 3. 기본값
    if not project_name or project_name == 'Desktop':
        project_name = 'default'
    
    return project_name


def get_dispatcher() -> WorkflowDispatcher:
    """전역 디스패처 인스턴스 가져오기 - 프로젝트별로 관리"""
    global _dispatcher
    current_project = get_current_project_name()
    
    # 프로젝트가 변경되었으면 새 디스패처 생성
    if _dispatcher is None or _dispatcher.project_name != current_project:
        _dispatcher = WorkflowDispatcher(current_project)
    
    return _dispatcher


def execute_workflow_command(command: str) -> Dict[str, Any]:
    """워크플로우 명령어 실행 (공개 API)"""
    dispatcher = get_dispatcher()
    return dispatcher.execute(command)


def update_dispatcher_project(project_name: str) -> None:
    """디스패처의 프로젝트 업데이트"""
    global _dispatcher
    if _dispatcher is None or _dispatcher.project_name != project_name:
        _dispatcher = WorkflowDispatcher(project_name)
