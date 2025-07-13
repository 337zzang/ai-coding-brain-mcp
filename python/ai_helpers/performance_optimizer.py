"""
성능 최적화 및 병렬 처리 강화 모듈
비동기 작업, 캐싱, 병렬 처리 최적화
"""
import asyncio
import threading
import time
import hashlib
import json
import logging
from typing import Dict, Any, List, Optional, Callable, Union, TypeVar, Generic
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from functools import wraps, lru_cache
from pathlib import Path
import weakref

T = TypeVar('T')


@dataclass
class PerformanceMetrics:
    """성능 메트릭"""
    execution_time: float = 0.0
    memory_usage: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    parallel_tasks: int = 0
    total_operations: int = 0
    
    def record_operation(self, execution_time: float, used_cache: bool = False):
        """작업 기록"""
        self.total_operations += 1
        self.execution_time += execution_time
        
        if used_cache:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
    
    def get_cache_hit_rate(self) -> float:
        """캐시 히트율 계산"""
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / max(total, 1)
    
    def get_average_time(self) -> float:
        """평균 실행 시간"""
        return self.execution_time / max(self.total_operations, 1)


class CacheManager:
    """통합 캐시 관리자"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl  # Time To Live (초)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = threading.RLock()
        
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """캐시 키 생성"""
        key_data = {
            'func': func_name,
            'args': args,
            'kwargs': sorted(kwargs.items()) if kwargs else {}
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _is_expired(self, key: str) -> bool:
        """캐시 만료 확인"""
        if key not in self._access_times:
            return True
        return time.time() - self._access_times[key] > self.ttl
    
    def _cleanup_expired(self):
        """만료된 캐시 정리"""
        current_time = time.time()
        expired_keys = [
            key for key, access_time in self._access_times.items()
            if current_time - access_time > self.ttl
        ]
        
        for key in expired_keys:
            self._cache.pop(key, None)
            self._access_times.pop(key, None)
    
    def _evict_lru(self):
        """LRU 방식으로 캐시 제거"""
        if len(self._cache) <= self.max_size:
            return
        
        # 가장 오래된 항목 찾기
        oldest_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
        self._cache.pop(oldest_key, None)
        self._access_times.pop(oldest_key, None)
    
    def get(self, func_name: str, args: tuple, kwargs: dict) -> Optional[Any]:
        """캐시에서 값 조회"""
        with self._lock:
            key = self._generate_key(func_name, args, kwargs)
            
            if key not in self._cache or self._is_expired(key):
                return None
            
            # 액세스 시간 업데이트
            self._access_times[key] = time.time()
            return self._cache[key]['result']
    
    def set(self, func_name: str, args: tuple, kwargs: dict, result: Any):
        """캐시에 값 저장"""
        with self._lock:
            # 만료된 캐시 정리
            self._cleanup_expired()
            
            # 크기 제한 확인
            if len(self._cache) >= self.max_size:
                self._evict_lru()
            
            key = self._generate_key(func_name, args, kwargs)
            self._cache[key] = {
                'result': result,
                'timestamp': time.time()
            }
            self._access_times[key] = time.time()
    
    def clear(self):
        """캐시 전체 정리"""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계"""
        with self._lock:
            return {
                'cache_size': len(self._cache),
                'max_size': self.max_size,
                'ttl': self.ttl,
                'oldest_entry': min(self._access_times.values()) if self._access_times else None,
                'newest_entry': max(self._access_times.values()) if self._access_times else None
            }


class ParallelProcessor:
    """병렬 처리 관리자"""
    
    def __init__(self, max_workers: Optional[int] = None):
        self.max_workers = max_workers or min(32, (threading.active_count() or 1) + 4)
        self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self._futures: List[Future] = []
        
    def submit_task(self, func: Callable, *args, **kwargs) -> Future:
        """작업 제출"""
        future = self._executor.submit(func, *args, **kwargs)
        self._futures.append(future)
        return future
    
    def submit_batch(self, func: Callable, items: List[Any], 
                    chunk_size: Optional[int] = None) -> List[Future]:
        """배치 작업 제출"""
        if chunk_size is None:
            chunk_size = max(1, len(items) // self.max_workers)
        
        futures = []
        for i in range(0, len(items), chunk_size):
            chunk = items[i:i + chunk_size]
            future = self.submit_task(func, chunk)
            futures.append(future)
        
        return futures
    
    def wait_all(self, timeout: Optional[float] = None) -> List[Any]:
        """모든 작업 완료 대기"""
        results = []
        
        try:
            for future in as_completed(self._futures, timeout=timeout):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append(e)
        finally:
            self._futures.clear()
        
        return results
    
    def map_parallel(self, func: Callable, items: List[Any], 
                    chunk_size: Optional[int] = None) -> List[Any]:
        """병렬 매핑"""
        futures = self.submit_batch(func, items, chunk_size)
        return self.wait_all()
    
    def shutdown(self):
        """executor 종료"""
        self._executor.shutdown(wait=True)


class AsyncExecutor:
    """비동기 작업 실행자"""
    
    def __init__(self):
        self._loop = None
        self._thread = None
        self._running = False
    
    def start(self):
        """비동기 루프 시작"""
        if self._running:
            return
        
        def run_loop():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()
        
        self._thread = threading.Thread(target=run_loop, daemon=True)
        self._thread.start()
        self._running = True
        
        # 루프가 시작될 때까지 대기
        while self._loop is None:
            time.sleep(0.01)
    
    def submit_async(self, coro) -> Future:
        """비동기 작업 제출"""
        if not self._running:
            self.start()
        
        return asyncio.run_coroutine_threadsafe(coro, self._loop)
    
    def run_async(self, coro, timeout: Optional[float] = None):
        """비동기 작업 실행 및 결과 대기"""
        future = self.submit_async(coro)
        return future.result(timeout=timeout)
    
    def stop(self):
        """비동기 루프 중지"""
        if self._running and self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join()
            self._running = False


# 전역 성능 관리자 인스턴스
_cache_manager = CacheManager()
_parallel_processor = ParallelProcessor()
_async_executor = AsyncExecutor()
_performance_metrics = PerformanceMetrics()


def with_cache(ttl: int = 3600, key_func: Optional[Callable] = None):
    """캐싱 데코레이터"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            start_time = time.time()
            
            # 캐시 확인
            cached_result = _cache_manager.get(func.__name__, args, kwargs)
            if cached_result is not None:
                execution_time = time.time() - start_time
                _performance_metrics.record_operation(execution_time, used_cache=True)
                return cached_result
            
            # 실제 함수 실행
            result = func(*args, **kwargs)
            
            # 캐시에 저장
            _cache_manager.set(func.__name__, args, kwargs, result)
            
            execution_time = time.time() - start_time
            _performance_metrics.record_operation(execution_time, used_cache=False)
            
            return result
        
        return wrapper
    return decorator


def with_parallel(chunk_size: Optional[int] = None):
    """병렬 처리 데코레이터"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(items: List[Any], *args, **kwargs) -> List[T]:
            if not isinstance(items, list) or len(items) <= 1:
                return func(items, *args, **kwargs)
            
            start_time = time.time()
            
            def process_item(item):
                return func(item, *args, **kwargs)
            
            results = _parallel_processor.map_parallel(process_item, items, chunk_size)
            
            execution_time = time.time() - start_time
            _performance_metrics.record_operation(execution_time)
            _performance_metrics.parallel_tasks += len(items)
            
            return results
        
        return wrapper
    return decorator


def with_async_support(timeout: Optional[float] = None):
    """비동기 지원 데코레이터"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            # 동기 함수를 비동기로 실행
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, func, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            return func(*args, **kwargs)
        
        # 비동기와 동기 버전 모두 제공
        sync_wrapper.async_version = async_wrapper
        return sync_wrapper
    
    return decorator


class PerformanceOptimizer:
    """성능 최적화 통합 관리자"""
    
    def __init__(self):
        self.cache_manager = _cache_manager
        self.parallel_processor = _parallel_processor
        self.async_executor = _async_executor
        self.metrics = _performance_metrics
        
        # 성능 프로파일링
        self._profiling_enabled = False
        self._profile_data = {}
    
    def enable_profiling(self):
        """프로파일링 활성화"""
        self._profiling_enabled = True
    
    def disable_profiling(self):
        """프로파일링 비활성화"""
        self._profiling_enabled = False
    
    def profile_function(self, func: Callable) -> Callable:
        """함수 프로파일링"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self._profiling_enabled:
                return func(*args, **kwargs)
            
            start_time = time.time()
            start_memory = self._get_memory_usage()
            
            try:
                result = func(*args, **kwargs)
                success = True
            except Exception as e:
                result = e
                success = False
            
            end_time = time.time()
            end_memory = self._get_memory_usage()
            
            # 프로파일 데이터 기록
            func_name = func.__name__
            if func_name not in self._profile_data:
                self._profile_data[func_name] = {
                    'call_count': 0,
                    'total_time': 0.0,
                    'avg_time': 0.0,
                    'memory_delta': 0,
                    'success_count': 0,
                    'error_count': 0
                }
            
            profile = self._profile_data[func_name]
            profile['call_count'] += 1
            execution_time = end_time - start_time
            profile['total_time'] += execution_time
            profile['avg_time'] = profile['total_time'] / profile['call_count']
            profile['memory_delta'] = end_memory - start_memory
            
            if success:
                profile['success_count'] += 1
            else:
                profile['error_count'] += 1
            
            if not success:
                raise result
            
            return result
        
        return wrapper
    
    def _get_memory_usage(self) -> int:
        """메모리 사용량 조회 (간단한 버전)"""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss
        except ImportError:
            return 0
    
    def get_performance_report(self) -> Dict[str, Any]:
        """성능 리포트 생성"""
        cache_stats = self.cache_manager.get_stats()
        
        return {
            'metrics': {
                'total_operations': self.metrics.total_operations,
                'total_execution_time': self.metrics.execution_time,
                'average_execution_time': self.metrics.get_average_time(),
                'cache_hit_rate': self.metrics.get_cache_hit_rate(),
                'parallel_tasks': self.metrics.parallel_tasks
            },
            'cache': cache_stats,
            'parallel': {
                'max_workers': self.parallel_processor.max_workers,
                'active_tasks': len(self.parallel_processor._futures)
            },
            'profiling': self._profile_data if self._profiling_enabled else None
        }
    
    def optimize_function(self, func: Callable, 
                         use_cache: bool = True,
                         use_parallel: bool = False,
                         use_async: bool = False,
                         cache_ttl: int = 3600) -> Callable:
        """함수 최적화 적용"""
        optimized_func = func
        
        # 프로파일링 적용
        if self._profiling_enabled:
            optimized_func = self.profile_function(optimized_func)
        
        # 캐싱 적용
        if use_cache:
            optimized_func = with_cache(ttl=cache_ttl)(optimized_func)
        
        # 병렬 처리 적용
        if use_parallel:
            optimized_func = with_parallel()(optimized_func)
        
        # 비동기 지원 적용
        if use_async:
            optimized_func = with_async_support()(optimized_func)
        
        return optimized_func
    
    def clear_all_caches(self):
        """모든 캐시 정리"""
        self.cache_manager.clear()
    
    def reset_metrics(self):
        """메트릭 초기화"""
        self.metrics = PerformanceMetrics()
    
    def shutdown(self):
        """리소스 정리"""
        self.parallel_processor.shutdown()
        self.async_executor.stop()


# 전역 최적화 관리자
_performance_optimizer = PerformanceOptimizer()


def get_performance_optimizer() -> PerformanceOptimizer:
    """전역 성능 최적화 관리자 반환"""
    return _performance_optimizer


def optimize_io_operations(batch_size: int = 10):
    """I/O 작업 최적화 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(paths: List[str], *args, **kwargs):
            if not isinstance(paths, list):
                return func(paths, *args, **kwargs)
            
            # 배치 단위로 처리
            results = []
            for i in range(0, len(paths), batch_size):
                batch = paths[i:i + batch_size]
                
                # 병렬 처리
                futures = []
                for path in batch:
                    future = _parallel_processor.submit_task(func, path, *args, **kwargs)
                    futures.append(future)
                
                # 결과 수집
                batch_results = [future.result() for future in futures]
                results.extend(batch_results)
            
            return results
        
        return wrapper
    return decorator


# 편의 함수들
def enable_performance_profiling():
    """성능 프로파일링 활성화"""
    _performance_optimizer.enable_profiling()


def disable_performance_profiling():
    """성능 프로파일링 비활성화"""
    _performance_optimizer.disable_profiling()


def get_performance_report() -> Dict[str, Any]:
    """성능 리포트 조회"""
    return _performance_optimizer.get_performance_report()


def clear_performance_caches():
    """성능 캐시 정리"""
    _performance_optimizer.clear_all_caches()