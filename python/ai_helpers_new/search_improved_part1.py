
# search.py 개선 버전 - Part 1: 유틸리티 함수들
import os
import re
import ast
import sys
from pathlib import Path
from typing import Dict, Any, List, Generator, Optional
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

# 바이너리 파일 감지용 상수
NULL_BYTE = b'\x00'

def is_binary_file(file_path: str, sample_size: int = 8192) -> bool:
    """널 바이트로 바이너리 파일 감지"""
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(sample_size)
            return NULL_BYTE in chunk
    except (FileNotFoundError, PermissionError, IOError):
        return True  # 읽기 실패시 바이너리로 간주

# 캐시 관리
_caches = []

def _register_cache(func):
    """캐시된 함수 등록"""
    if hasattr(func, 'cache_clear'):
        _caches.append(func)
    return func

def clear_all_caches():
    """모든 등록된 캐시 클리어"""
    for cache in _caches:
        if hasattr(cache, 'cache_clear'):
            cache.cache_clear()
