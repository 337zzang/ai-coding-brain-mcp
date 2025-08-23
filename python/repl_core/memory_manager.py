"""
Memory management and monitoring for large-scale data processing.
"""

import gc
import sys
import weakref
import warnings
from typing import Dict, Any, Optional, Tuple, List
from collections import OrderedDict
from dataclasses import dataclass
import time
import logging

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None


logger = logging.getLogger(__name__)


@dataclass
class MemoryStats:
    """Memory statistics snapshot."""
    rss_mb: float          # Resident Set Size
    vms_mb: float          # Virtual Memory Size
    percent: float         # Memory percentage
    available_mb: float    # Available system memory
    gc_stats: Dict[str, int]
    timestamp: float
    
    @property
    def is_critical(self) -> bool:
        """Check if memory usage is critical (>90%)."""
        return self.percent > 90.0
    
    @property
    def is_warning(self) -> bool:
        """Check if memory usage needs attention (>75%)."""
        return self.percent > 75.0


class MemoryManager:
    """
    Advanced memory manager for large-scale data processing.
    
    Features:
    - Real-time memory monitoring
    - Automatic garbage collection
    - Memory-mapped variable storage
    - Spill-to-disk for large objects
    - Memory pressure detection
    """
    
    def __init__(
        self,
        memory_limit_mb: float = 1000.0,
        gc_threshold_mb: float = 500.0,
        spill_threshold_mb: float = 800.0,
        cache_dir: str = ".repl_cache"
    ):
        self.memory_limit_mb = memory_limit_mb
        self.gc_threshold_mb = gc_threshold_mb
        self.spill_threshold_mb = spill_threshold_mb
        self.cache_dir = cache_dir
        
        # Tracking
        self._last_gc_time = time.time()
        self._gc_interval = 30  # seconds
        self._memory_history: List[MemoryStats] = []
        self._spilled_objects: Dict[str, str] = {}  # name -> file path
        self._weak_refs: Dict[str, weakref.ref] = {}
        
        # Initialize cache directory
        import os
        os.makedirs(cache_dir, exist_ok=True)
        
        # Configure garbage collection
        gc.set_threshold(700, 10, 10)  # More aggressive GC
        
    def get_memory_stats(self) -> MemoryStats:
        """Get current memory statistics."""
        if PSUTIL_AVAILABLE:
            process = psutil.Process()
            mem_info = process.memory_info()
            mem_percent = process.memory_percent()
            available = psutil.virtual_memory().available / (1024 * 1024)
        else:
            # Fallback for systems without psutil
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            mem_info = type('MemInfo', (), {
                'rss': usage.ru_maxrss * 1024,  # Convert to bytes
                'vms': 0
            })()
            mem_percent = 0.0
            available = 0.0
        
        gc_stats = {
            f"gen{i}": gc.get_count()[i] 
            for i in range(gc.get_count().__len__())
        }
        
        return MemoryStats(
            rss_mb=mem_info.rss / (1024 * 1024),
            vms_mb=mem_info.vms / (1024 * 1024) if hasattr(mem_info, 'vms') else 0,
            percent=mem_percent,
            available_mb=available,
            gc_stats=gc_stats,
            timestamp=time.time()
        )
    
    def check_memory_pressure(self) -> Tuple[bool, MemoryStats]:
        """
        Check if system is under memory pressure.
        Returns (is_under_pressure, stats).
        """
        stats = self.get_memory_stats()
        self._memory_history.append(stats)
        
        # Keep only last 100 measurements
        if len(self._memory_history) > 100:
            self._memory_history.pop(0)
        
        is_under_pressure = (
            stats.rss_mb > self.spill_threshold_mb or
            stats.is_warning
        )
        
        return is_under_pressure, stats
    
    def trigger_gc_if_needed(self, force: bool = False) -> bool:
        """
        Trigger garbage collection if needed.
        Returns True if GC was triggered.
        """
        current_time = time.time()
        time_since_gc = current_time - self._last_gc_time
        
        stats = self.get_memory_stats()
        
        should_gc = (
            force or
            time_since_gc > self._gc_interval or
            stats.rss_mb > self.gc_threshold_mb or
            stats.is_warning
        )
        
        if should_gc:
            logger.info(f"Triggering GC (Memory: {stats.rss_mb:.1f}MB)")
            
            # Full collection
            collected = gc.collect(2)
            
            self._last_gc_time = current_time
            
            # Get stats after GC
            new_stats = self.get_memory_stats()
            freed_mb = stats.rss_mb - new_stats.rss_mb
            
            logger.info(
                f"GC completed: collected {collected} objects, "
                f"freed {freed_mb:.1f}MB"
            )
            
            return True
        
        return False
    
    def estimate_object_size(self, obj: Any) -> int:
        """Estimate object size in bytes."""
        if NUMPY_AVAILABLE and isinstance(obj, np.ndarray):
            return obj.nbytes
        
        if hasattr(obj, '__sizeof__'):
            return sys.getsizeof(obj)
        
        # Rough estimation for complex objects
        try:
            import pickle
            return len(pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL))
        except:
            return 0
    
    def should_spill(self, obj: Any, name: str = None) -> bool:
        """Determine if object should be spilled to disk."""
        obj_size_mb = self.estimate_object_size(obj) / (1024 * 1024)
        stats = self.get_memory_stats()
        
        return (
            obj_size_mb > 50 or  # Large object
            stats.rss_mb + obj_size_mb > self.spill_threshold_mb or
            stats.is_warning
        )
    
    def spill_to_disk(self, obj: Any, name: str) -> Optional[str]:
        """
        Spill large object to disk.
        Returns file path if successful.
        """
        import pickle
        import os
        import hashlib
        
        # Generate unique filename
        obj_hash = hashlib.md5(name.encode()).hexdigest()[:8]
        filepath = os.path.join(
            self.cache_dir,
            f"spill_{name}_{obj_hash}.pkl"
        )
        
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            self._spilled_objects[name] = filepath
            logger.info(f"Spilled {name} to disk: {filepath}")
            
            # Create weak reference to track when object is deleted
            if hasattr(obj, '__weakref__'):
                self._weak_refs[name] = weakref.ref(obj, 
                    lambda ref, n=name: self._on_object_deleted(n))
            
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to spill {name}: {e}")
            return None
    
    def load_from_disk(self, name: str) -> Optional[Any]:
        """Load spilled object from disk."""
        if name not in self._spilled_objects:
            return None
        
        filepath = self._spilled_objects[name]
        
        try:
            import pickle
            with open(filepath, 'rb') as f:
                obj = pickle.load(f)
            
            logger.info(f"Loaded {name} from disk: {filepath}")
            return obj
            
        except Exception as e:
            logger.error(f"Failed to load {name}: {e}")
            return None
    
    def _on_object_deleted(self, name: str):
        """Callback when spilled object is deleted."""
        if name in self._spilled_objects:
            import os
            filepath = self._spilled_objects[name]
            try:
                os.remove(filepath)
                del self._spilled_objects[name]
                logger.debug(f"Cleaned up spilled file: {filepath}")
            except:
                pass
    
    def get_memory_report(self) -> Dict[str, Any]:
        """Generate comprehensive memory report."""
        stats = self.get_memory_stats()
        
        report = {
            'current': {
                'rss_mb': stats.rss_mb,
                'vms_mb': stats.vms_mb,
                'percent': stats.percent,
                'available_mb': stats.available_mb,
                'is_critical': stats.is_critical,
                'is_warning': stats.is_warning
            },
            'limits': {
                'memory_limit_mb': self.memory_limit_mb,
                'gc_threshold_mb': self.gc_threshold_mb,
                'spill_threshold_mb': self.spill_threshold_mb
            },
            'gc': {
                'stats': stats.gc_stats,
                'last_gc_time': self._last_gc_time,
                'gc_interval': self._gc_interval
            },
            'spilled': {
                'count': len(self._spilled_objects),
                'objects': list(self._spilled_objects.keys())
            },
            'history': {
                'samples': len(self._memory_history),
                'avg_rss_mb': sum(s.rss_mb for s in self._memory_history) / len(self._memory_history)
                    if self._memory_history else 0
            }
        }
        
        return report
    
    def optimize_memory(self) -> Dict[str, Any]:
        """
        Run full memory optimization routine.
        Returns optimization results.
        """
        logger.info("Starting memory optimization...")
        
        initial_stats = self.get_memory_stats()
        
        # Step 1: Clear weak references
        dead_refs = [
            name for name, ref in self._weak_refs.items()
            if ref() is None
        ]
        for name in dead_refs:
            del self._weak_refs[name]
            self._on_object_deleted(name)
        
        # Step 2: Force garbage collection
        self.trigger_gc_if_needed(force=True)
        
        # Step 3: Compact memory (if possible)
        if hasattr(gc, 'freeze'):
            gc.freeze()  # Freeze tracked objects
            gc.collect()
            gc.unfreeze()
        
        final_stats = self.get_memory_stats()
        
        results = {
            'freed_mb': initial_stats.rss_mb - final_stats.rss_mb,
            'cleaned_refs': len(dead_refs),
            'initial_mb': initial_stats.rss_mb,
            'final_mb': final_stats.rss_mb,
            'optimization_time': time.time() - initial_stats.timestamp
        }
        
        logger.info(f"Memory optimization completed: freed {results['freed_mb']:.1f}MB")
        
        return results