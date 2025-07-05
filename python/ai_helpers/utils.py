"""유틸리티 함수들"""

from typing import List
from ai_helpers.decorators import track_operation


@track_operation('utils', 'list_functions')
def list_functions(helpers_instance) -> List[str]:
    """사용 가능한 함수 목록 표시
    
    Args:
        helpers_instance: AIHelpers 인스턴스
    
    Returns:
        list: 사용 가능한 함수명 목록
    """
    funcs = [attr for attr in dir(helpers_instance)
             if not attr.startswith('_') and callable(getattr(helpers_instance, attr))]
    
    print(f"🔧 사용 가능한 헬퍼 함수 ({len(funcs)}개):")
    for func in sorted(funcs):
        print(f"  • helpers.{func}()")
    
    return funcs


def track_file_access(file_path: str, operation: str = 'access') -> None:
    """파일 접근 추적"""
    try:
        # WorkTracker가 있으면 사용
        from work_tracking import WorkTracker
        tracker = WorkTracker()
        if hasattr(tracker, 'track_file_access'):
            tracker.track_file_access(file_path, operation)
    except:
        # WorkTracker가 없거나 오류 시 무시
        pass

def _safe_import_parse_with_snippets():
    """parse_with_snippets를 안전하게 import"""
    try:
        from ai_helpers.code import parse_with_snippets
        return parse_with_snippets
    except ImportError:
        return None
