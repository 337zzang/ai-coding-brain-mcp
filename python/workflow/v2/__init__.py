"""Workflow V2 - 통합 명령어 시스템"""

from .dispatcher import WorkflowDispatcher
from .handlers import *

# 외부에서 사용할 주요 함수
def execute_workflow_command(command: str):
    """워크플로우 명령어 실행 - 통합 인터페이스"""
    dispatcher = WorkflowDispatcher()
    return dispatcher.execute(command)

# 하위 호환성을 위한 export
__all__ = [
    'WorkflowDispatcher',
    'execute_workflow_command',
    # handlers
    'workflow_start',
    'workflow_focus', 
    'workflow_plan',
    'workflow_task',
    'workflow_next',
    'workflow_build',
    'workflow_status',
]
