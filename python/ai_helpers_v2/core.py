"""
AI Helpers V2 - 핵심 프로토콜 시스템
간단하고 강력한 실행 추적 및 캐싱
"""
import time
from enum import Enum
import json
from typing import Any, Callable, Dict, List, Optional
from functools import wraps
from pathlib import Path

# 캐싱에서 제외할 함수 목록
NO_CACHE_FUNCTIONS = [
    'replace_block',
    'create_file',
    'write_file',
    'append_to_file',
    'git_add',
    'git_commit',
    'git_push',
    'delete_file',
    'move_file',
    'copy_file'
]
class ExecutionProtocol:
    """실행 추적 프로토콜"""

    def __init__(self):
        self.executions = []
        self.cache = {}
        self.enabled = True

    def track(self, func_name: str, args: tuple, kwargs: dict, result: Any, duration: float):
        """실행 추적"""
        if not self.enabled:
            return

        execution = {
            'id': f"{func_name}_{int(time.time() * 1000)}",
            'function': func_name,
            'timestamp': time.time(),
            'duration': duration,
            'args': str(args)[:100],  # 너무 길면 자르기
            'success': result is not None
        }
        self.executions.append(execution)

        # 최대 1000개만 유지
        if len(self.executions) > 1000:
            self.executions = self.executions[-1000:]

    def get_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """캐시 키 생성"""
        return f"{func_name}:{str(args)}:{str(sorted(kwargs.items()))}"

    def get_cached(self, cache_key: str) -> Optional[Any]:
        """캐시에서 가져오기"""
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            # 5분 캐시
            if time.time() - entry['timestamp'] < 300:
                return entry['result']
        return None

    def set_cache(self, cache_key: str, result: Any):
        """캐시에 저장"""
        self.cache[cache_key] = {
            'result': result,
            'timestamp': time.time()
        }

        # 최대 100개만 유지
        if len(self.cache) > 100:
            # 가장 오래된 것부터 제거
            oldest = sorted(self.cache.items(), key=lambda x: x[1]['timestamp'])[:50]
            for key, _ in oldest:
                del self.cache[key]

# 전역 프로토콜 인스턴스
protocol = ExecutionProtocol()

def track_execution(func: Callable) -> Callable:
    """실행 추적 데코레이터 - 캐싱 개선 버전"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        start_time = time.time()

        # 파일 수정 작업은 캐싱하지 않음
        if func_name in NO_CACHE_FUNCTIONS:
            try:
                # 실제 함수 실행
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # 명시적 메시지 출력 (주요 파일 작업만)
                if func_name in ['create_file', 'write_file', 'replace_block', 'append_to_file']:
                    print(f"🔄 {func_name}: 캐싱 없이 실행 (파일 작업)")

                protocol.track(func_name, args, kwargs, result, duration)
                return result

            except Exception as e:
                duration = time.time() - start_time
                protocol.track(func_name, args, kwargs, None, duration)
                raise

        # 캐시 확인 (파일 작업이 아닌 경우만)
        cache_key = protocol.get_cache_key(func_name, args, kwargs)
        cached_result = protocol.get_cached(cache_key)

        if cached_result is not None:
            print(f"📦 {func_name}: 캐시된 결과 사용")
            protocol.track(func_name, args, kwargs, cached_result, 0.0)
            return cached_result

        # 실제 실행
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            # 캐시 저장 (빠른 작업만)
            if duration < 1.0:  # 1초 미만인 경우만
                protocol.set_cache(cache_key, result)
                if func_name not in ['read_file', 'scan_directory', 'search_files']:  # 너무 자주 호출되는 것 제외
                    print(f"💾 {func_name}: 결과 캐싱됨 ({duration:.3f}초)")

            protocol.track(func_name, args, kwargs, result, duration)
            return result

        except Exception as e:
            duration = time.time() - start_time
            protocol.track(func_name, args, kwargs, None, duration)
            raise

    return wrapper

def get_metrics() -> Dict[str, Any]:
    """실행 메트릭 조회"""
    if not protocol.executions:
        return {
            'total_executions': 0,
            'cache_size': 0,
            'success_rate': 0
        }

    total = len(protocol.executions)
    successful = sum(1 for e in protocol.executions if e['success'])
    total_duration = sum(e['duration'] for e in protocol.executions)

    return {
        'total_executions': total,
        'cache_size': len(protocol.cache),
        'success_rate': successful / total if total > 0 else 0,
        'average_duration': total_duration / total if total > 0 else 0,
        'cache_hit_rate': sum(1 for e in protocol.executions if e['duration'] == 0.0) / total if total > 0 else 0
    }

def clear_cache():
    """캐시 초기화"""
    protocol.cache.clear()

def get_execution_history(limit: int = 10) -> List[Dict[str, Any]]:
    """실행 히스토리 조회"""
    return protocol.executions[-limit:]


# ============================================================================
# Error Handling System (from error_handler.py)
# ============================================================================

from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, TypeVar, Generic



T = TypeVar('T')

class ErrorCategory(Enum):
    """에러 카테고리 분류"""
    FILE_SYSTEM = "file_system"
    NETWORK = "network"
    PERMISSION = "permission"
    VALIDATION = "validation"
    RUNTIME = "runtime"
    UNKNOWN = "unknown"

class ErrorSeverity(Enum):
    """에러 심각도"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class RetryPolicy:
    """재시도 정책"""
    max_attempts: int = 3
    delay: float = 1.0
    backoff_factor: float = 2.0
    max_delay: float = 60.0

@track_execution
def with_retry(func: Callable[..., T], policy: RetryPolicy = None) -> T:
    """재시도 기능이 있는 함수 실행"""
    if policy is None:
        policy = RetryPolicy()

    last_error = None
    delay = policy.delay

    for attempt in range(policy.max_attempts):
        try:
            return func()
        except Exception as e:
            last_error = e
            if attempt < policy.max_attempts - 1:
                time.sleep(delay)
                delay = min(delay * policy.backoff_factor, policy.max_delay)
            else:
                raise

    raise last_error