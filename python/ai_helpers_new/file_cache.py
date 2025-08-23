"""
File Cache System - 파일 읽기 캐싱 시스템
자주 읽는 파일의 성능 향상을 위한 스마트 캐싱
생성일: 2025-08-23
"""

import os
import hashlib
import json
import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from functools import lru_cache
import threading

class FileCache:
    """파일 캐싱 시스템"""

    def __init__(self, 
                 max_size: int = 100,
                 ttl_seconds: int = 300,
                 max_file_size: int = 1024 * 1024):  # 1MB
        """
        Args:
            max_size: 최대 캐시 항목 수
            ttl_seconds: 캐시 유효 시간 (초)
            max_file_size: 캐싱할 최대 파일 크기 (바이트)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.max_file_size = max_file_size

        # 캐시 저장소
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_count: Dict[str, int] = {}
        self.lock = threading.RLock()

        # 통계
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_reads': 0,
            'bytes_saved': 0
        }

    def _get_file_key(self, filepath: str) -> Tuple[str, float, int]:
        """파일 키 생성 (경로, 수정시간, 크기)"""
        try:
            stat = os.stat(filepath)
            return (
                os.path.abspath(filepath),
                stat.st_mtime,
                stat.st_size
            )
        except OSError:
            return (filepath, 0, 0)

    def _create_cache_key(self, filepath: str, mtime: float) -> str:
        """캐시 키 생성"""
        key_str = f"{filepath}:{mtime}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def _is_cacheable(self, filepath: str, size: int) -> bool:
        """캐싱 가능 여부 확인"""
        # 크기 체크
        if size > self.max_file_size:
            return False

        # 확장자 체크 (바이너리 파일 제외)
        ext = os.path.splitext(filepath)[1].lower()
        non_cacheable = {'.exe', '.dll', '.so', '.dylib', '.zip', '.tar', '.gz'}
        if ext in non_cacheable:
            return False

        return True

    def get(self, filepath: str, encoding: str = 'utf-8') -> Optional[str]:
        """캐시에서 파일 내용 가져오기"""
        with self.lock:
            self.stats['total_reads'] += 1

            # 파일 정보 가져오기
            abs_path, mtime, size = self._get_file_key(filepath)

            # 캐싱 가능 여부 확인
            if not self._is_cacheable(abs_path, size):
                self.stats['misses'] += 1
                return None

            # 캐시 키 생성
            cache_key = self._create_cache_key(abs_path, mtime)

            # 캐시 확인
            if cache_key in self.cache:
                entry = self.cache[cache_key]

                # TTL 확인
                if time.time() - entry['timestamp'] < self.ttl_seconds:
                    # 캐시 히트
                    self.stats['hits'] += 1
                    self.stats['bytes_saved'] += size

                    # 접근 횟수 증가
                    self.access_count[cache_key] = self.access_count.get(cache_key, 0) + 1

                    # LRU 업데이트
                    entry['last_access'] = time.time()

                    return entry['content']
                else:
                    # 만료된 캐시 제거
                    del self.cache[cache_key]
                    if cache_key in self.access_count:
                        del self.access_count[cache_key]

            self.stats['misses'] += 1
            return None

    def put(self, filepath: str, content: str, encoding: str = 'utf-8'):
        """파일 내용을 캐시에 저장"""
        with self.lock:
            # 파일 정보
            abs_path, mtime, size = self._get_file_key(filepath)

            # 캐싱 가능 여부
            if not self._is_cacheable(abs_path, size):
                return

            # 캐시 크기 제한 체크
            if len(self.cache) >= self.max_size:
                self._evict_lru()

            # 캐시 키 생성
            cache_key = self._create_cache_key(abs_path, mtime)

            # 캐시 저장
            self.cache[cache_key] = {
                'filepath': abs_path,
                'content': content,
                'size': size,
                'mtime': mtime,
                'timestamp': time.time(),
                'last_access': time.time(),
                'encoding': encoding
            }

            self.access_count[cache_key] = 0

    def _evict_lru(self):
        """LRU 기반 캐시 제거"""
        if not self.cache:
            return

        # 가장 오래 사용하지 않은 항목 찾기
        lru_key = min(self.cache.keys(), 
                     key=lambda k: self.cache[k]['last_access'])

        # 제거
        del self.cache[lru_key]
        if lru_key in self.access_count:
            del self.access_count[lru_key]
        self.stats['evictions'] += 1

    def invalidate(self, filepath: str):
        """특정 파일 캐시 무효화"""
        with self.lock:
            abs_path = os.path.abspath(filepath)

            # 해당 파일의 모든 캐시 엔트리 제거
            keys_to_remove = []
            for key, entry in self.cache.items():
                if entry['filepath'] == abs_path:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self.cache[key]
                if key in self.access_count:
                    del self.access_count[key]

    def clear(self):
        """전체 캐시 초기화"""
        with self.lock:
            self.cache.clear()
            self.access_count.clear()

    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        with self.lock:
            total = self.stats['hits'] + self.stats['misses']
            hit_rate = (self.stats['hits'] / total * 100) if total > 0 else 0

            # 인기 파일 통계
            popular_files = []
            for key, count in sorted(self.access_count.items(), 
                                    key=lambda x: x[1], reverse=True)[:5]:
                if key in self.cache:
                    entry = self.cache[key]
                    popular_files.append({
                        'file': os.path.basename(entry['filepath']),
                        'accesses': count,
                        'size': entry['size']
                    })

            return {
                'cache_size': len(self.cache),
                'max_size': self.max_size,
                'ttl_seconds': self.ttl_seconds,
                'statistics': {
                    **self.stats,
                    'hit_rate': f"{hit_rate:.1f}%"
                },
                'popular_files': popular_files,
                'memory_usage': sum(entry['size'] for entry in self.cache.values())
            }


class CachedFileReader:
    """캐싱이 적용된 파일 리더"""

    def __init__(self, cache: Optional[FileCache] = None):
        self.cache = cache or FileCache()

    def read(self, filepath: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """파일 읽기 (캐싱 적용)"""
        try:
            # 캐시 확인
            content = self.cache.get(filepath, encoding)

            if content is not None:
                # 캐시 히트
                return {
                    'ok': True,
                    'data': content,
                    'cached': True,
                    'message': '캐시에서 읽음'
                }

            # 캐시 미스 - 파일 읽기
            with open(filepath, 'r', encoding=encoding) as f:
                content = f.read()

            # 캐시에 저장
            self.cache.put(filepath, content, encoding)

            return {
                'ok': True,
                'data': content,
                'cached': False,
                'message': '파일에서 읽음'
            }

        except Exception as e:
            return {
                'ok': False,
                'error': str(e),
                'cached': False
            }

    def write(self, filepath: str, content: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """파일 쓰기 (캐시 무효화)"""
        try:
            with open(filepath, 'w', encoding=encoding) as f:
                f.write(content)

            # 캐시 무효화
            self.cache.invalidate(filepath)

            return {
                'ok': True,
                'message': '파일 저장 및 캐시 무효화'
            }

        except Exception as e:
            return {
                'ok': False,
                'error': str(e)
            }

    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계"""
        return self.cache.get_stats()


# 싱글톤 인스턴스
_file_cache = FileCache()
_cached_reader = CachedFileReader(_file_cache)

# 편의 함수
def cached_read(filepath: str, encoding: str = 'utf-8') -> Dict[str, Any]:
    """캐싱된 파일 읽기"""
    return _cached_reader.read(filepath, encoding)

def cached_write(filepath: str, content: str, encoding: str = 'utf-8') -> Dict[str, Any]:
    """파일 쓰기 (캐시 자동 무효화)"""
    return _cached_reader.write(filepath, content, encoding)

def get_cache_stats() -> Dict[str, Any]:
    """캐시 통계 조회"""
    return _cached_reader.get_cache_stats()

def clear_cache():
    """캐시 초기화"""
    _file_cache.clear()


# Export
__all__ = [
    'FileCache',
    'CachedFileReader',
    'cached_read',
    'cached_write', 
    'get_cache_stats',
    'clear_cache'
]
