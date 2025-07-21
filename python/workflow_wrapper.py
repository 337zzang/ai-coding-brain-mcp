"""Workflow wrapper for dict-based interface with optional Context integration"""

from ai_helpers_new import get_workflow_manager
from ai_helpers_new.context_workflow_manager import create_context_workflow_manager
import os

def wf(command: str, verbose: bool = False):
    """워크플로우 명령 실행 - dict 반환 (Context 지원)"""
    try:
        # WorkflowManager 인스턴스 가져오기
        base_manager = get_workflow_manager()

        # Context 시스템이 활성화되어 있으면 래핑
        if os.environ.get('CONTEXT_SYSTEM', 'off').lower() == 'on':
            manager = create_context_workflow_manager(base_manager)
        else:
            manager = base_manager

        # 명령 실행
        result = manager.wf_command(command)

        # dict 반환
        response = {
            'ok': True,
            'data': result,
            'type': 'workflow_command'
        }

        # verbose 모드에서는 출력도 함
        if verbose:
            print(result)

        return response

    except Exception as e:
        return {
            'ok': False,
            'error': str(e)
        }
