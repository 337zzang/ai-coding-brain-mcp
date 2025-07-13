"""
AI Helpers - Decorators Module
작업 추적 및 로깅을 위한 데코레이터들
"""

import functools
import time
from datetime import datetime
from typing import Callable, Any, Optional, Union

def track_operation(category: Optional[str] = None, operation: Optional[str] = None):
    """
    작업을 추적하는 데코레이터 팩토리

    사용법:
        @track_operation  # 매개변수 없음
        @track_operation()  # 빈 괄호
        @track_operation('code')  # 카테고리만
        @track_operation('code', 'parse')  # 카테고리와 작업명
        @track_operation(category='code', operation='parse')  # 키워드 매개변수

    Args:
        category: 작업 카테고리 (예: 'code', 'file', 'git')
        operation: 세부 작업명 (예: 'parse', 'replace', 'commit')
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            function_name = func.__name__

            # 작업 정보 구성
            operation_name = operation or function_name
            category_name = category or 'general'
            full_name = f"{category_name}.{operation_name}"

            try:
                # 함수 실행
                result = func(*args, **kwargs)

                # 실행 시간 계산
                execution_time = time.time() - start_time

                # 간단한 로깅 (필요시 활성화)
                if execution_time > 1.0:  # 1초 이상 걸린 작업만 로깅
                    print(f"🕒 {full_name} 실행 완료 ({execution_time:.3f}s)")

                return result

            except Exception as e:
                execution_time = time.time() - start_time
                # 에러 로깅 (필요시 활성화)
                # print(f"❌ {full_name} 실행 실패 ({execution_time:.3f}s): {e}")
                raise

        return wrapper

    # 데코레이터가 직접 함수에 적용된 경우 (@track_operation)
    if callable(category):
        func = category
        category = None
        operation = None
        return decorator(func)

    # 데코레이터 팩토리로 사용된 경우 (@track_operation(...))
    return decorator

def performance_monitor(threshold: float = 0.1):
    """
    성능 모니터링 데코레이터

    Args:
        threshold: 경고할 실행 시간 임계값 (초)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time

            if execution_time > threshold:
                print(f"⚠️ 성능 경고: {func.__name__} ({execution_time:.3f}s)")

            return result

        return wrapper

    return decorator

def error_handler(log_errors: bool = True, reraise: bool = True):
    """
    에러 처리 데코레이터

    Args:
        log_errors: 에러를 로깅할지 여부
        reraise: 에러를 다시 발생시킬지 여부
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    print(f"⚠️ {func.__name__}에서 오류 발생: {e}")

                if reraise:
                    raise
                else:
                    return None

        return wrapper

    return decorator

def retry(max_attempts: int = 3, delay: float = 0.1):
    """
    재시도 데코레이터

    Args:
        max_attempts: 최대 시도 횟수
        delay: 재시도 간 대기 시간 (초)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
                        continue
                    break

            # 모든 시도 실패
            if last_exception:
                raise last_exception

        return wrapper

    return decorator
