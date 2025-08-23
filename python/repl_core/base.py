"""
Base classes and interfaces for REPL Core components.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Generator, AsyncGenerator, Union
from dataclasses import dataclass
from enum import Enum
import asyncio


class ExecutionMode(Enum):
    """Execution modes for different processing strategies."""
    IMMEDIATE = "immediate"      # Execute immediately in memory
    STREAMING = "streaming"       # Stream processing for large data
    LAZY = "lazy"                # Lazy evaluation with DAG
    DISTRIBUTED = "distributed"   # Distributed processing (future)


@dataclass
class ExecutionResult:
    """Result of code execution with metadata."""
    success: bool
    stdout: str = ""
    stderr: str = ""
    result: Any = None
    memory_usage_mb: float = 0.0
    execution_time_ms: float = 0.0
    execution_mode: ExecutionMode = ExecutionMode.IMMEDIATE
    chunks_processed: int = 0
    cached: bool = False
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'success': self.success,
            'stdout': self.stdout,
            'stderr': self.stderr,
            'memory_usage_mb': self.memory_usage_mb,
            'execution_time_ms': self.execution_time_ms,
            'execution_mode': self.execution_mode.value,
            'chunks_processed': self.chunks_processed,
            'cached': self.cached,
            'metadata': self.metadata or {}
        }


class BaseSession(ABC):
    """Abstract base class for REPL sessions."""
    
    @abstractmethod
    def execute(self, code: str) -> ExecutionResult:
        """Execute code and return result."""
        pass
    
    @abstractmethod
    def get_variable(self, name: str) -> Any:
        """Get variable from session namespace."""
        pass
    
    @abstractmethod
    def set_variable(self, name: str, value: Any) -> None:
        """Set variable in session namespace."""
        pass
    
    @abstractmethod
    def clear_session(self) -> None:
        """Clear session state and free memory."""
        pass
    
    @abstractmethod
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        pass


class BaseCache(ABC):
    """Abstract base class for caching systems."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache."""
        pass
    
    @abstractmethod
    def put(self, key: str, value: Any) -> bool:
        """Store value in cache."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all cache entries."""
        pass
    
    @abstractmethod
    def get_size(self) -> int:
        """Get cache size in bytes."""
        pass


class BaseStream(ABC):
    """Abstract base class for streaming data processing."""
    
    @abstractmethod
    def read_chunks(self, chunk_size: int = 10000) -> Generator[Any, None, None]:
        """Read data in chunks."""
        pass
    
    @abstractmethod
    async def read_chunks_async(self, chunk_size: int = 10000) -> AsyncGenerator[Any, None]:
        """Read data in chunks asynchronously."""
        pass
    
    @abstractmethod
    def write_chunk(self, chunk: Any) -> bool:
        """Write a chunk of data."""
        pass
    
    @abstractmethod
    def get_progress(self) -> float:
        """Get processing progress (0.0 to 1.0)."""
        pass
    
    @abstractmethod
    def cancel(self) -> None:
        """Cancel streaming operation."""
        pass


class BaseStorage(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def save(self, key: str, data: Any, compress: bool = False) -> bool:
        """Save data to storage."""
        pass
    
    @abstractmethod
    def load(self, key: str) -> Optional[Any]:
        """Load data from storage."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete data from storage."""
        pass
    
    @abstractmethod
    def list_keys(self, pattern: str = "*") -> list:
        """List keys matching pattern."""
        pass
    
    @abstractmethod
    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage statistics."""
        pass