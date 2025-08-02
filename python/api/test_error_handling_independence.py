"""
에러 처리 독립성 테스트
Phase 1 Task 3 검증

작성일: 2025-08-02
"""
import pytest
import os
from unittest.mock import Mock, patch
from python.api.web_automation_error_context import ErrorContext, ErrorClassifier
from python.api.web_automation_errors import safe_execute, ErrorStats
from python.api.web_automation_debug_utils import PerformanceProfiler, DebugLogger, profile_performance


class TestErrorContext:
    """ErrorContext 클래스 테스트"""

    def test_error_context_creation(self):
        """ErrorContext 생성 테스트"""
        context = ErrorContext("test_function", "arg1", "arg2", kwarg1="value1")

        assert context.function_name == "test_function"
        assert context.args == ("arg1", "arg2")
        assert context.kwargs == {"kwarg1": "value1"}
        assert context.start_time is not None

    def test_error_info_building(self):
        """에러 정보 빌드 테스트"""
        context = ErrorContext("test_function", 123, [1, 2, 3])
        context.add_metadata("retry_count", 3)

        try:
            raise ValueError("Test error")
        except ValueError as e:
            error_info = context.build_error_info(e)

        assert error_info["error_type"] == "ValueError"
        assert error_info["error_message"] == "Test error"
        assert error_info["function"] == "test_function"
        assert "execution_time" in error_info
        assert error_info["context"]["metadata"]["retry_count"] == 3
        assert len(error_info["stack_trace"]["frames"]) > 0

    def test_argument_serialization(self):
        """인자 직렬화 테스트"""
        # 직렬화 불가능한 객체
        class UnserializableObject:
            pass

        obj = UnserializableObject()
        context = ErrorContext("test", obj, normal_arg="value")

        try:
            raise Exception("Test")
        except Exception as e:
            error_info = context.build_error_info(e)

        # 직렬화 불가능한 객체도 안전하게 처리
        assert "<UnserializableObject object>" in error_info["context"]["args"]
        assert error_info["context"]["kwargs"]["normal_arg"] == "'value'"


class TestErrorClassifier:
    """ErrorClassifier 테스트"""

    def test_error_classification(self):
        """에러 분류 테스트"""
        # CRITICAL
        error = MemoryError("Out of memory")
        classification = ErrorClassifier.classify(error)
        assert classification["category"] == "CRITICAL"
        assert classification["severity"] == "CRITICAL"

        # CONFIGURATION
        error = ImportError("Module not found")
        classification = ErrorClassifier.classify(error)
        assert classification["category"] == "CONFIGURATION"
        assert classification["severity"] == "HIGH"

        # INPUT
        error = ValueError("Invalid value")
        classification = ErrorClassifier.classify(error)
        assert classification["category"] == "INPUT"
        assert classification["severity"] == "MEDIUM"

        # IO with Timeout
        error = TimeoutError("Connection timeout")
        classification = ErrorClassifier.classify(error)
        assert classification["category"] == "IO"
        assert classification["severity"] == "LOW"

        # UNKNOWN
        class CustomError(Exception):
            pass

        error = CustomError("Custom error")
        classification = ErrorClassifier.classify(error)
        assert classification["category"] == "UNKNOWN"
        assert classification["severity"] == "LOW"


class TestSafeExecute:
    """safe_execute 함수 테스트"""

    def test_safe_execute_without_instance_check(self):
        """인스턴스 체크 없이 실행"""
        def test_func(x, y):
            return x + y

        result = safe_execute("test_func", test_func, 1, 2, check_instance=False)

        assert result["ok"] is True
        assert result["data"] == 3

    def test_safe_execute_with_instance_checker(self):
        """인스턴스 체커 주입 테스트"""
        def test_func():
            return "success"

        # 인스턴스가 없는 경우
        result = safe_execute(
            "test_func", 
            test_func,
            check_instance=True,
            instance_checker=lambda: False
        )

        assert result["ok"] is False
        assert "web_start()" in result["error"]

        # 인스턴스가 있는 경우
        result = safe_execute(
            "test_func",
            test_func,
            check_instance=True,
            instance_checker=lambda: True
        )

        assert result["ok"] is True
        assert result["data"] == "success"

    def test_safe_execute_error_handling(self):
        """에러 처리 테스트"""
        def failing_func():
            raise ValueError("Test error")

        result = safe_execute("failing_func", failing_func, check_instance=False)

        assert result["ok"] is False
        assert result["error"] == "Test error"
        assert result["error_type"] == "ValueError"
        assert "error_info" in result
        assert result["error_info"]["classification"]["category"] == "INPUT"


class TestDebugUtilities:
    """디버그 유틸리티 테스트"""

    def test_performance_profiler(self):
        """성능 프로파일러 테스트"""
        profiler = PerformanceProfiler()

        # 실행 시간 기록
        profiler.record("func1", 0.1)
        profiler.record("func1", 0.2)
        profiler.record("func2", 0.5)

        # 통계 확인
        stats = profiler.get_stats("func1")
        assert stats["call_count"] == 2
        assert stats["total_time"] == 0.3
        assert stats["average_time"] == 0.15
        assert stats["min_time"] == 0.1
        assert stats["max_time"] == 0.2

        # 전체 통계
        all_stats = profiler.get_stats()
        assert "func1" in all_stats
        assert "func2" in all_stats

    def test_profile_performance_decorator(self):
        """성능 프로파일링 데코레이터 테스트"""
        from python.api.web_automation_debug_utils import profile_performance, profiler

        profiler.reset()

        @profile_performance("test_decorated_func")
        def test_func(x):
            return x * 2

        # 함수 실행
        result = test_func(5)
        assert result == 10

        # 프로파일링 확인
        stats = profiler.get_stats("test_decorated_func")
        assert stats["call_count"] == 1
        assert stats["total_time"] > 0

    def test_debug_logger(self):
        """디버그 로거 테스트"""
        # 임시 로그 파일
        test_log_file = "test_debug.log"
        logger = DebugLogger(test_log_file)
        logger.enabled = True  # 강제 활성화

        # 로그 메시지
        logger.debug("Debug message", key="value")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message", error_code=500)

        # 로그 파일 확인
        assert os.path.exists(test_log_file)

        # 정리
        os.remove(test_log_file)


class TestCircularReferenceRemoval:
    """순환 참조 제거 확인 테스트"""

    def test_no_circular_import(self):
        """순환 import가 없는지 확인"""
        # web_automation_errors가 web_automation_helpers를 import하지 않음
        import python.api.web_automation_errors as errors_module

        # 모듈의 import 확인
        assert not hasattr(errors_module, 'web_automation_helpers')

        # safe_execute가 instance_checker를 매개변수로 받음
        import inspect
        sig = inspect.signature(errors_module.safe_execute)
        assert 'instance_checker' in sig.parameters


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
