
"""
AI Helpers 표준화 래퍼
기존 함수를 수정하지 않고 표준 API 패턴 제공
"""
from typing import Dict, Any, List, Optional
from .core.fs import scan_directory as core_scan_directory, ScanOptions

# 표준 패턴: {ok: bool, data: Any, error?: str}


def ensure_response(data: Any, error: str = None, **extras) -> Dict[str, Any]:
    """모든 데이터를 표준 응답 형식으로 변환

    Args:
        data: 반환할 데이터
        error: 에러 메시지 (있는 경우)
        **extras: 추가 필드 (count, path 등)

    Returns:
        {'ok': bool, 'data': Any, 'error': str, ...}
    """
    if error:
        error_info = {'ok': False, 'error': error}
        # exception 객체가 전달된 경우 타입 정보 추가
        if 'exception' in extras:
            exc = extras.pop('exception')
            error_info['error_type'] = type(exc).__name__
        error_info.update(extras)
        return error_info
        
    if isinstance(data, dict) and 'ok' in data:
        # 이미 표준 응답이지만 extras가 있으면 병합
        if extras:
            data.update(extras)
        return data

    response = {'ok': True, 'data': data}
    response.update(extras)
    return response


def safe_execution(func):
    """함수 실행을 안전하게 래핑하는 데코레이터
    
    모든 예외를 자동으로 {'ok': False, 'error': ...} 형태로 변환합니다.
    """
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            # 이미 표준 응답인 경우 그대로 반환
            if isinstance(result, dict) and 'ok' in result:
                return result
            # 아니면 ensure_response로 래핑
            return ensure_response(result)
        except Exception as e:
            return ensure_response(
                None, 
                str(e), 
                exception=e,
                function=func.__name__,
                args=args[:3] if len(args) > 3 else args,  # 긴 인자는 처음 3개만
                kwargs=list(kwargs.keys())  # 키만 기록
            )
    return wrapper


def scan_directory(path: str = '.', 
                  max_depth: Optional[int] = None,
                  output: str = 'list') -> Dict[str, Any]:
    """
    통합 디렉토리 스캔

    Args:
        path: 스캔할 경로
        max_depth: 최대 깊이 (None = 전체)
        output: 'list' | 'dict' | 'tree'

    Returns:
        {'ok': True, 'data': [...], 'count': N, 'path': path}
    """
    try:
        if output == 'list':
            # 기존 방식 - core 사용
            options = ScanOptions(output="flat", max_depth=max_depth)
            result = core_scan_directory(path, options=options)
            if result["ok"]:
                return ensure_response(result["data"], count=len(result["data"]), path=path)
            else:
                return ensure_response(None, error=result.get("error", "Unknown error"), path=path)

        elif output == 'dict':
            # 동적 import로 순환 참조 방지
            from .project import scan_directory_dict as _scan_directory_dict
            # 기존 scan_directory_dict 활용
            data = _scan_directory_dict(path, max_depth or 5)
            return ensure_response(data, path=path)

        else:  # tree 등 추가 형식
            return ensure_response([], count=0, path=path)

    except Exception as e:
        return ensure_response(None, error=str(e), path=path)
def scan_directory_dict(path: str = '.', max_depth: int = 3) -> Dict[str, Any]:
    """DEPRECATED: Use scan_directory(path, output='dict') instead

    이 함수는 곧 제거될 예정입니다.
    scan_directory(path, max_depth=max_depth, output='dict')를 사용하세요.
    """
    import warnings
    warnings.warn(
        "scan_directory_dict is deprecated. Use scan_directory(output='dict')",
        DeprecationWarning,
        stacklevel=2
    )
    return scan_directory(path, max_depth=max_depth, output='dict')
def get_current_project() -> Dict[str, Any]:
    """현재 프로젝트 정보 반환 (안전 버전)

    Returns:
        {'ok': bool, 'data': dict} - 프로젝트 정보 또는 에러
    """
    try:
        # 동적 import로 순환 참조 방지
        from .project import get_current_project as _get_current_project
        project = _get_current_project()
        if not project:
            return ensure_response(None, error='No project selected')
        return ensure_response(project)
    except Exception as e:
        return ensure_response(None, error=str(e))
# 하위 호환성을 위한 별칭
safe_scan_directory = scan_directory
safe_scan_directory_dict = scan_directory_dict
safe_get_current_project = get_current_project
