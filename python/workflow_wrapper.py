
# workflow_wrapper.py - 간단한 래퍼
from ai_helpers_new import get_workflow_manager

def wf(command: str, verbose: bool = False):
    """워크플로우 명령 실행 - dict 반환"""
    try:
        # WorkflowManager 인스턴스 가져오기
        manager = get_workflow_manager()

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
