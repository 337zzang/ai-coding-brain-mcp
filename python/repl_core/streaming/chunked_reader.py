"""
Chunked reading and writing for large files.
"""

from typing import Generator, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ChunkedReader:
    """Read large files in chunks."""
    
    def __init__(self, filepath: str, chunk_size: int = 8192):
        self.filepath = filepath
        self.chunk_size = chunk_size
        
    def read_chunks(self) -> Generator[bytes, None, None]:
        """Read file in chunks."""
        with open(self.filepath, 'rb') as f:
            while chunk := f.read(self.chunk_size):
                yield chunk


class ChunkedWriter:
    """Write data in chunks."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        
    def write_chunks(self, chunks: Generator[bytes, None, None]):
        """Write chunks to file."""
        with open(self.filepath, 'wb') as f:
            for chunk in chunks:
                f.write(chunk)