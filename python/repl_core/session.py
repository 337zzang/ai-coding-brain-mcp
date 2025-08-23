"""
Enhanced REPL session with notebook-like capabilities for large-scale data processing.
"""

import sys
import os
import json
import time
import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
import io
import traceback
from contextlib import contextmanager

from .base import BaseSession, ExecutionResult, ExecutionMode
from .memory_manager import MemoryManager
from .cache.tiered_cache import TieredCache
from .streaming.data_stream import DataStream, StreamProcessor

logger = logging.getLogger(__name__)


class EnhancedREPLSession(BaseSession):
    """
    Enhanced REPL session with enterprise-grade features.
    
    Features:
    - Streaming data processing
    - Multi-tier caching
    - Memory management
    - Progressive output rendering
    - DataFrame/array lazy loading
    - Automatic spill-to-disk
    """
    
    def __init__(
        self,
        memory_limit_mb: float = 1000,
        cache_dir: str = ".repl_cache",
        enable_streaming: bool = True,
        enable_caching: bool = True,
        chunk_size: int = 10000
    ):
        self.memory_limit_mb = memory_limit_mb
        self.cache_dir = cache_dir
        self.enable_streaming = enable_streaming
        self.enable_caching = enable_caching
        self.chunk_size = chunk_size
        
        # Initialize components
        self.memory_manager = MemoryManager(
            memory_limit_mb=memory_limit_mb,
            cache_dir=cache_dir
        )
        
        self.cache = TieredCache(
            cache_dir=cache_dir
        ) if enable_caching else None
        
        self.stream_processor = StreamProcessor(max_workers=4)
        
        # Session namespace
        self.namespace = {}
        self._init_namespace()
        
        # Execution tracking
        self.execution_count = 0
        self.execution_history = []
        
        logger.info(
            f"Enhanced REPL initialized: memory_limit={memory_limit_mb}MB, "
            f"streaming={enable_streaming}, caching={enable_caching}"
        )
    
    def _init_namespace(self):
        """Initialize session namespace with helpers."""
        import builtins
        
        self.namespace.update({
            '__name__': '__main__',
            '__builtins__': builtins,
            'DataStream': DataStream,
            'load_csv': self._create_csv_loader(),
            'load_json': self._create_json_loader(),
            'load_parquet': self._create_parquet_loader(),
            'memory_info': self.get_memory_report,
            'cache_info': self.get_cache_stats,
            'clear_cache': self.clear_cache,
            'process_large': self._process_large_data
        })
    
    def _create_csv_loader(self):
        """Create lazy CSV loader function."""
        def load_csv(filepath: str, streaming: bool = True, **kwargs):
            if streaming and self.enable_streaming:
                return DataStream.from_csv(filepath, chunk_size=self.chunk_size)
            else:
                try:
                    import pandas as pd
                    return pd.read_csv(filepath, **kwargs)
                except ImportError:
                    import csv
                    with open(filepath, 'r') as f:
                        return list(csv.DictReader(f))
        
        return load_csv
    
    def _create_json_loader(self):
        """Create lazy JSON loader function."""
        def load_json(filepath: str, streaming: bool = False):
            if streaming and self.enable_streaming:
                def json_generator():
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            for item in data:
                                yield item
                        else:
                            yield data
                
                return DataStream(json_generator())
            else:
                with open(filepath, 'r') as f:
                    return json.load(f)
        
        return load_json
    
    def _create_parquet_loader(self):
        """Create lazy Parquet loader function."""
        def load_parquet(filepath: str, streaming: bool = True):
            try:
                import pyarrow.parquet as pq
                
                if streaming and self.enable_streaming:
                    def parquet_generator():
                        parquet_file = pq.ParquetFile(filepath)
                        for batch in parquet_file.iter_batches(batch_size=self.chunk_size):
                            yield batch.to_pandas()
                    
                    return DataStream(parquet_generator())
                else:
                    return pq.read_table(filepath).to_pandas()
                    
            except ImportError:
                raise ImportError("pyarrow is required for Parquet support")
        
        return load_parquet
    
    def _process_large_data(self, data: Any, operation: str, **kwargs):
        """
        Process large data with automatic optimization.
        
        Examples:
            process_large(df, 'filter', lambda x: x['value'] > 100)
            process_large(df, 'groupby', column='category')
            process_large(df, 'sort', by='timestamp')
        """
        # Check if we should use streaming
        size_mb = self.memory_manager.estimate_object_size(data) / (1024 * 1024)
        
        if size_mb > 100 or self.memory_manager.get_memory_stats().is_warning:
            # Use streaming for large data or under memory pressure
            logger.info(f"Using streaming for {operation} (size: {size_mb:.1f}MB)")
            
            if not isinstance(data, DataStream):
                # Convert to stream
                data = DataStream.from_iterable(data, chunk_size=self.chunk_size)
            
            # Apply operation
            if operation == 'filter':
                predicate = kwargs.get('predicate')
                return data.filter(predicate)
            elif operation == 'map':
                func = kwargs.get('func')
                return data.map(func)
            elif operation == 'batch':
                batch_size = kwargs.get('size', self.chunk_size)
                return data.batch(batch_size)
            else:
                raise ValueError(f"Unsupported streaming operation: {operation}")
        
        else:
            # Process in memory for small data
            logger.info(f"Processing {operation} in memory (size: {size_mb:.1f}MB)")
            
            if operation == 'filter':
                predicate = kwargs.get('predicate')
                return [x for x in data if predicate(x)]
            elif operation == 'map':
                func = kwargs.get('func')
                return [func(x) for x in data]
            else:
                return data
    
    def execute(self, code: str) -> ExecutionResult:
        """Execute code with automatic optimization."""
        self.execution_count += 1
        start_time = time.perf_counter()
        
        # Check memory before execution
        under_pressure, stats = self.memory_manager.check_memory_pressure()
        if under_pressure:
            logger.warning(f"Memory pressure detected: {stats.rss_mb:.1f}MB")
            self.memory_manager.trigger_gc_if_needed(force=True)
        
        # Determine execution mode
        mode = self._determine_execution_mode(code)
        
        result = ExecutionResult(
            success=True,
            execution_mode=mode,
            memory_usage_mb=stats.rss_mb
        )
        
        try:
            # Capture output
            with self._capture_output() as (stdout, stderr):
                # Execute code
                if mode == ExecutionMode.STREAMING:
                    exec_result = self._execute_streaming(code)
                else:
                    exec_result = self._execute_immediate(code)
                
                result.result = exec_result
            
            result.stdout = stdout.getvalue()
            result.stderr = stderr.getvalue()
            
        except Exception as e:
            result.success = False
            result.stderr = f"Error: {type(e).__name__}: {str(e)}\n"
            result.stderr += traceback.format_exc()
        
        # Post-execution cleanup
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        result.execution_time_ms = elapsed_ms
        
        # Update history
        self.execution_history.append({
            'count': self.execution_count,
            'code_preview': code[:100],
            'success': result.success,
            'mode': mode.value,
            'elapsed_ms': elapsed_ms,
            'memory_mb': result.memory_usage_mb
        })
        
        # Trim history if too large
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-500:]
        
        # Check if we need to spill variables to disk
        self._check_and_spill_variables()
        
        return result
    
    def _determine_execution_mode(self, code: str) -> ExecutionMode:
        """Determine optimal execution mode based on code analysis."""
        # Simple heuristics - can be enhanced with AST analysis
        streaming_keywords = ['DataStream', 'load_csv', 'load_parquet', 'process_large']
        
        for keyword in streaming_keywords:
            if keyword in code:
                return ExecutionMode.STREAMING
        
        # Check for large data operations
        if any(op in code for op in ['read_csv', 'read_parquet', 'read_json']):
            # Check file size if possible
            import re
            file_match = re.search(r'["\']([^"\']+\.(csv|parquet|json))["\']', code)
            if file_match:
                filepath = file_match.group(1)
                if os.path.exists(filepath):
                    size_mb = os.path.getsize(filepath) / (1024 * 1024)
                    if size_mb > 100:
                        return ExecutionMode.STREAMING
        
        return ExecutionMode.IMMEDIATE
    
    def _execute_immediate(self, code: str) -> Any:
        """Execute code immediately in memory."""
        exec(code, self.namespace)
        return None
    
    def _execute_streaming(self, code: str) -> Any:
        """Execute code with streaming optimizations."""
        # Inject streaming helpers into namespace
        self.namespace['_streaming_mode'] = True
        
        try:
            exec(code, self.namespace)
        finally:
            self.namespace.pop('_streaming_mode', None)
        
        return None
    
    def _check_and_spill_variables(self):
        """Check variables and spill large ones to disk."""
        if not self.enable_caching:
            return
        
        for name, value in list(self.namespace.items()):
            if name.startswith('_') or name in ['__builtins__', '__name__']:
                continue
            
            if self.memory_manager.should_spill(value, name):
                # Cache the variable
                cache_key = f"var_{name}"
                if self.cache.put(cache_key, value):
                    # Replace with a lazy proxy
                    self.namespace[name] = LazyVariable(cache_key, self.cache)
                    logger.info(f"Spilled variable '{name}' to cache")
    
    @contextmanager
    def _capture_output(self):
        """Capture stdout and stderr."""
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        try:
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture
            yield stdout_capture, stderr_capture
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
    
    def get_variable(self, name: str) -> Any:
        """Get variable from namespace."""
        value = self.namespace.get(name)
        
        # Check if it's a lazy variable
        if isinstance(value, LazyVariable):
            return value.get()
        
        return value
    
    def set_variable(self, name: str, value: Any) -> None:
        """Set variable in namespace."""
        # Check if we should cache it
        if self.enable_caching and self.memory_manager.should_spill(value, name):
            cache_key = f"var_{name}"
            if self.cache.put(cache_key, value):
                self.namespace[name] = LazyVariable(cache_key, self.cache)
                return
        
        self.namespace[name] = value
    
    def clear_session(self) -> None:
        """Clear session state."""
        # Keep essential items
        essential = ['__name__', '__builtins__', 'DataStream', 
                    'load_csv', 'load_json', 'load_parquet',
                    'memory_info', 'cache_info', 'clear_cache',
                    'process_large']
        
        # Clear namespace
        for key in list(self.namespace.keys()):
            if key not in essential:
                del self.namespace[key]
        
        # Clear cache
        if self.cache:
            self.cache.clear()
        
        # Force garbage collection
        self.memory_manager.trigger_gc_if_needed(force=True)
        
        logger.info("Session cleared")
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        return self.memory_manager.get_memory_stats().rss_mb
    
    def get_memory_report(self) -> Dict[str, Any]:
        """Get detailed memory report."""
        return self.memory_manager.get_memory_report()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if self.cache:
            return self.cache.get_stats()
        return {}
    
    def clear_cache(self) -> None:
        """Clear cache."""
        if self.cache:
            self.cache.clear()
            logger.info("Cache cleared")


class LazyVariable:
    """
    Lazy variable that loads from cache on access.
    """
    
    def __init__(self, cache_key: str, cache: TieredCache):
        self.cache_key = cache_key
        self.cache = cache
        self._loaded = False
        self._value = None
    
    def get(self):
        """Load and return value."""
        if not self._loaded:
            self._value = self.cache.get(self.cache_key)
            self._loaded = True
        return self._value
    
    def __repr__(self):
        return f"<LazyVariable: {self.cache_key}>"
    
    def __str__(self):
        return f"LazyVariable({self.cache_key})"
    
    # Proxy common operations
    def __getattr__(self, name):
        return getattr(self.get(), name)
    
    def __getitem__(self, key):
        return self.get()[key]
    
    def __len__(self):
        return len(self.get())
    
    def __iter__(self):
        return iter(self.get())