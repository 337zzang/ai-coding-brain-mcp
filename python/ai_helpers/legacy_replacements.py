"""
Legacy replacement functions - 점진적 폐기 예정
이 모듈의 함수들은 더 이상 사용하지 않는 것을 권장합니다.
"""
import warnings

def cmd_flow(*args, **kwargs):
    """Deprecated: flow_project 명령을 사용하세요"""
    warnings.warn(
        "cmd_flow()는 폐기될 예정입니다. 대신 flow_project 명령을 사용하세요.",
        DeprecationWarning,
        stacklevel=2
    )
    # enhanced_flow의 cmd_flow_with_context 호출 시도
    try:
        import sys
        sys.path.insert(0, 'python')
        from enhanced_flow import cmd_flow_with_context
        if args and len(args) > 0:
            return cmd_flow_with_context(args[0])
        return {"success": False, "error": "프로젝트 이름이 필요합니다"}
    except ImportError:
        return {"success": False, "error": "enhanced_flow 모듈을 찾을 수 없습니다"}

def track_function_edit(*args, **kwargs):
    """Deprecated: 작업 추적은 WorkTracker를 사용하세요"""
    warnings.warn(
        "track_function_edit()는 폐기될 예정입니다. WorkTracker를 사용하세요.",
        DeprecationWarning,
        stacklevel=2
    )
    return None

def get_work_tracking_summary(*args, **kwargs):
    """Deprecated: 작업 추적은 WorkTracker를 사용하세요"""
    warnings.warn(
        "get_work_tracking_summary()는 폐기될 예정입니다.",
        DeprecationWarning,
        stacklevel=2
    )
    return {}

# track_file_access는 file 모듈에서 import
from .file import track_file_access

__all__ = ['cmd_flow', 'track_file_access', 'track_function_edit', 'get_work_tracking_summary']
