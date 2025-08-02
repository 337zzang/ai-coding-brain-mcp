"""
에러 컨텍스트 관리 클래스
에러 발생 시 상세한 컨텍스트 정보를 수집하고 관리

작성일: 2025-08-02
"""
import sys
import traceback
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import inspect
import functools


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

    @classmethod
    def classify(cls, error: Exception) -> Dict[str, str]:
        """에러를 분류하고 심각도를 반환"""
        error_type = type(error).__name__

        # 카테고리 찾기
        category = "UNKNOWN"
        for cat, types in cls.ERROR_CATEGORIES.items():
            if error_type in types:
                category = cat
                break

        # 심각도 결정
        severity = cls._determine_severity(category, error)

        return {
            "category": category,
            "severity": severity,
            "type": error_type
        }

    @classmethod
    def _determine_severity(cls, category: str, error: Exception) -> str:
        """에러 심각도 결정"""
        if category == "CRITICAL":
            return "CRITICAL"
        elif category == "CONFIGURATION":
            return "HIGH"
        elif category in ["INPUT", "RUNTIME"]:
            return "MEDIUM"
        elif category == "IO":
            # 네트워크 에러는 재시도 가능하므로 낮음
            if "Timeout" in type(error).__name__:
                return "LOW"
            return "MEDIUM"
        else:
            return "LOW"


def enhanced_safe_execute(
    func_name: str,
    impl_func: Callable,
    *args,
    instance_checker: Optional[Callable[[], bool]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    향상된 안전한 실행 함수 - 순환 참조 없음

    Args:
        func_name: 함수 이름
        impl_func: 실행할 함수
        instance_checker: 인스턴스 확인 함수 (옵션)
        *args, **kwargs: 함수 인자

    Returns:
        표준 응답 형식
    """
    context = ErrorContext(func_name, *args, **kwargs)

    try:
        # 인스턴스 확인 (콜백 방식)
        if instance_checker and not instance_checker():
            return {
                'ok': False,
                'error': 'web_start()를 먼저 실행하세요',
                '_context': {
                    'function': func_name,
                    'execution_time': context.get_execution_time()
                }
            }

        # 함수 실행
        result = impl_func(*args, **kwargs)

        # 결과 정규화
        if isinstance(result, dict) and 'ok' in result:
            return result
        else:
            return {'ok': True, 'data': result}

    except Exception as e:
        # 에러 분류
        classification = ErrorClassifier.classify(e)

        # 에러 정보 빌드
        error_info = context.build_error_info(e)
        error_info['classification'] = classification

        # 에러 응답
        return {
            'ok': False,
            'error': str(e),
            'error_type': type(e).__name__,
            'error_info': error_info
        }
