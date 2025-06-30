"""명령어 관련 함수들"""

from typing import Any, Optional
from .decorators import track_operation, lazy_import


@track_operation('command', 'plan')
def cmd_plan(*args, **kwargs) -> Optional[Any]:
    """plan 명령 실행
    
    계획 수립 명령을 실행합니다.
    
    Returns:
        Any: 명령 실행 결과
    """
    try:
        from commands.plan import cmd_plan as plan_func
        return plan_func(*args, **kwargs)
    except Exception as e:
        print(f"⚠️ cmd_plan 오류: {e}")
        return None


@track_operation('command', 'task')
def cmd_task(*args, **kwargs) -> Optional[Any]:
    """task 명령 실행
    
    작업 관리 명령을 실행합니다.
    
    Returns:
        Any: 명령 실행 결과
    """
    try:
        from commands.task import cmd_task as task_func
        return task_func(*args, **kwargs)
    except Exception as e:
        print(f"⚠️ cmd_task 오류: {e}")
        return None


@track_operation('command', 'next')
def cmd_next(*args, **kwargs) -> Optional[Any]:
    """next 명령 실행
    
    다음 작업으로 진행하는 명령을 실행합니다.
    
    Returns:
        Any: 명령 실행 결과
    """
    try:
        from commands.next import cmd_next as next_func
        return next_func(*args, **kwargs)
    except Exception as e:
        print(f"⚠️ cmd_next 오류: {e}")
        return None


# 지연 로딩 함수들 (claude_code_ai_brain에서)
cmd_flow = lazy_import('claude_code_ai_brain', 'cmd_flow')
track_file_access = lazy_import('claude_code_ai_brain', 'track_file_access')
track_function_edit = lazy_import('claude_code_ai_brain', 'track_function_edit')
get_work_tracking_summary = lazy_import('claude_code_ai_brain', 'get_work_tracking_summary')
