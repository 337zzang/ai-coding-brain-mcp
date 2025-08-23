"""
LRU (Least Recently Used) 캐시 구현
- 시간 기반 만료 (TTL) 지원
- 최대 크기 제한
"""
import time
from collections import OrderedDict
from typing import Any, Optional, Tuple
import threading


class LRUCache:
    """시간 기반 만료를 지원하는 LRU 캐시"""

    def __init__(self, max_size: int = 128, ttl: int = 60):
        """
        Args:
            max_size: 최대 캐시 크기
            ttl: Time To Live (초)
        """
        self.max_size = max_size
        self.ttl = ttl
        self._data: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._lock = threading.RLock()  # 스레드 안전성

    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 가져오기"""
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None

            value, timestamp = item

            # TTL 확인
            if time.time() - timestamp > self.ttl:
                # 만료된 항목 제거
                self._data.pop(key, None)
                return None

            # 최근 사용으로 이동
            self._data.move_to_end(key)
            return value

    def set(self, key: str, value: Any) -> None:
        """캐시에 값 설정"""
        with self._lock:
            # 기존 항목 제거 (순서 업데이트를 위해)
            if key in self._data:
                del self._data[key]

            # 새 항목 추가
            self._data[key] = (value, time.time())

            # 크기 초과 시 가장 오래된 항목 제거
            if len(self._data) > self.max_size:
                self._data.popitem(last=False)

    def invalidate(self, key: Optional[str] = None) -> None:
        """캐시 무효화"""
        with self._lock:
            if key is None:
                # 전체 캐시 클리어
                self._data.clear()
            else:
                # 특정 키만 제거
                self._data.pop(key, None)

    def invalidate_pattern(self, pattern: str) -> None:
        """패턴에 맞는 키들 무효화"""
        with self._lock:
            keys_to_remove = [k for k in self._data if pattern in k]
            for key in keys_to_remove:
                self._data.pop(key, None)

    def size(self) -> int:
        """현재 캐시 크기"""
        return len(self._data)

    def clear_expired(self) -> int:
        """만료된 항목 정리"""
        with self._lock:
            current_time = time.time()
            expired_keys = []

            for key, (value, timestamp) in self._data.items():
                if current_time - timestamp > self.ttl:
                    expired_keys.append(key)

            for key in expired_keys:
                self._data.pop(key)

            return len(expired_keys)

    def stats(self) -> dict:
        """캐시 통계"""
        with self._lock:
            return {
                'size': len(self._data),
                'max_size': self.max_size,
                'ttl': self.ttl,
                'keys': list(self._data.keys())
            }
