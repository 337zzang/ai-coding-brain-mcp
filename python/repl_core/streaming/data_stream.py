"""
Core streaming data structures for processing large datasets.
"""

import asyncio
from typing import (
    Generator, AsyncGenerator, Any, Optional, Callable,
    Union, List, Dict, Tuple
)
from dataclasses import dataclass
from collections import deque
import logging
import time

logger = logging.getLogger(__name__)


@dataclass
class StreamMetadata:
    """Metadata for streaming operations."""
    total_items: Optional[int] = None
    processed_items: int = 0
    bytes_processed: int = 0
    start_time: float = 0.0
    chunk_size: int = 10000
    
    @property
    def progress(self) -> float:
        """Get progress percentage (0.0 to 1.0)."""
        if self.total_items and self.total_items > 0:
            return min(1.0, self.processed_items / self.total_items)
        return 0.0
    
    @property
    def throughput(self) -> float:
        """Get throughput in items per second."""
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            return self.processed_items / elapsed
        return 0.0


class DataStream:
    """
    Lazy, memory-efficient data stream for processing large datasets.
    
    Supports:
    - Lazy evaluation
    - Chunked processing
    - Backpressure handling
    - Progress tracking
    - Cancellation
    """
    
    def __init__(
        self,
        source: Union[Generator, AsyncGenerator, Callable],
        metadata: Optional[StreamMetadata] = None,
        buffer_size: int = 100
    ):
        self.source = source
        self.metadata = metadata or StreamMetadata()
        self.buffer_size = buffer_size
        self._buffer = deque(maxlen=buffer_size)
        self._transforms: List[Callable] = []
        self._cancelled = False
        self._exhausted = False
        
    @classmethod
    def from_iterable(cls, iterable, chunk_size: int = 10000):
        """Create stream from any iterable."""
        def generator():
            for item in iterable:
                yield item
        
        metadata = StreamMetadata(
            total_items=len(iterable) if hasattr(iterable, '__len__') else None,
            chunk_size=chunk_size
        )
        return cls(generator(), metadata)
    
    @classmethod
    def from_file(cls, filepath: str, mode: str = 'r', chunk_size: int = 8192):
        """Create stream from file."""
        def file_generator():
            with open(filepath, mode) as f:
                if mode == 'rb':
                    while chunk := f.read(chunk_size):
                        yield chunk
                else:
                    for line in f:
                        yield line.rstrip('\n')
        
        import os
        file_size = os.path.getsize(filepath)
        metadata = StreamMetadata(
            total_items=file_size // chunk_size if mode == 'rb' else None,
            chunk_size=chunk_size
        )
        return cls(file_generator(), metadata)
    
    @classmethod
    def from_csv(cls, filepath: str, chunk_size: int = 10000):
        """Create stream from CSV file."""
        try:
            import pandas as pd
            
            def csv_generator():
                for chunk in pd.read_csv(filepath, chunksize=chunk_size):
                    yield chunk
            
            # Get total rows for progress tracking
            with open(filepath, 'r') as f:
                total_rows = sum(1 for _ in f) - 1  # Subtract header
            
            metadata = StreamMetadata(
                total_items=total_rows,
                chunk_size=chunk_size
            )
            return cls(csv_generator(), metadata)
            
        except ImportError:
            # Fallback to basic CSV reading
            import csv
            
            def csv_generator():
                with open(filepath, 'r', newline='') as f:
                    reader = csv.DictReader(f)
                    batch = []
                    for row in reader:
                        batch.append(row)
                        if len(batch) >= chunk_size:
                            yield batch
                            batch = []
                    if batch:
                        yield batch
            
            return cls(csv_generator())
    
    def map(self, func: Callable[[Any], Any]) -> 'DataStream':
        """Apply transformation to each element."""
        def mapped_generator():
            for item in self._iterate():
                if self._cancelled:
                    break
                yield func(item)
        
        new_stream = DataStream(mapped_generator(), self.metadata)
        new_stream._transforms = self._transforms + [('map', func)]
        return new_stream
    
    def filter(self, predicate: Callable[[Any], bool]) -> 'DataStream':
        """Filter elements based on predicate."""
        def filtered_generator():
            for item in self._iterate():
                if self._cancelled:
                    break
                if predicate(item):
                    yield item
        
        new_stream = DataStream(filtered_generator(), self.metadata)
        new_stream._transforms = self._transforms + [('filter', predicate)]
        return new_stream
    
    def batch(self, batch_size: int) -> 'DataStream':
        """Group elements into batches."""
        def batched_generator():
            batch = []
            for item in self._iterate():
                if self._cancelled:
                    break
                batch.append(item)
                if len(batch) >= batch_size:
                    yield batch
                    batch = []
            if batch and not self._cancelled:
                yield batch
        
        new_stream = DataStream(batched_generator(), self.metadata)
        new_stream._transforms = self._transforms + [('batch', batch_size)]
        return new_stream
    
    def take(self, n: int) -> 'DataStream':
        """Take first n elements."""
        def take_generator():
            count = 0
            for item in self._iterate():
                if count >= n or self._cancelled:
                    break
                yield item
                count += 1
        
        new_stream = DataStream(take_generator(), self.metadata)
        new_stream._transforms = self._transforms + [('take', n)]
        return new_stream
    
    def skip(self, n: int) -> 'DataStream':
        """Skip first n elements."""
        def skip_generator():
            count = 0
            for item in self._iterate():
                if self._cancelled:
                    break
                if count >= n:
                    yield item
                else:
                    count += 1
        
        new_stream = DataStream(skip_generator(), self.metadata)
        new_stream._transforms = self._transforms + [('skip', n)]
        return new_stream
    
    def _iterate(self) -> Generator:
        """Internal iteration with metadata tracking."""
        self.metadata.start_time = time.time()
        
        if callable(self.source) and not hasattr(self.source, '__next__'):
            source = self.source()
        else:
            source = self.source
        
        for item in source:
            if self._cancelled:
                break
            
            self.metadata.processed_items += 1
            
            # Estimate bytes processed
            if hasattr(item, '__sizeof__'):
                self.metadata.bytes_processed += item.__sizeof__()
            
            # Apply backpressure if buffer is full
            while len(self._buffer) >= self.buffer_size and not self._cancelled:
                time.sleep(0.001)  # Small delay
            
            self._buffer.append(item)
            yield item
        
        self._exhausted = True
    
    def collect(self, max_items: Optional[int] = None) -> List[Any]:
        """
        Materialize stream into a list.
        Warning: This loads all data into memory!
        """
        result = []
        count = 0
        
        for item in self._iterate():
            if self._cancelled:
                break
            result.append(item)
            count += 1
            if max_items and count >= max_items:
                break
        
        return result
    
    def to_pandas(self, max_rows: Optional[int] = None):
        """Convert stream to pandas DataFrame."""
        try:
            import pandas as pd
            data = self.collect(max_items=max_rows)
            return pd.DataFrame(data)
        except ImportError:
            raise ImportError("pandas is required for to_pandas()")
    
    def save_to_file(self, filepath: str, format: str = 'json') -> bool:
        """Save stream to file."""
        try:
            if format == 'json':
                import json
                with open(filepath, 'w') as f:
                    json.dump(self.collect(), f)
            
            elif format == 'csv':
                import csv
                data = self.collect()
                if data:
                    with open(filepath, 'w', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=data[0].keys())
                        writer.writeheader()
                        writer.writerows(data)
            
            elif format == 'parquet':
                df = self.to_pandas()
                df.to_parquet(filepath)
            
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save stream: {e}")
            return False
    
    def cancel(self):
        """Cancel streaming operation."""
        self._cancelled = True
    
    @property
    def is_cancelled(self) -> bool:
        """Check if stream is cancelled."""
        return self._cancelled
    
    @property
    def is_exhausted(self) -> bool:
        """Check if stream is exhausted."""
        return self._exhausted
    
    def get_progress(self) -> Dict[str, Any]:
        """Get streaming progress information."""
        return {
            'progress': self.metadata.progress,
            'processed_items': self.metadata.processed_items,
            'bytes_processed': self.metadata.bytes_processed,
            'throughput': self.metadata.throughput,
            'buffer_usage': len(self._buffer) / self.buffer_size,
            'is_cancelled': self._cancelled,
            'is_exhausted': self._exhausted
        }


class StreamProcessor:
    """
    Advanced stream processor with parallel execution support.
    """
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self._executor = None
        
    async def process_parallel(
        self,
        stream: DataStream,
        func: Callable,
        batch_size: int = 100
    ) -> AsyncGenerator[Any, None]:
        """Process stream in parallel with async workers."""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Create batches
            batched_stream = stream.batch(batch_size)
            
            # Process batches in parallel
            for batch in batched_stream._iterate():
                if stream.is_cancelled:
                    break
                
                # Submit batch processing to executor
                loop = asyncio.get_event_loop()
                futures = [
                    loop.run_in_executor(executor, func, item)
                    for item in batch
                ]
                
                # Yield results as they complete
                for future in asyncio.as_completed(futures):
                    result = await future
                    yield result
    
    def process_windowed(
        self,
        stream: DataStream,
        window_size: int,
        func: Callable[[List], Any]
    ) -> Generator[Any, None, None]:
        """Process stream with sliding window."""
        window = deque(maxlen=window_size)
        
        for item in stream._iterate():
            if stream.is_cancelled:
                break
            
            window.append(item)
            if len(window) == window_size:
                yield func(list(window))
    
    def process_grouped(
        self,
        stream: DataStream,
        key_func: Callable[[Any], Any],
        agg_func: Callable[[List], Any]
    ) -> Dict[Any, Any]:
        """Group stream by key and aggregate."""
        groups = {}
        
        for item in stream._iterate():
            if stream.is_cancelled:
                break
            
            key = key_func(item)
            if key not in groups:
                groups[key] = []
            groups[key].append(item)
        
        # Apply aggregation
        return {
            key: agg_func(items)
            for key, items in groups.items()
        }