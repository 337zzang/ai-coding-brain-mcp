"""
테스트용 헬퍼 모듈 (REPL 최적화 테스트)
"""
from typing import Any, Optional, List
from .wrappers import HelperResult, safe_execution, ensure_response

@safe_execution
def test_read_file(filepath: str) -> dict:
    """파일 읽기 테스트 함수"""
    # 간단한 시뮬레이션
    if filepath == "test.txt":
        return {'ok': True, 'data': 'Test file content', 'path': filepath}
    else:
        raise FileNotFoundError(f"File not found: {filepath}")

@safe_execution
def test_search_files(pattern: str, path: str = ".") -> dict:
    """파일 검색 테스트 함수"""
    # 간단한 시뮬레이션
    if pattern == "*.py":
        files = ['main.py', 'utils.py', 'test.py']
    else:
        files = []

    return {
        'ok': True,
        'data': files,
        'pattern': pattern,
        'path': path,
        'count': len(files)
    }

@safe_execution
def test_write_file(filepath: str, content: str) -> dict:
    """파일 쓰기 테스트 함수"""
    # 성공 시뮬레이션 (data가 None)
    return {'ok': True, 'data': None, 'path': filepath, 'bytes_written': len(content)}

# safe_execution 없이 직접 HelperResult 반환하는 함수
def test_direct_helper_result(value: Any) -> HelperResult:
    """HelperResult를 직접 반환하는 테스트"""
    if value is None:
        return ensure_response(None, error="Value cannot be None")
    return ensure_response(value, metadata="direct_test")
