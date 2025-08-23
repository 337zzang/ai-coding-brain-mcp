"""
In-memory LRU cache implementation.
"""

from collections import OrderedDict
from typing import Any, Optional
import sys
import pickle
import logging

from ..base import BaseCache

logger = logging.getLogger(__name__)


class MemoryCache(BaseCache):
    """
    LRU memory cache with size limits.
    """
    
    def __init__(self, max_size_mb: float = 100):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.cache = OrderedDict()
        self.size_bytes = 0
        
    def get(self, key: str) -> Optional[Any]:
        """Get value and move to end (most recently used)."""
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def put(self, key: str, value: Any) -> bool:
        """Store value with LRU eviction."""
        try:
            # Estimate size
            size = sys.getsizeof(value)
            
            # Check if it fits
            if size > self.max_size_bytes:
                return False
            
            # Evict if necessary
            while self.size_bytes + size > self.max_size_bytes and self.cache:
                evicted_key = next(iter(self.cache))
                evicted_value = self.cache.pop(evicted_key)
                self.size_bytes -= sys.getsizeof(evicted_value)
            
            # Store value
            if key in self.cache:
                # Update existing
                old_size = sys.getsizeof(self.cache[key])
                self.size_bytes -= old_size
            
            self.cache[key] = value
            self.size_bytes += size
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        return key in self.cache
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if key in self.cache:
            value = self.cache.pop(key)
            self.size_bytes -= sys.getsizeof(value)
            return True
        return False
    
    def clear(self):
        """Clear all entries."""
        self.cache.clear()
        self.size_bytes = 0
    
    def get_size(self) -> int:
        """Get cache size in bytes."""
        return self.size_bytes