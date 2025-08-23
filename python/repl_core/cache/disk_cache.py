"""
Disk-based cache for large objects and archives.
"""

import os
import pickle
import hashlib
import time
import json
import logging
from typing import Any, Optional, List, Dict
import zlib
from pathlib import Path

from ..base import BaseCache

logger = logging.getLogger(__name__)


class DiskCache(BaseCache):
    """
    File-based cache with optional compression.
    Supports Parquet for DataFrames and pickle for general objects.
    """
    
    def __init__(
        self,
        cache_dir: str = ".disk_cache",
        max_size_mb: float = 10000,
        compress: bool = False
    ):
        self.cache_dir = Path(cache_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.compress = compress
        
        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Metadata file
        self.metadata_file = self.cache_dir / "metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load cache metadata."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_metadata(self):
        """Save cache metadata."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def _get_file_path(self, key: str) -> Path:
        """Get file path for cache key."""
        # Use hash to avoid filesystem issues
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash[:2]}" / f"{key_hash}.cache"
    
    def _is_dataframe(self, obj: Any) -> bool:
        """Check if object is a pandas DataFrame."""
        return type(obj).__name__ == 'DataFrame'
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from disk."""
        file_path = self._get_file_path(key)
        
        if not file_path.exists():
            return None
        
        try:
            # Update access time
            if key in self.metadata:
                self.metadata[key]['accessed_at'] = time.time()
                self.metadata[key]['access_count'] += 1
                self._save_metadata()
            
            # Check file type from metadata
            file_type = self.metadata.get(key, {}).get('type', 'pickle')
            
            if file_type == 'parquet':
                # Load as DataFrame
                try:
                    import pandas as pd
                    return pd.read_parquet(file_path)
                except ImportError:
                    logger.error("pandas required for Parquet files")
                    return None
            
            else:
                # Load as pickle
                with open(file_path, 'rb') as f:
                    data = f.read()
                    if self.compress:
                        data = zlib.decompress(data)
                    return pickle.loads(data)
                    
        except Exception as e:
            logger.error(f"Failed to load {key}: {e}")
            return None
    
    def put(self, key: str, value: Any) -> bool:
        """Store value on disk."""
        file_path = self._get_file_path(key)
        
        try:
            # Create directory if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Determine storage format
            if self._is_dataframe(value):
                # Save as Parquet for DataFrames
                try:
                    import pandas as pd
                    value.to_parquet(file_path, compression='snappy' if self.compress else None)
                    file_type = 'parquet'
                except ImportError:
                    # Fallback to pickle
                    file_type = 'pickle'
                    serialized = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
                    if self.compress:
                        serialized = zlib.compress(serialized)
                    with open(file_path, 'wb') as f:
                        f.write(serialized)
            else:
                # Use pickle for general objects
                file_type = 'pickle'
                serialized = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
                if self.compress:
                    serialized = zlib.compress(serialized)
                
                with open(file_path, 'wb') as f:
                    f.write(serialized)
            
            # Update metadata
            file_size = file_path.stat().st_size
            self.metadata[key] = {
                'file_path': str(file_path),
                'size_bytes': file_size,
                'type': file_type,
                'created_at': time.time(),
                'accessed_at': time.time(),
                'access_count': 0,
                'compressed': self.compress
            }
            self._save_metadata()
            
            # Check capacity
            self._ensure_capacity()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache {key}: {e}")
            # Clean up partial file
            if file_path.exists():
                file_path.unlink()
            return False
    
    def _ensure_capacity(self):
        """Ensure cache stays within size limits."""
        total_size = sum(
            entry['size_bytes']
            for entry in self.metadata.values()
        )
        
        if total_size > self.max_size_bytes:
            # Sort by LRU
            sorted_entries = sorted(
                self.metadata.items(),
                key=lambda x: x[1]['accessed_at']
            )
            
            # Evict until under limit
            bytes_to_free = total_size - self.max_size_bytes
            freed = 0
            
            for key, entry in sorted_entries:
                if freed >= bytes_to_free:
                    break
                
                file_path = Path(entry['file_path'])
                if file_path.exists():
                    file_path.unlink()
                
                freed += entry['size_bytes']
                del self.metadata[key]
                logger.debug(f"Evicted {key} from disk cache")
            
            self._save_metadata()
    
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        file_path = self._get_file_path(key)
        return file_path.exists()
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        file_path = self._get_file_path(key)
        
        if file_path.exists():
            try:
                file_path.unlink()
                if key in self.metadata:
                    del self.metadata[key]
                    self._save_metadata()
                return True
            except Exception as e:
                logger.error(f"Failed to delete {key}: {e}")
        
        return False
    
    def clear(self):
        """Clear all cache files."""
        # Remove all cache files
        for key, entry in list(self.metadata.items()):
            file_path = Path(entry['file_path'])
            if file_path.exists():
                try:
                    file_path.unlink()
                except:
                    pass
        
        # Clear metadata
        self.metadata.clear()
        self._save_metadata()
        
        # Clean up empty directories
        for subdir in self.cache_dir.iterdir():
            if subdir.is_dir() and not any(subdir.iterdir()):
                subdir.rmdir()
    
    def get_size(self) -> int:
        """Get total cache size in bytes."""
        return sum(
            entry['size_bytes']
            for entry in self.metadata.values()
        )
    
    def list_keys(self) -> List[str]:
        """List all cached keys."""
        return list(self.metadata.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.metadata:
            return {
                'entries': 0,
                'total_size_mb': 0,
                'types': {}
            }
        
        total_size = sum(e['size_bytes'] for e in self.metadata.values())
        
        # Count by type
        type_counts = {}
        for entry in self.metadata.values():
            file_type = entry.get('type', 'unknown')
            type_counts[file_type] = type_counts.get(file_type, 0) + 1
        
        # Most accessed
        sorted_by_access = sorted(
            self.metadata.items(),
            key=lambda x: x[1].get('access_count', 0),
            reverse=True
        )[:5]
        
        return {
            'entries': len(self.metadata),
            'total_size_mb': total_size / (1024 * 1024),
            'types': type_counts,
            'most_accessed': [
                {'key': k, 'count': v.get('access_count', 0)}
                for k, v in sorted_by_access
            ],
            'compression': self.compress
        }