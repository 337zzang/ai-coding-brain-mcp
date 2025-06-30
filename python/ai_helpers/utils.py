"""유틸리티 함수들"""

from typing import List
from .decorators import track_operation


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
