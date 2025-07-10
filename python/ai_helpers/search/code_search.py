"""
코드 내용 검색 전문 모듈

파일 내용에서 패턴을 검색하는 기능을 제공합니다.
"""

import os
import time
import fnmatch
from typing import List, Optional, Union, Pattern
from pathlib import Path

from ..helper_result import HelperResult
from .types import SearchMatch
from .core import (
    normalize_path,
    should_ignore,
    compile_regex,
    read_file_lines,
    extract_match_context,
    filter_hidden_items,
    DEFAULT_IGNORE_PATTERNS
)


def search_code(
    path: Union[str, Path] = '.',
    pattern: str = '',
    file_pattern: str = '*',
    case_sensitive: bool = False,
    whole_word: bool = False,
    max_results: int = 100,
    context_lines: int = 2,
    include_context: bool = False,
    ignore_patterns: Optional[List[str]] = None
) -> HelperResult:
    """코드 내용 검색
    
    Args:
        path: 검색 시작 경로
        pattern: 정규식 패턴
        file_pattern: 파일명 패턴 (fnmatch 형식)
        case_sensitive: 대소문자 구분 여부
        whole_word: 단어 경계 매칭 여부
        max_results: 최대 결과 수
        context_lines: 컨텍스트 라인 수
        include_context: 컨텍스트 포함 여부
        ignore_patterns: 무시할 패턴 리스트
        
    Returns:
        HelperResult with data as list of SearchMatch
    """
    start_time = time.time()
    results = []
    searched_files = 0
    
    # 경로 정규화
    search_path = normalize_path(path)
    if not search_path.exists():
        return HelperResult.fail(f"경로가 존재하지 않음: {search_path}")
    
    # 정규식 컴파일
    regex = compile_regex(pattern, case_sensitive, whole_word)
    if regex is None:
        return HelperResult.fail(f'잘못된 정규식 패턴: {pattern}')
    
    # 무시 패턴 설정
    if ignore_patterns is None:
        ignore_patterns = DEFAULT_IGNORE_PATTERNS
    
    try:
        for root, dirs, files in os.walk(search_path):
            root_path = Path(root)
            
            # 숨김 디렉토리 제외
            dirs[:] = filter_hidden_items(dirs)
            
            # 무시 패턴 체크
            dirs[:] = [d for d in dirs if not should_ignore(root_path / d, ignore_patterns)]
            
            for filename in files:
                if fnmatch.fnmatch(filename, file_pattern):
                    file_path = root_path / filename
                    
                    if should_ignore(file_path, ignore_patterns):
                        continue
                    
                    searched_files += 1
                    
                    # 파일 읽기
                    lines = read_file_lines(file_path)
                    if lines is None:
                        continue
                    
                    # 라인별 검색
                    for i, line in enumerate(lines):
                        match = regex.search(line)
                        if match:
                            # 매칭된 텍스트 추출
                            matched_text = match.group(0)
                            
                            result_entry = {
                                'line_number': i + 1,
                                'code_line': line.rstrip(),
                                'matched_text': matched_text,
                                'file_path': str(file_path)
                            }
                            
                            # 컨텍스트 추가
                            if include_context:
                                context_info = extract_match_context(lines, i, context_lines)
                                result_entry.update(context_info)
                            
                            results.append(result_entry)
                            
                            if len(results) >= max_results:
                                break
                    
                    if len(results) >= max_results:
                        break
            
            if len(results) >= max_results:
                break
                
    except Exception as e:
        return HelperResult.fail(f'코드 검색 실패: {str(e)}')
    
    # 결과 반환
    result = HelperResult.success(results)
    result.metadata = {
        'searched_files': searched_files,
        'execution_time': time.time() - start_time,
        'pattern': pattern,
        'file_pattern': file_pattern
    }
    
    return result


# 특화된 검색 함수들

def find_class(
    class_name: str,
    path: Union[str, Path] = '.',
    **kwargs
) -> HelperResult:
    """클래스 정의 찾기
    
    Args:
        class_name: 찾을 클래스 이름
        path: 검색 경로
        **kwargs: search_code에 전달할 추가 인자
        
    Returns:
        HelperResult with class definition locations
    """
    pattern = rf"class\s+{class_name}\s*[\(:]"
    return search_code(path, pattern, '*.py', **kwargs)


def find_function(
    func_name: str,
    path: Union[str, Path] = '.',
    **kwargs
) -> HelperResult:
    """함수 정의 찾기
    
    Args:
        func_name: 찾을 함수 이름
        path: 검색 경로
        **kwargs: search_code에 전달할 추가 인자
        
    Returns:
        HelperResult with function definition locations
    """
    pattern = rf"def\s+{func_name}\s*\("
    return search_code(path, pattern, '*.py', **kwargs)


def find_import(
    module_name: str,
    path: Union[str, Path] = '.',
    **kwargs
) -> HelperResult:
    """import 문 찾기
    
    Args:
        module_name: 찾을 모듈 이름
        path: 검색 경로
        **kwargs: search_code에 전달할 추가 인자
        
    Returns:
        HelperResult with import statement locations
    """
    pattern = rf"(from\s+{module_name}|import\s+{module_name})"
    return search_code(path, pattern, '*.py', **kwargs)


def find_method(
    method_name: str,
    class_name: Optional[str] = None,
    path: Union[str, Path] = '.',
    **kwargs
) -> HelperResult:
    """메서드 정의 찾기
    
    Args:
        method_name: 찾을 메서드 이름
        class_name: 특정 클래스 내에서만 찾을 경우
        path: 검색 경로
        **kwargs: search_code에 전달할 추가 인자
        
    Returns:
        HelperResult with method definition locations
    """
    if class_name:
        # 특정 클래스의 메서드 찾기 (더 복잡한 로직 필요)
        # 일단 간단하게 구현
        pattern = rf"def\s+{method_name}\s*\("
        results = search_code(path, pattern, '*.py', include_context=True, **kwargs)
        
        # TODO: 클래스 컨텍스트 확인 로직 추가
        return results
    else:
        # 모든 메서드 찾기
        pattern = rf"def\s+{method_name}\s*\("
        return search_code(path, pattern, '*.py', **kwargs)


def find_variable(
    var_name: str,
    path: Union[str, Path] = '.',
    assignment_only: bool = True,
    **kwargs
) -> HelperResult:
    """변수 사용/할당 찾기
    
    Args:
        var_name: 찾을 변수 이름
        path: 검색 경로
        assignment_only: 할당문만 찾을지 여부
        **kwargs: search_code에 전달할 추가 인자
        
    Returns:
        HelperResult with variable usage/assignment locations
    """
    if assignment_only:
        pattern = rf"{var_name}\s*="
    else:
        pattern = rf"\b{var_name}\b"
    
    return search_code(path, pattern, '*.py', whole_word=True, **kwargs)
