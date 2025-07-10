"""
로깅 데코레이터 - 함수 호출을 자동으로 로깅
"""
import functools
import time
import traceback
from typing import Any, Callable, Optional

# LogLevel과 LogCategory를 직접 정의 (import 문제 회피)
class LogLevel:
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory:
    SYSTEM = "system"
    WORKFLOW = "workflow"
    GIT = "git"
    FILE = "file"
    COMMAND = "command"
    ERROR = "error"

# 전역 로거
_logger = None

def get_decorator_logger():
    """데코레이터용 로거 싱글톤"""
    global _logger
    if _logger is None:
        from python.workflow_logging.logger import get_logger
        _logger = get_logger()
    return _logger

class LogConfig:
    """로깅 설정"""
    enabled = True
    log_args = True
    log_result = True
    log_time = True
    max_str_length = 200

def truncate_str(obj: Any, max_length: int = 200) -> str:
    """긴 문자열을 적절히 자르기"""
    s = str(obj)
    if len(s) > max_length:
        return s[:max_length] + "..."
    return s

def log_call(category: str = "system", level: str = "INFO", custom_message: Optional[str] = None):
    """함수 호출을 자동으로 로깅하는 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not LogConfig.enabled:
                return func(*args, **kwargs)

            logger = get_decorator_logger()
            func_name = func.__name__

            # 시작 로그
            start_time = time.time()
            details = {"function": func_name}

            # 인자 로깅
            if LogConfig.log_args:
                filtered_args = args[1:] if args and hasattr(args[0], '__class__') else args
                if filtered_args:
                    details["args"] = [truncate_str(arg) for arg in filtered_args]
                if kwargs:
                    details["kwargs"] = {k: truncate_str(v) for k, v in kwargs.items()}

            # 함수 시작 로그
            start_message = custom_message or f"{func_name} 호출"
            logger.debug(start_message, category=category, **details)

            try:
                # 함수 실행
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                # 성공 로그
                success_details = {"function": func_name}
                if LogConfig.log_time:
                    success_details["execution_time"] = f"{execution_time:.3f}s"

                if LogConfig.log_result and hasattr(result, 'ok'):
                    success_details["success"] = result.ok
                    if not result.ok and hasattr(result, 'error'):
                        success_details["error"] = result.error

                complete_message = f"{func_name} 완료"
                if level == "INFO":
                    logger.info(complete_message, category=category, **success_details)

                return result

            except Exception as e:
                execution_time = time.time() - start_time
                error_details = {
                    "function": func_name,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "execution_time": f"{execution_time:.3f}s"
                }

                error_message = f"{func_name} 실패"
                logger.error(error_message, category=category, **error_details)
                raise

        return wrapper
    return decorator

# 카테고리별 특화 데코레이터
def log_workflow(custom_message: Optional[str] = None):
    """워크플로우 작업 로깅"""
    return log_call("workflow", "INFO", custom_message)

def log_git(custom_message: Optional[str] = None):
    """Git 작업 로깅"""
    return log_call("git", "INFO", custom_message)

def log_file(custom_message: Optional[str] = None):
    """파일 작업 로깅"""
    return log_call("file", "INFO", custom_message)

def log_command(custom_message: Optional[str] = None):
    """명령 실행 로깅"""
    return log_call("command", "INFO", custom_message)

def log_system(custom_message: Optional[str] = None):
    """시스템 작업 로깅"""
    return log_call("system", "INFO", custom_message)
