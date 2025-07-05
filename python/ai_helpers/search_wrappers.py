"""
Search Wrappers - 검색 관련 헬퍼 함수들의 편의 래퍼
"""

from .helper_result import HelperResult
from .search import search_code_content, search_files_advanced

def search_code(pattern: str, path: str = '.', file_pattern: str = '*.py'):
    """코드 내용 검색 편의 함수

    Args:
        pattern: 검색할 패턴 (정규식 지원)
        path: 검색 경로 (기본: 현재 디렉토리)
        file_pattern: 파일 패턴 (기본: *.py)

    Returns:
        HelperResult: 검색 결과
    """
    return search_code_content(path, pattern, file_pattern)

def find_class(class_name: str, path: str = '.'):
    """클래스 정의 찾기

    Args:
        class_name: 찾을 클래스 이름
        path: 검색 경로

    Returns:
        HelperResult: 클래스 정의 위치
    """
    pattern = f"class\\s+{class_name}\\s*[\\(:]"
    return search_code_content(path, pattern, '*.py')

def find_function(func_name: str, path: str = '.'):
    """함수 정의 찾기

    Args:
        func_name: 찾을 함수 이름
        path: 검색 경로

    Returns:
        HelperResult: 함수 정의 위치
    """
    pattern = f"def\\s+{func_name}\\s*\\("
    return search_code_content(path, pattern, '*.py')

def find_import(module_name: str, path: str = '.'):
    """import 문 찾기

    Args:
        module_name: 찾을 모듈 이름
        path: 검색 경로

    Returns:
        HelperResult: import 문 위치
    """
    pattern = f"(from\\s+{module_name}|import\\s+{module_name})"
    return search_code_content(path, pattern, '*.py')

__all__ = ['search_code', 'find_class', 'find_function', 'find_import']
