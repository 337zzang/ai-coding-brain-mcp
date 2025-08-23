"""
SQLite-based cache for warm data storage.
"""

import sqlite3
import pickle
import time
import logging
from typing import Any, Optional, List
import zlib

from ..base import BaseCache

logger = logging.getLogger(__name__)


class SQLiteCache(BaseCache):
    """
    SQLite cache with compression support.
    """
    
    def __init__(
        self,
        db_path: str = ".cache.db",
        max_size_mb: float = 1000,
        compress: bool = True
    ):
        self.db_path = db_path
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.compress = compress
        
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    size_bytes INTEGER,
                    created_at REAL,
                    accessed_at REAL,
                    access_count INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_accessed 
                ON cache(accessed_at)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_size 
                ON cache(size_bytes)
            """)
            conn.commit()
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT value FROM cache WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
            
            if row:
                # Update access metadata
                conn.execute(
                    """UPDATE cache 
                       SET accessed_at = ?, access_count = access_count + 1
                       WHERE key = ?""",
                    (time.time(), key)
                )
                conn.commit()
                
                # Deserialize value
                try:
                    data = row[0]
                    if self.compress:
                        data = zlib.decompress(data)
                    return pickle.loads(data)
                except Exception as e:
                    logger.error(f"Failed to deserialize {key}: {e}")
                    return None
        
        return None
    
    def put(self, key: str, value: Any) -> bool:
        """Store value in cache."""
        try:
            # Serialize value
            serialized = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
            if self.compress:
                serialized = zlib.compress(serialized)
            
            size_bytes = len(serialized)
            
            # Check size limit
            if size_bytes > self.max_size_bytes:
                return False
            
            # Ensure capacity
            self._ensure_capacity(size_bytes)
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO cache 
                       (key, value, size_bytes, created_at, accessed_at, access_count)
                       VALUES (?, ?, ?, ?, ?, COALESCE(
                           (SELECT access_count FROM cache WHERE key = ?), 0
                       ))""",
                    (key, serialized, size_bytes, time.time(), time.time(), key)
                )
                conn.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache {key}: {e}")
            return False
    
    def _ensure_capacity(self, required_bytes: int):
        """Ensure cache has capacity by evicting LRU entries."""
        with sqlite3.connect(self.db_path) as conn:
            # Get current size
            cursor = conn.execute("SELECT SUM(size_bytes) FROM cache")
            current_size = cursor.fetchone()[0] or 0
            
            if current_size + required_bytes > self.max_size_bytes:
                # Need to evict
                bytes_to_free = (current_size + required_bytes) - self.max_size_bytes
                
                # Get LRU entries
                cursor = conn.execute(
                    """SELECT key, size_bytes FROM cache
                       ORDER BY accessed_at ASC"""
                )
                
                freed = 0
                keys_to_delete = []
                
                for key, size in cursor:
                    keys_to_delete.append(key)
                    freed += size
                    if freed >= bytes_to_free:
                        break
                
                # Delete entries
                if keys_to_delete:
                    placeholders = ','.join('?' * len(keys_to_delete))
                    conn.execute(
                        f"DELETE FROM cache WHERE key IN ({placeholders})",
                        keys_to_delete
                    )
                    conn.commit()
                    logger.debug(f"Evicted {len(keys_to_delete)} entries")
    
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM cache WHERE key = ? LIMIT 1",
                (key,)
            )
            return cursor.fetchone() is not None
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM cache WHERE key = ?",
                (key,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def clear(self):
        """Clear all entries."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM cache")
            conn.commit()
        
        # VACUUM must be run outside transaction
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("VACUUM")
            conn.close()
        except:
            pass  # VACUUM is optional optimization
    
    def get_size(self) -> int:
        """Get total cache size in bytes."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT SUM(size_bytes) FROM cache")
            return cursor.fetchone()[0] or 0
    
    def list_keys(self, pattern: str = "%") -> List[str]:
        """List keys matching pattern."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT key FROM cache WHERE key LIKE ?",
                (pattern,)
            )
            return [row[0] for row in cursor]
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        with sqlite3.connect(self.db_path) as conn:
            # Entry count
            cursor = conn.execute("SELECT COUNT(*) FROM cache")
            count = cursor.fetchone()[0]
            
            # Total size
            cursor = conn.execute("SELECT SUM(size_bytes) FROM cache")
            total_size = cursor.fetchone()[0] or 0
            
            # Average size
            avg_size = total_size / count if count > 0 else 0
            
            # Most accessed
            cursor = conn.execute(
                """SELECT key, access_count FROM cache
                   ORDER BY access_count DESC LIMIT 5"""
            )
            most_accessed = [
                {'key': row[0], 'count': row[1]}
                for row in cursor
            ]
            
            return {
                'entries': count,
                'total_size_mb': total_size / (1024 * 1024),
                'avg_size_kb': avg_size / 1024,
                'most_accessed': most_accessed,
                'compression': self.compress
            }