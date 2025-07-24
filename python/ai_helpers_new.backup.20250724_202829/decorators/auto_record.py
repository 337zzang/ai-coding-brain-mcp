"""
Context 자동 기록 데코레이터
o3 분석 기반으로 구현
"""
import functools
import inspect
import uuid
import os
import json
import time
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional, Callable

logger = logging.getLogger(__name__)

# 단일 스레드 실행자 (Context 기록 전용)
_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="context-recorder")


def _safe_serialize(obj: Any, max_len: int = 120) -> Any:
    """
    객체를 JSON 직렬화 가능한 형태로 안전하게 변환

    Args:
        obj: 직렬화할 객체
        max_len: 문자열 최대 길이

    Returns:
        JSON 직렬화 가능한 객체
    """
    try:
        json.dumps(obj)
        return obj
    except (TypeError, OverflowError):
        # 특수 타입 처리
        if hasattr(obj, '__dict__'):
            # 객체의 경우 타입 정보만
            return f"<{obj.__class__.__name__} object>"
        elif isinstance(obj, (list, tuple)):
            # 컬렉션은 길이 정보만
            return f"<{type(obj).__name__} len={len(obj)}>"
        elif isinstance(obj, dict):
            # 딕셔너리는 키 개수만
            return f"<dict keys={len(obj)}>"
        else:
            # 나머지는 문자열로 변환
            text = str(obj)
            return text if len(text) <= max_len else text[:max_len] + "..."


def _extract_params(func: Callable, args: tuple, kwargs: dict) -> Dict[str, Any]:
    """
    함수 시그니처를 기반으로 파라미터 추출

    Args:
        func: 대상 함수
        args: 위치 인자
        kwargs: 키워드 인자

    Returns:
        파라미터 딕셔너리
    """
    try:
        sig = inspect.signature(func)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()

        # self 제외하고 반환
        return {
            k: _safe_serialize(v) 
            for k, v in bound.arguments.items() 
            if k != 'self'
        }
    except Exception as e:
        logger.warning(f"Failed to extract params: {e}")
        return {"_error": "param extraction failed"}


def auto_record(
    action_type: Optional[str] = None,
    *,
    capture_params: bool = True,
    capture_result: bool = True,
    log_start: bool = False
) -> Callable:
    """
    메서드 호출을 Context에 자동으로 기록하는 데코레이터

    Args:
        action_type: 액션 타입 (기본값: 함수명)
        capture_params: 파라미터 캡처 여부
        capture_result: 결과 캡처 여부
        log_start: 시작 이벤트 기록 여부

    Returns:
        데코레이터 함수

    Example:
        @auto_record(capture_result=False)
        def create_flow(self, name: str):
            # 자동으로 create_flow_completed/failed 이벤트 기록
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # Fast-path: Context 시스템 비활성화 시
            if os.getenv("CONTEXT_OFF") == "1":
                return func(self, *args, **kwargs)

            # Context 객체 확인
            ctx = getattr(self, '_context', None)
            if ctx is None:
                return func(self, *args, **kwargs)

            # Context 활성화 여부 확인
            if not getattr(self, '_context_enabled', True):
                return func(self, *args, **kwargs)

            # 메타데이터 준비
            act = action_type or func.__name__
            call_id = str(uuid.uuid4())[:8]  # 짧은 ID

            # Flow ID 결정 (우선순위: kwargs > current_flow_id > 'system')
            flow_id = kwargs.get('flow_id')
            if not flow_id:
                flow_id = getattr(self, '_current_flow_id', None)
            if not flow_id:
                flow_id = 'system'

            # 파라미터 캡처
            params = {}
            if capture_params:
                params = _extract_params(func, (self,) + args, kwargs)

            # 비동기 기록 함수
            def _async_record(event_type: str, extra: Optional[Dict] = None):
                try:
                    details = {
                        "call_id": call_id,
                        "source": "auto",
                        "method": func.__name__,
                        "module": func.__module__,
                        **(extra or {})
                    }

                    # 백그라운드에서 Context 기록
                    future = _EXECUTOR.submit(
                        ctx.record_flow_action,
                        flow_id,
                        event_type,
                        details
                    )

                    # Fire and forget - 결과를 기다리지 않음

                except Exception as e:
                    # Context 기록 실패는 로그만 남기고 무시
                    logger.warning(f"Failed to record context: {e}")

            # 실행 시간 측정 시작
            start_time = time.perf_counter()

            try:
                # 시작 이벤트 (선택적)
                if log_start:
                    _async_record(f"{act}_started", {"params": params})

                # 실제 함수 실행
                result = func(self, *args, **kwargs)

                # 실행 시간 계산
                elapsed = time.perf_counter() - start_time

                # 완료 이벤트
                extra = {
                    "elapsed_ms": round(elapsed * 1000, 2),
                    "params": params if not log_start else None  # 중복 방지
                }

                if capture_result:
                    extra["result"] = _safe_serialize(result)

                _async_record(f"{act}_completed", extra)

                return result

            except Exception as e:
                # 실행 시간 계산
                elapsed = time.perf_counter() - start_time

                # 실패 이벤트
                _async_record(f"{act}_failed", {
                    "elapsed_ms": round(elapsed * 1000, 2),
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "params": params if not log_start else None
                })

                # 원본 예외를 그대로 전파
                raise

        return wrapper
    return decorator


# 종료 시 executor 정리
import atexit
atexit.register(lambda: _EXECUTOR.shutdown(wait=True))
