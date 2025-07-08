"""
타임아웃 헬퍼 - 검색 함수에 타임아웃 기능 추가
"""
import concurrent.futures
from functools import wraps
from typing import Callable, Any


def with_timeout(timeout_seconds: float = 30.0):
    """함수에 타임아웃을 적용하는 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # timeout_ms 파라미터 확인
            timeout_ms = kwargs.get('timeout_ms', timeout_seconds * 1000)
            timeout_sec = timeout_ms / 1000
            
            # ThreadPoolExecutor로 타임아웃 적용
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, *args, **kwargs)
                try:
                    return future.result(timeout=timeout_sec)
                except concurrent.futures.TimeoutError:
                    future.cancel()
                    # HelperResult 형식으로 반환
                    try:
                        from ai_helpers.helper_result import HelperResult
                        return HelperResult.failure(f"작업 타임아웃 ({timeout_ms}ms)")
                    except ImportError:
                        return {"success": False, "error": f"작업 타임아웃 ({timeout_ms}ms)"}
                except Exception as e:
                    try:
                        from ai_helpers.helper_result import HelperResult
                        return HelperResult.failure(str(e))
                    except ImportError:
                        return {"success": False, "error": str(e)}
        return wrapper
    return decorator
