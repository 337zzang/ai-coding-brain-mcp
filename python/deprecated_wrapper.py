"""
Deprecated 함수들을 위한 래퍼
"""
import warnings
from typing import Any, Callable
import functools

def deprecated(alternative: str = None):
    """함수를 deprecated로 표시하는 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            message = f"{func.__name__}는 deprecated되었습니다."
            if alternative:
                message += f" 대신 {alternative}를 사용하세요."
            warnings.warn(message, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Deprecated 함수들을 대체 함수로 리다이렉트
def search_in_files(*args, **kwargs):
    """Deprecated: search_code를 사용하세요"""
    warnings.warn("search_in_files는 deprecated되었습니다. search_code를 사용하세요.", DeprecationWarning)
    # helpers.search_code로 리다이렉트
    from . import helpers
    return helpers.search_code(*args, **kwargs)

def flow_project(project_name: str):
    """Deprecated: fp()를 사용하세요"""
    warnings.warn("flow_project는 deprecated되었습니다. fp()를 사용하세요.", DeprecationWarning)
    # fp 함수로 리다이렉트
    import sys
    if 'fp' in sys.modules['__main__'].__dict__:
        return sys.modules['__main__'].__dict__['fp'](project_name)
    else:
        raise RuntimeError("fp() 함수를 찾을 수 없습니다")

def ez_parse(filepath: str):
    """Deprecated: parse_file을 사용하세요"""
    warnings.warn("ez_parse는 deprecated되었습니다. parse_file을 사용하세요.", DeprecationWarning)
    from . import helpers
    return helpers.parse_file(filepath)

def explain_error(error_msg: str, context: str = None):
    """Deprecated: ask_o3를 사용하세요"""
    warnings.warn("explain_error는 deprecated되었습니다. ask_o3를 사용하세요.", DeprecationWarning)
    from . import helpers
    prompt = f"다음 에러를 설명해주세요: {error_msg}"
    if context:
        prompt += f"\n컨텍스트: {context}"
    return helpers.ask_o3(prompt)

def generate_docstring(code: str):
    """Deprecated: ask_o3를 사용하세요"""
    warnings.warn("generate_docstring는 deprecated되었습니다. ask_o3를 사용하세요.", DeprecationWarning)
    from . import helpers
    return helpers.ask_o3(f"다음 코드에 대한 docstring을 생성해주세요:\n{code}")
