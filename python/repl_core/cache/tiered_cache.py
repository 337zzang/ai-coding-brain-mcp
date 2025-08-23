"""
Multi-tier caching system with automatic tier migration.
"""

import time
import logging
from typing import Any, Optional, Dict, List, Tuple
from enum import Enum
from dataclasses import dataclass
from collections import OrderedDict
import hashlib
import pickle

from ..base import BaseCache

logger = logging.getLogger(__name__)


class CacheTier(Enum):
    """Cache tier levels."""
    L1_MEMORY = "memory"      # Hot data (<100MB)
    L2_SQLITE = "sqlite"       # Warm data (100MB-1GB)
    L3_PARQUET = "parquet"     # Cold data (1GB-10GB)
    L4_COMPRESSED = "compressed"  # Archive (>10GB)


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    size_bytes: int
    tier: CacheTier
    access_count: int = 0
    last_access: float = 0.0
    created_at: float = 0.0
    ttl: Optional[float] = None
    
    @property
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl
    
    @property
    def access_frequency(self) -> float:
        """Calculate access frequency score."""
        age = time.time() - self.created_at
        if age > 0:
            return self.access_count / age
        return float('inf')


class TieredCache:
    """
    Multi-tier cache with automatic migration between tiers.
    
    Features:
    - Automatic tier promotion/demotion
    - LRU eviction within tiers
    - TTL support
    - Compression for large objects
    - Statistics tracking
    """
    
    def __init__(
        self,
        memory_limit_mb: float = 100,
        sqlite_limit_mb: float = 1000,
        parquet_limit_mb: float = 10000,
        cache_dir: str = ".repl_cache"
    ):
        self.memory_limit_mb = memory_limit_mb
        self.sqlite_limit_mb = sqlite_limit_mb
        self.parquet_limit_mb = parquet_limit_mb
        self.cache_dir = cache_dir
        
        # Initialize tier backends
        self._init_tiers()
        
        # Metadata tracking
        self._entries: Dict[str, CacheEntry] = {}
        self._tier_sizes: Dict[CacheTier, int] = {
            tier: 0 for tier in CacheTier
        }
        
        # Statistics
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'promotions': 0,
            'demotions': 0
        }
        
    def _init_tiers(self):
        """Initialize cache tier backends."""
        import os
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # L1: In-memory LRU cache
        from .memory_cache import MemoryCache
        self._memory_cache = MemoryCache(
            max_size_mb=self.memory_limit_mb
        )
        
        # L2: SQLite cache
        from .sqlite_cache import SQLiteCache
        self._sqlite_cache = SQLiteCache(
            db_path=os.path.join(self.cache_dir, "cache.db"),
            max_size_mb=self.sqlite_limit_mb
        )
        
        # L3: Parquet cache (for DataFrames)
        from .disk_cache import DiskCache
        self._parquet_cache = DiskCache(
            cache_dir=os.path.join(self.cache_dir, "parquet"),
            max_size_mb=self.parquet_limit_mb
        )
        
        # L4: Compressed archive
        self._compressed_cache = DiskCache(
            cache_dir=os.path.join(self.cache_dir, "compressed"),
            compress=True
        )
        
        # Tier mapping
        self._tier_backends = {
            CacheTier.L1_MEMORY: self._memory_cache,
            CacheTier.L2_SQLITE: self._sqlite_cache,
            CacheTier.L3_PARQUET: self._parquet_cache,
            CacheTier.L4_COMPRESSED: self._compressed_cache
        }
    
    def _determine_tier(self, size_bytes: int) -> CacheTier:
        """Determine appropriate tier based on object size."""
        size_mb = size_bytes / (1024 * 1024)
        
        if size_mb < 10:
            return CacheTier.L1_MEMORY
        elif size_mb < 100:
            return CacheTier.L2_SQLITE
        elif size_mb < 1000:
            return CacheTier.L3_PARQUET
        else:
            return CacheTier.L4_COMPRESSED
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache with automatic tier promotion.
        """
        if key not in self._entries:
            self._stats['misses'] += 1
            return None
        
        entry = self._entries[key]
        
        # Check expiration
        if entry.is_expired:
            self.delete(key)
            self._stats['misses'] += 1
            return None
        
        # Get from appropriate tier
        backend = self._tier_backends[entry.tier]
        value = backend.get(key)
        
        if value is None:
            # Data corruption or missing
            del self._entries[key]
            self._stats['misses'] += 1
            return None
        
        # Update access metadata
        entry.access_count += 1
        entry.last_access = time.time()
        
        # Consider promotion if frequently accessed
        if entry.access_frequency > 10 and entry.tier != CacheTier.L1_MEMORY:
            self._promote_entry(key, entry, value)
        
        self._stats['hits'] += 1
        return value
    
    def put(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None
    ) -> bool:
        """
        Store value in appropriate cache tier.
        """
        # Estimate size
        try:
            serialized = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
            size_bytes = len(serialized)
        except:
            return False
        
        # Determine tier
        tier = self._determine_tier(size_bytes)
        
        # Check tier capacity and evict if needed
        self._ensure_capacity(tier, size_bytes)
        
        # Store in backend
        backend = self._tier_backends[tier]
        success = backend.put(key, value)
        
        if success:
            # Update metadata
            self._entries[key] = CacheEntry(
                key=key,
                size_bytes=size_bytes,
                tier=tier,
                access_count=0,
                last_access=time.time(),
                created_at=time.time(),
                ttl=ttl
            )
            self._tier_sizes[tier] += size_bytes
            
            logger.debug(f"Cached {key} in {tier.value} (size: {size_bytes})")
        
        return success
    
    def _ensure_capacity(self, tier: CacheTier, required_bytes: int):
        """Ensure tier has capacity, evicting if necessary."""
        tier_limit_bytes = {
            CacheTier.L1_MEMORY: self.memory_limit_mb * 1024 * 1024,
            CacheTier.L2_SQLITE: self.sqlite_limit_mb * 1024 * 1024,
            CacheTier.L3_PARQUET: self.parquet_limit_mb * 1024 * 1024,
            CacheTier.L4_COMPRESSED: float('inf')
        }
        
        limit = tier_limit_bytes[tier]
        current_size = self._tier_sizes[tier]
        
        if current_size + required_bytes > limit:
            # Need to evict or demote entries
            self._evict_from_tier(tier, required_bytes)
    
    def _evict_from_tier(self, tier: CacheTier, required_bytes: int):
        """Evict entries from tier to make space."""
        # Get entries in this tier sorted by LRU
        tier_entries = [
            (k, e) for k, e in self._entries.items()
            if e.tier == tier
        ]
        tier_entries.sort(key=lambda x: x[1].last_access)
        
        freed_bytes = 0
        for key, entry in tier_entries:
            if freed_bytes >= required_bytes:
                break
            
            # Try to demote to lower tier
            if tier != CacheTier.L4_COMPRESSED:
                next_tier = CacheTier(list(CacheTier)[list(CacheTier).index(tier) + 1])
                backend = self._tier_backends[tier]
                value = backend.get(key)
                
                if value and self._demote_entry(key, entry, value, next_tier):
                    freed_bytes += entry.size_bytes
                    continue
            
            # Otherwise evict completely
            self.delete(key)
            freed_bytes += entry.size_bytes
            self._stats['evictions'] += 1
    
    def _promote_entry(self, key: str, entry: CacheEntry, value: Any) -> bool:
        """Promote entry to higher tier."""
        current_tier_idx = list(CacheTier).index(entry.tier)
        if current_tier_idx == 0:
            return False  # Already at highest tier
        
        new_tier = CacheTier(list(CacheTier)[current_tier_idx - 1])
        
        # Check capacity in new tier
        self._ensure_capacity(new_tier, entry.size_bytes)
        
        # Move to new tier
        old_backend = self._tier_backends[entry.tier]
        new_backend = self._tier_backends[new_tier]
        
        if new_backend.put(key, value):
            old_backend.delete(key)
            
            # Update metadata
            self._tier_sizes[entry.tier] -= entry.size_bytes
            self._tier_sizes[new_tier] += entry.size_bytes
            entry.tier = new_tier
            
            self._stats['promotions'] += 1
            logger.debug(f"Promoted {key} to {new_tier.value}")
            return True
        
        return False
    
    def _demote_entry(
        self,
        key: str,
        entry: CacheEntry,
        value: Any,
        new_tier: CacheTier
    ) -> bool:
        """Demote entry to lower tier."""
        old_backend = self._tier_backends[entry.tier]
        new_backend = self._tier_backends[new_tier]
        
        if new_backend.put(key, value):
            old_backend.delete(key)
            
            # Update metadata
            self._tier_sizes[entry.tier] -= entry.size_bytes
            self._tier_sizes[new_tier] += entry.size_bytes
            entry.tier = new_tier
            
            self._stats['demotions'] += 1
            logger.debug(f"Demoted {key} to {new_tier.value}")
            return True
        
        return False
    
    def delete(self, key: str) -> bool:
        """Delete entry from cache."""
        if key not in self._entries:
            return False
        
        entry = self._entries[key]
        backend = self._tier_backends[entry.tier]
        
        if backend.delete(key):
            self._tier_sizes[entry.tier] -= entry.size_bytes
            del self._entries[key]
            return True
        
        return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if key not in self._entries:
            return False
        
        entry = self._entries[key]
        if entry.is_expired:
            self.delete(key)
            return False
        
        return True
    
    def clear(self):
        """Clear all cache entries."""
        for backend in self._tier_backends.values():
            backend.clear()
        
        self._entries.clear()
        self._tier_sizes = {tier: 0 for tier in CacheTier}
        
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        hit_rate = 0.0
        total = self._stats['hits'] + self._stats['misses']
        if total > 0:
            hit_rate = self._stats['hits'] / total
        
        return {
            'entries': len(self._entries),
            'hit_rate': hit_rate,
            'stats': self._stats.copy(),
            'tier_sizes': {
                tier.value: size / (1024 * 1024)  # MB
                for tier, size in self._tier_sizes.items()
            },
            'tier_counts': {
                tier.value: sum(1 for e in self._entries.values() if e.tier == tier)
                for tier in CacheTier
            }
        }
    
    def optimize(self):
        """
        Optimize cache by rebalancing tiers based on access patterns.
        """
        logger.info("Optimizing cache...")
        
        # Sort entries by access frequency
        entries_by_freq = sorted(
            self._entries.items(),
            key=lambda x: x[1].access_frequency,
            reverse=True
        )
        
        # Promote frequently accessed items
        for key, entry in entries_by_freq[:10]:  # Top 10
            if entry.tier != CacheTier.L1_MEMORY:
                backend = self._tier_backends[entry.tier]
                value = backend.get(key)
                if value:
                    self._promote_entry(key, entry, value)
        
        # Demote rarely accessed items
        for key, entry in entries_by_freq[-10:]:  # Bottom 10
            if entry.tier == CacheTier.L1_MEMORY:
                backend = self._tier_backends[entry.tier]
                value = backend.get(key)
                if value:
                    self._demote_entry(key, entry, value, CacheTier.L2_SQLITE)
        
        logger.info("Cache optimization completed")