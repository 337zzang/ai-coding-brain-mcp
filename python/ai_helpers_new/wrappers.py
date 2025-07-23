
"""
AI Helpers 표준화 래퍼
기존 함수를 수정하지 않고 표준 API 패턴 제공
"""
from typing import Dict, Any, List, Optional
import ai_helpers_new as h

# 표준 패턴: {ok: bool, data: Any, error?: str}

def scan_directory(path: str = '.') -> Dict[str, Any]:
    """scan_directory의 표준화 래퍼"""
    try:
        result = h.scan_directory(path)
        return {
            'ok': True,
            'data': result,
            'count': len(result) if isinstance(result, list) else 0,
            'path': path
        }
    except Exception as e:
        return {
            'ok': False,
            'error': str(e),
            'path': path
        }

def scan_directory_dict(path: str = '.', max_depth: int = 3) -> Dict[str, Any]:
    """scan_directory_dict의 표준화 래퍼"""
    try:
        result = h.scan_directory_dict(path, max_depth)
        return {
            'ok': True,
            'data': result,
            'path': path,
            'max_depth': max_depth
        }
    except Exception as e:
        return {
            'ok': False,
            'error': str(e),
            'path': path
        }

def get_current_project() -> Dict[str, Any]:
    """get_current_project의 표준화 래퍼"""
    try:
        # 이미 표준 형식으로 반환하므로 그대로 전달
        return h.get_current_project()
    except Exception as e:
        return {
            'ok': False,
            'error': str(e)
        }

# 하위 호환성을 위한 별칭
safe_scan_directory = scan_directory
safe_scan_directory_dict = scan_directory_dict
safe_get_current_project = get_current_project
