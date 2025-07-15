"""
검색 기능 - 프로토콜 추적 포함
"""
import os
import re
import glob
from pathlib import Path
from typing import List, Dict, Any, Optional, Pattern
from .core import track_execution

@track_execution
def search_files(
    directory: str = ".", 
    pattern: str = "*", 
    recursive: bool = True
) -> List[str]:
    """파일명 검색"""
    if recursive:
        pattern_path = os.path.join(directory, "**", pattern)
        files = glob.glob(pattern_path, recursive=True)
    else:
        pattern_path = os.path.join(directory, pattern)
        files = glob.glob(pattern_path)

    # 파일만 필터링 (디렉토리 제외)
    return [f for f in files if os.path.isfile(f)]

@track_execution
def search_code(
    directory: str,
    pattern: str,
    file_pattern: str = "*.py",
    case_sensitive: bool = True
) -> List[Dict[str, Any]]:
    """코드 내용 검색"""
    results = []
    regex_flags = 0 if case_sensitive else re.IGNORECASE
    regex = re.compile(pattern, regex_flags)

    # 파일 찾기
    files = search_files(directory, file_pattern, recursive=True)

    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                if regex.search(line):
                    results.append({
                        'file': filepath,
                        'line_number': i + 1,
                        'line': line.rstrip(),
                        'context': get_context_lines(lines, i)
                    })
        except Exception:
            # 읽을 수 없는 파일은 무시
            pass

    return results

def get_context_lines(lines: List[str], index: int, context: int = 2) -> List[str]:
    """주변 컨텍스트 라인 가져오기"""
    start = max(0, index - context)
    end = min(len(lines), index + context + 1)
    return [lines[i].rstrip() for i in range(start, end)]

@track_execution
def find_function(directory: str, function_name: str) -> List[Dict[str, Any]]:
    """함수 정의 찾기"""
    # 정규표현식 특수문자 이스케이프
    escaped_name = re.escape(function_name)
    pattern = rf"def\s+{escaped_name}\s*\("
    return search_code(directory, pattern, "*.py")

@track_execution
def find_class(directory: str, class_name: str) -> List[Dict[str, Any]]:
    """클래스 정의 찾기"""
    # 정규표현식 특수문자 이스케이프
    escaped_name = re.escape(class_name)
    pattern = rf"class\s+{escaped_name}\s*[\(:]"
    return search_code(directory, pattern, "*.py")

@track_execution
def grep(pattern: str, directory: str = ".", file_pattern: str = "*") -> List[Dict[str, Any]]:
    """grep 스타일 검색"""
    return search_code(directory, pattern, file_pattern)

# 사용 가능한 함수 목록
__all__ = [
    'search_files', 'search_code', 
    'find_function', 'find_class', 'grep'
]
