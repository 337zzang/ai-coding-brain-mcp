"""
웹 자동화 디버그 유틸리티
성능 프로파일링, 로깅, 디버깅 도구 모음

작성일: 2025-08-02
"""
import os
import time
import json
import functools
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime
from contextlib import contextmanager
from collections import defaultdict


class PerformanceProfiler:
    """함수 실행 성능 프로파일러"""

    def __init__(self):
        self.timings: Dict[str, List[float]] = defaultdict(list)
        self.call_counts: Dict[str, int] = defaultdict(int)

    def record(self, func_name: str, execution_time: float):
        """실행 시간 기록"""
        self.timings[func_name].append(execution_time)
        self.call_counts[func_name] += 1

    def get_stats(self, func_name: Optional[str] = None) -> Dict[str, Any]:
        """통계 반환"""
        if func_name:
            times = self.timings.get(func_name, [])
            if not times:
                return {"error": f"No data for {func_name}"}

            return {
                "function": func_name,
                "call_count": self.call_counts[func_name],
                "total_time": sum(times),
                "average_time": sum(times) / len(times),
                "min_time": min(times),
                "max_time": max(times)
            }
        else:
            # 전체 통계
            stats = {}
            for name in self.timings:
                stats[name] = self.get_stats(name)
            return stats

    def reset(self):
        """통계 초기화"""
        self.timings.clear()
        self.call_counts.clear()


class DebugLogger:
    """향상된 디버그 로거"""

    def __init__(self, log_file: Optional[str] = None):
        self.enabled = os.getenv('WEB_AUTOMATION_DEBUG', 'false').lower() == 'true'
        self.verbose = os.getenv('WEB_AUTOMATION_VERBOSE', 'false').lower() == 'true'
        self.log_file = log_file or f"web_automation_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')

    def log(self, level: str, message: str, data: Optional[Dict[str, Any]] = None):
        """로그 메시지 기록"""
        if not self.enabled:
            return

        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "session_id": self.session_id,
            "level": level,
            "message": message
        }

        if data:
            log_entry["data"] = data

        # 콘솔 출력 (verbose 모드)
        if self.verbose:
            print(f"[{level}] {timestamp} - {message}")
            if data:
                print(f"  Data: {json.dumps(data, indent=2)}")

        # 파일 기록
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except:
            pass  # 로깅 실패는 무시

    def debug(self, message: str, **kwargs):
        self.log("DEBUG", message, kwargs)

    def info(self, message: str, **kwargs):
        self.log("INFO", message, kwargs)

    def warning(self, message: str, **kwargs):
        self.log("WARNING", message, kwargs)

    def error(self, message: str, **kwargs):
        self.log("ERROR", message, kwargs)


# 전역 인스턴스
profiler = PerformanceProfiler()
debug_logger = DebugLogger()


def profile_performance(func_name: Optional[str] = None):
    """성능 프로파일링 데코레이터"""
    def decorator(func):
        nonlocal func_name
        if func_name is None:
            func_name = func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                # 성능 기록
                profiler.record(func_name, execution_time)

                # 디버그 로깅
                debug_logger.debug(
                    f"{func_name} executed",
                    execution_time=execution_time,
                    args_count=len(args),
                    kwargs_keys=list(kwargs.keys())
                )

                return result

            except Exception as e:
                execution_time = time.time() - start_time
                debug_logger.error(
                    f"{func_name} failed",
                    execution_time=execution_time,
                    error_type=type(e).__name__,
                    error_message=str(e)
                )
                raise

        return wrapper
    return decorator


@contextmanager
def debug_context(operation_name: str):
    """디버그 컨텍스트 매니저"""
    debug_logger.info(f"Starting {operation_name}")
    start_time = time.time()

    try:
        yield debug_logger
    except Exception as e:
        debug_logger.error(
            f"{operation_name} failed",
            error_type=type(e).__name__,
            error_message=str(e),
            execution_time=time.time() - start_time
        )
        raise
    else:
        debug_logger.info(
            f"Completed {operation_name}",
            execution_time=time.time() - start_time
        )


def dump_debug_info():
    """현재 디버그 정보 덤프"""
    info = {
        "timestamp": datetime.now().isoformat(),
        "debug_mode": debug_logger.enabled,
        "verbose_mode": debug_logger.verbose,
        "performance_stats": profiler.get_stats(),
        "log_file": debug_logger.log_file,
        "session_id": debug_logger.session_id
    }

    # 파일로 저장
    dump_file = f"debug_dump_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(dump_file, 'w') as f:
        json.dump(info, f, indent=2)

    return {
        "dump_file": dump_file,
        "info": info
    }


# 환경변수 기반 설정 헬퍼
class DebugConfig:
    """디버그 설정 관리"""

    @staticmethod
    def enable_debug():
        """디버그 모드 활성화"""
        os.environ['WEB_AUTOMATION_DEBUG'] = 'true'
        debug_logger.enabled = True

    @staticmethod
    def disable_debug():
        """디버그 모드 비활성화"""
        os.environ['WEB_AUTOMATION_DEBUG'] = 'false'
        debug_logger.enabled = False

    @staticmethod
    def enable_verbose():
        """상세 출력 모드 활성화"""
        os.environ['WEB_AUTOMATION_VERBOSE'] = 'true'
        debug_logger.verbose = True

    @staticmethod
    def disable_verbose():
        """상세 출력 모드 비활성화"""
        os.environ['WEB_AUTOMATION_VERBOSE'] = 'false'
        debug_logger.verbose = False

    @staticmethod
    def get_config() -> Dict[str, bool]:
        """현재 설정 반환"""
        return {
            "debug": debug_logger.enabled,
            "verbose": debug_logger.verbose
        }
