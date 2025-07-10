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

def search_code_content(path: str = '.', pattern: str = '', 
                       file_pattern: str = '*', max_results: int = 50,
                       case_sensitive: bool = False, whole_word: bool = False,
                       include_context: bool = False):
    """코드 내용 검색 (추적 포함) - 개선된 버전
    
    Args:
        path: 검색할 경로
        pattern: 검색 패턴 (정규식 지원)
        file_pattern: 파일 패턴 (예: '*.py')
        max_results: 최대 결과 수
        case_sensitive: 대소문자 구분
        whole_word: 단어 단위 검색
        include_context: 컨텍스트 포함 여부 (기본: False)
    
    Returns:
        HelperResult: 검색 결과
            - ok=True일 때 data는 매칭된 라인들의 리스트:
              [
                {
                  'line_number': int,      # 라인 번호
                  'code_line': str,        # 코드 라인 내용
                  'matched_text': str,     # 매칭된 텍스트
                  'file_path': str,        # 파일 경로
                  'context': list (선택)   # include_context=True일 때만
                },
                ...
              ]
            - metadata 속성에 추가 정보:
              - searched_files: 검색한 파일 수
              - execution_time: 실행 시간
    
    Example:
        >>> result = search_code_content(".", "def.*test", "*.py")
        >>> if result.ok:
        ...     for match in result.data:
        ...         print(f"{match['file_path']}:{match['line_number']} - {match['matched_text']}")
    """
    # ----- (1) 추적 -----
    track_file_access('search_code', path)
    
    # ----- (2) SearchHelper 호출 -----
    result = _search_code_content(
        path=path,
        pattern=pattern,
        file_pattern=file_pattern,
        max_results=max_results,
        case_sensitive=case_sensitive,
        whole_word=whole_word,
        include_context=include_context
    )
    
    # ----- (3) 결과에 추적 정보 추가 -----
    if result.ok and result.data:
        for file_result in result.data:
            if 'file_path' in file_result:
                track_file_access('search_code', file_result['file_path'])
    
    return result


def _search_code_content(path: str, pattern: str, file_pattern: str = "*",
                        case_sensitive: bool = False, whole_word: bool = False,
                        max_results: int = 100, context_lines: int = 2, 
                        include_context: bool = False) -> HelperResult:
    """
    코드 내용 검색 내부 구현 - 개선된 버전
    
    Args:
        path: 검색 시작 경로
        pattern: 정규식 패턴
        file_pattern: 파일명 패턴 (fnmatch 형식)
        case_sensitive: 대소문자 구분 여부
        whole_word: 단어 경계 매칭 여부
        max_results: 최대 결과 수
        context_lines: 컨텍스트 라인 수
        include_context: 컨텍스트 포함 여부
    
    Returns:
        HelperResult with data as list of matches:
        [
            {
                'line_number': int,      # 1-based 라인 번호
                'code_line': str,        # 매칭된 라인 (rstrip 적용)
                'matched_text': str,     # 정규식에 매칭된 실제 텍스트
                'file_path': str,        # 절대 경로
                'context': list,         # 선택: 주변 라인들
                'context_start_line': int # 선택: 컨텍스트 시작 라인
            },
            ...
        ]
        
        metadata 속성:
        - searched_files: 검색한 파일 수
        - execution_time: 실행 시간 (초)
    
    Note:
        - 숨김 디렉토리 (.)는 자동으로 제외됨
        - 읽을 수 없는 파일은 무시됨
        - UTF-8 인코딩 가정
    """
    import fnmatch
    import time
    import re
    
    start_time = time.time()
    results = []
    searched_files = 0
    
    # 정규식 컴파일
    flags = 0 if case_sensitive else re.IGNORECASE

    # whole_word 옵션 처리
    if whole_word:
        # 특수문자 이스케이프 후 단어 경계 추가
        pattern = rf'\b{re.escape(pattern)}\b'
    try:
        regex = re.compile(pattern, flags)
    except re.error as e:
        return HelperResult.fail(f'Invalid regex pattern: {e}')
    
    try:
        for root, dirs, files in os.walk(path):
            # 숨김 디렉토리 제외
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for filename in files:
                if fnmatch.fnmatch(filename, file_pattern):
                    file_path = os.path.join(root, filename)
                    searched_files += 1
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            
                        for i, line in enumerate(lines):
                            match = regex.search(line)
                            if match:
                                # 매칭된 텍스트 추출
                                matched_text = match.group(0)
                                
                                result_entry = {
                                    'line_number': i + 1,
                                    'code_line': line.rstrip(),
                                    'matched_text': matched_text,
                                    'file_path': file_path
                                }
                                
                                # 컨텍스트가 필요한 경우에만 추가
                                if include_context:
                                    start = max(0, i - context_lines)
                                    end = min(len(lines), i + context_lines + 1)
                                    context = [l.rstrip() for l in lines[start:end]]
                                    result_entry['context'] = context
                                    result_entry['context_start_line'] = start + 1
                                
                                results.append(result_entry)
                                
                                if len(results) >= max_results:
                                    break
                    except:
                        # 읽을 수 없는 파일은 무시
                        pass
                        
                if len(results) >= max_results:
                    break
                    
            if len(results) >= max_results:
                break
                
    except Exception as e:
        return HelperResult.fail(f'Code search failed: {str(e)}')
    
    # 성공 시 결과 리스트 직접 반환
    result = HelperResult.success(results)
    
    # 메타데이터는 별도 속성으로 추가 (선택적)
    result.metadata = {
        'searched_files': searched_files,
        'execution_time': time.time() - start_time
    }
    
    return result

