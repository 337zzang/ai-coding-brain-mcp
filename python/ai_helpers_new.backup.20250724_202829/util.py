"""
AI Helpers Utility Module
단순하고 일관된 결과 반환을 위한 유틸리티
"""
from typing import Any, Dict

def ok(data: Any = None, **meta) -> Dict[str, Any]:
    """성공 결과를 반환

    Args:
        data: 실제 결과 데이터
        **meta: 추가 메타데이터 (path, lines, size 등)

    Returns:
        {'ok': True, 'data': data, ...meta}
    """
    return {'ok': True, 'data': data, **meta}


def err(msg: str, **meta) -> Dict[str, Any]:
    """실패 결과를 반환

    Args:
        msg: 에러 메시지
        **meta: 추가 컨텍스트 정보

    Returns:
        {'ok': False, 'error': msg, ...meta}
    """
    return {'ok': False, 'error': msg, **meta}


# 자주 사용하는 유틸리티
def is_ok(result: Dict[str, Any]) -> bool:
    """결과가 성공인지 확인"""
    return result.get('ok', False)


def get_data(result: Dict[str, Any], default=None):
    """성공 시 데이터 추출, 실패 시 default 반환"""
    if is_ok(result):
        return result.get('data', default)
    return default


def get_error(result: Dict[str, Any]) -> str:
    """에러 메시지 추출"""
    return result.get('error', '')
