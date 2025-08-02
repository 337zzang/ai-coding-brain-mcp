"""
웹 자동화 에러 처리 모듈
안전한 실행과 에러 처리를 위한 유틸리티

작성일: 2025-01-27
수정일: 2025-08-02 (Phase 1 - 순환 참조 제거)
"""

from typing import Dict, Any, Optional, List, Callable
import inspect
import functools
import os
import sys
import logging
import traceback
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from functools import wraps

# 새로운 ErrorContext import

# 디버그 모드 설정
DEBUG_MODE = os.getenv('WEB_AUTOMATION_DEBUG', 'false').lower() == 'true'

# 로거 설정
logger = logging.getLogger('web_automation')
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)

# 로그 파일 추가 (디버그 모드에서만)
if DEBUG_MODE:
    from datetime import datetime
    log_filename = f"web_automation_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def safe_execute(func_name: str, 
                impl_func: Callable,
                *args, 
                check_instance: bool = True,
                instance_checker: Optional[Callable[[], bool]] = None,
                **kwargs) -> Dict[str, Any]:
    """
    웹 자동화 함수의 안전한 실행을 위한 래퍼 (리팩토링됨)

    순환 참조를 피하기 위해 instance_checker를 주입받음

    Args:
        func_name: 함수 이름 (로깅/디버깅용)
        impl_func: 실제 실행할 함수
        *args: 함수 인자
        check_instance: 인스턴스 체크 여부
        instance_checker: 인스턴스 확인 함수 (주입)
        **kwargs: 함수 키워드 인자

    Returns:
        표준 응답 형식 {'ok': bool, 'error/data': ...}
    """
    # 새로운 enhanced_safe_execute 사용
    if check_instance and instance_checker:
        return enhanced_safe_execute(
            func_name, 
            impl_func, 
            *args,
            instance_checker=instance_checker,
            **kwargs
        )
    else:
        return enhanced_safe_execute(
            func_name,
            impl_func,
            *args,
            **kwargs
        )


def with_error_handling(func_name: str = None, check_instance: bool = True):
    """
    데코레이터 방식의 에러 처리 (개선됨)

    Usage:
        @with_error_handling("my_function")
        def my_function(arg1, arg2):
            return do_something()
    """
    def decorator(func):
        nonlocal func_name
        if func_name is None:
            func_name = func.__name__

        @wraps(func)
        def wrapper(*args, **kwargs):
            # 인스턴스 체커는 래퍼 함수에서 주입받아야 함
            instance_checker = kwargs.pop('_instance_checker', None)

            return safe_execute(
                func_name,
                func,
                *args,
                check_instance=check_instance,
                instance_checker=instance_checker,
                **kwargs
            )
        return wrapper
    return decorator


# 에러 통계 수집 (선택적)
class ErrorStats:
    """에러 통계 수집 클래스"""

    def __init__(self):
        self.errors: Dict[str, int] = {}
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0

    def record_call(self, success: bool, error_type: Optional[str] = None):
        """호출 기록"""
        self.total_calls += 1
        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
            if error_type:
                self.errors[error_type] = self.errors.get(error_type, 0) + 1

    def get_stats(self) -> Dict[str, Any]:
        """통계 반환"""
        return {
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "success_rate": self.successful_calls / self.total_calls if self.total_calls > 0 else 0,
            "error_breakdown": self.errors
        }


# 전역 에러 통계 (옵션)
error_stats = ErrorStats() if DEBUG_MODE else None


# 기존 코드와의 호환성을 위한 별칭


# 디버그 유틸리티
def print_debug_info(info: Dict[str, Any]):
    """디버그 정보 출력"""
    if DEBUG_MODE:
        print("\n" + "="*60)
        print("DEBUG INFO")
        print("="*60)
        for key, value in info.items():
            print(f"{key}: {value}")
        print("="*60 + "\n")

# ========== web_automation_error_context.py에서 이동된 클래스들 ==========

class ErrorContext:
    """에러 발생 시 컨텍스트 정보를 수집하고 관리하는 클래스"""

    def __init__(self, function_name: str, *args, **kwargs):
        self.function_name = function_name
        self.args = args
        self.kwargs = kwargs
        self.start_time = datetime.now()
        self.metadata: Dict[str, Any] = {}

    def add_metadata(self, key: str, value: Any) -> None:
        """추가 메타데이터 저장"""
        self.metadata[key] = value

    def get_execution_time(self) -> float:
        """실행 시간 계산 (초)"""
        return (datetime.now() - self.start_time).total_seconds()

    def build_error_info(self, error: Exception) -> Dict[str, Any]:
        """에러 정보를 포함한 전체 컨텍스트 빌드"""
        # 스택 트레이스 정보
        exc_type, exc_value, exc_traceback = sys.exc_info()
        stack_frames = traceback.extract_tb(exc_traceback)

        # 호출 스택 정보 추출
        call_stack = []
        for frame in stack_frames:
            call_stack.append({
                "file": frame.filename,
                "line": frame.lineno,
                "function": frame.name,
                "code": frame.line
            })

        return {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "function": self.function_name,
            "execution_time": self.get_execution_time(),
            "timestamp": datetime.now().isoformat(),
            "context": {
                "args": self._serialize_args(self.args),
                "kwargs": self._serialize_kwargs(self.kwargs),
                "metadata": self.metadata
            },
            "stack_trace": {
                "formatted": traceback.format_exc(),
                "frames": call_stack
            }
        }

    def _serialize_args(self, args) -> List[str]:
        """인자를 안전하게 문자열로 변환"""
        serialized = []
        for arg in args:
            try:
                serialized.append(repr(arg))
            except:
                serialized.append(f"<{type(arg).__name__} object>")
        return serialized

    def _serialize_kwargs(self, kwargs) -> Dict[str, str]:
        """키워드 인자를 안전하게 문자열로 변환"""
        serialized = {}
        for key, value in kwargs.items():
            try:
                serialized[key] = repr(value)
            except:
                serialized[key] = f"<{type(value).__name__} object>"
        return serialized


class ErrorClassifier:
    """에러를 분류하고 심각도를 판단하는 클래스"""

    # 에러 분류 체계
    ERROR_CATEGORIES = {
        # 치명적 오류
        "CRITICAL": [
            "SystemError", "MemoryError", "RecursionError"
        ],
        # 설정 오류
        "CONFIGURATION": [
            "ImportError", "ModuleNotFoundError", "AttributeError"
        ],
        # 입력 오류
        "INPUT": [
            "ValueError", "TypeError", "KeyError", "IndexError"
        ],
        # 네트워크/IO 오류
        "IO": [
            "IOError", "FileNotFoundError", "PermissionError",
            "ConnectionError", "TimeoutError"
        ],
        # 런타임 오류
        "RUNTIME": [
            "RuntimeError", "NotImplementedError", "AssertionError"
        ]
    }

    @
