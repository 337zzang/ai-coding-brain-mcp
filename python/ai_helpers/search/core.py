"""
Search 모듈 핵심 유틸리티

공통적으로 사용되는 헬퍼 함수들과 상수들을 정의합니다.
"""

import os
import re
import fnmatch
from typing import List, Pattern, Optional, Set
from pathlib import Path


# 기본 무시 패턴
DEFAULT_IGNORE_PATTERNS = [
    # Python 관련
    "__pycache__", "*.pyc", "*.pyo", "*.pyd", ".Python",
    ".pytest_cache", ".mypy_cache", 
    
    # 가상환경
    ".venv", "venv", "ENV", "env",
    
    # 빌드/배포
    "dist", "build", "*.egg-info", "node_modules",
    
    # 버전 관리
    ".git", ".svn", ".hg",
    
    # IDE/에디터
    ".vscode", ".idea", "*.swp", "*.swo",
    
    # 백업/임시 파일
    "backup", "backups", "*.bak", "*.backup",
    ".mcp_backup_*", "backup_*", "backup_test_suite",
    
    # 테스트
    "test", "tests", "test_*", "*_test",
    
    # 캐시/세션
    ".cache", ".ai_cache", "cache", ".sessions",
    "session_cache",
    
    # 로그
    "logs", "*.log",
    
    # 데이터베이스
    "*.db", "*.sqlite*", "chroma_db",
    
    # 기타
    ".vibe", "output", "tmp", "temp"
]


def compile_regex(pattern: str, case_sensitive: bool = False, 
                  whole_word: bool = False) -> Optional[Pattern]:
    """정규식 패턴 컴파일
    
    Args:
        pattern: 정규식 패턴
        case_sensitive: 대소문자 구분 여부
        whole_word: 단어 경계 매칭 여부
        
    Returns:
        컴파일된 정규식 객체 또는 None (에러 시)
    """
    flags = 0 if case_sensitive else re.IGNORECASE
    
    if whole_word:
        pattern = rf'\b{re.escape(pattern)}\b'
    
    try:
        return re.compile(pattern, flags)
    except re.error:
        return None


def should_ignore(path: Path, ignore_patterns: List[str]) -> bool:
    """경로가 무시 패턴에 매치되는지 확인
    
    Args:
        path: 확인할 경로
        ignore_patterns: 무시 패턴 리스트
        
    Returns:
        무시해야 하면 True
    """
    path_str = str(path)
    path_parts = path.parts
    path_name = path.name
    
    for pattern in ignore_patterns:
        # 와일드카드 패턴 처리
        if '*' in pattern or '?' in pattern:
            if fnmatch.fnmatch(path_name, pattern):
                return True
        else:
            # 정확한 매칭
            if pattern in path_parts or path_name == pattern:
                return True
                
    return False


def normalize_path(path: Union[str, Path]) -> Path:
    """경로 정규화
    
    Args:
        path: 정규화할 경로
        
    Returns:
        정규화된 Path 객체
    """
    return Path(path).resolve()


def get_file_info(file_path: Path) -> dict:
    """파일 정보 가져오기
    
    Args:
        file_path: 파일 경로
        
    Returns:
        파일 정보 딕셔너리
    """
    try:
        stat = file_path.stat()
        return {
            'file_path': str(file_path),
            'file_name': file_path.name,
            'size': stat.st_size,
            'modified': stat.st_mtime
        }
    except:
        return {
            'file_path': str(file_path),
            'file_name': file_path.name,
            'size': 0,
            'modified': 0
        }


def filter_hidden_items(items: List[str], include_hidden: bool = False) -> List[str]:
    """숨김 항목 필터링
    
    Args:
        items: 항목 리스트
        include_hidden: 숨김 항목 포함 여부
        
    Returns:
        필터링된 항목 리스트
    """
    if include_hidden:
        return items
    return [item for item in items if not item.startswith('.')]


def read_file_lines(file_path: Path, encoding: str = 'utf-8') -> Optional[List[str]]:
    """파일을 라인 단위로 읽기
    
    Args:
        file_path: 파일 경로
        encoding: 인코딩
        
    Returns:
        라인 리스트 또는 None (에러 시)
    """
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.readlines()
    except:
        return None


def extract_match_context(lines: List[str], match_index: int, 
                         context_lines: int = 2) -> dict:
    """매치 주변 컨텍스트 추출
    
    Args:
        lines: 전체 라인 리스트
        match_index: 매치된 라인 인덱스 (0-based)
        context_lines: 컨텍스트 라인 수
        
    Returns:
        컨텍스트 정보 딕셔너리
    """
    start = max(0, match_index - context_lines)
    end = min(len(lines), match_index + context_lines + 1)
    
    return {
        'context': [line.rstrip() for line in lines[start:end]],
        'context_start_line': start + 1  # 1-based
    }
