"""
파일 검색 전문 모듈

파일명 패턴 기반 검색 기능을 제공합니다.
"""

import os
import time
import fnmatch
from typing import List, Optional, Union
from pathlib import Path

from ..helper_result import HelperResult
from .types import FileInfo, SearchResult
from .core import (
    normalize_path, 
    should_ignore, 
    get_file_info,
    filter_hidden_items,
    DEFAULT_IGNORE_PATTERNS
)


def search_files(
    path: Union[str, Path] = '.',
    pattern: str = '*',
    recursive: bool = True,
    include_hidden: bool = False,
    max_results: int = 1000,
    return_details: bool = False,
    ignore_patterns: Optional[List[str]] = None
) -> HelperResult:
    """파일 검색 기능
    
    Args:
        path: 검색 시작 경로
        pattern: 파일명 패턴 (fnmatch 형식)
        recursive: 하위 디렉토리 재귀 검색 여부
        include_hidden: 숨김 파일/디렉토리 포함 여부
        max_results: 최대 결과 수
        return_details: 상세 정보 반환 여부
        ignore_patterns: 무시할 패턴 리스트
        
    Returns:
        HelperResult with:
        - return_details=False: data는 파일 경로 문자열의 리스트
        - return_details=True: data는 FileInfo 딕셔너리의 리스트
    """
    start_time = time.time()
    results = []
    searched_count = 0
    
    # 경로 정규화
    search_path = normalize_path(path)
    if not search_path.exists():
        return HelperResult.fail(f"경로가 존재하지 않음: {search_path}")
    
    # 무시 패턴 설정
    if ignore_patterns is None:
        ignore_patterns = DEFAULT_IGNORE_PATTERNS
    
    try:
        if recursive:
            # 재귀 검색
            for root, dirs, files in os.walk(search_path):
                root_path = Path(root)
                
                # 무시할 디렉토리 제거
                if not include_hidden:
                    dirs[:] = filter_hidden_items(dirs, include_hidden)
                
                # 무시 패턴 체크
                dirs[:] = [d for d in dirs if not should_ignore(root_path / d, ignore_patterns)]
                
                # 파일 검색
                for filename in files:
                    if not include_hidden and filename.startswith('.'):
                        continue
                    
                    file_path = root_path / filename
                    if should_ignore(file_path, ignore_patterns):
                        continue
                    
                    searched_count += 1
                    
                    # 패턴 매칭
                    if fnmatch.fnmatch(filename.lower(), pattern.lower()):
                        if return_details:
                            results.append(get_file_info(file_path))
                        else:
                            results.append(str(file_path))
                        
                        if len(results) >= max_results:
                            break
                
                if len(results) >= max_results:
                    break
        else:
            # 현재 디렉토리만 검색
            for item in search_path.iterdir():
                if item.is_file():
                    if not include_hidden and item.name.startswith('.'):
                        continue
                    
                    if should_ignore(item, ignore_patterns):
                        continue
                    
                    searched_count += 1
                    
                    if fnmatch.fnmatch(item.name.lower(), pattern.lower()):
                        if return_details:
                            results.append(get_file_info(item))
                        else:
                            results.append(str(item))
                        
                        if len(results) >= max_results:
                            break
                            
    except Exception as e:
        return HelperResult.fail(f'파일 검색 실패: {str(e)}')
    
    # 결과 반환
    result = HelperResult.success(results)
    result.metadata = {
        'searched_count': searched_count,
        'execution_time': time.time() - start_time,
        'pattern': pattern,
        'recursive': recursive
    }
    
    return result


def find_files_by_extension(
    path: Union[str, Path] = '.',
    extensions: Union[str, List[str]] = None,
    recursive: bool = True,
    **kwargs
) -> HelperResult:
    """확장자로 파일 찾기
    
    Args:
        path: 검색 경로
        extensions: 확장자 또는 확장자 리스트 (예: '.py' 또는 ['.py', '.txt'])
        recursive: 재귀 검색 여부
        **kwargs: search_files에 전달할 추가 인자
        
    Returns:
        HelperResult with file paths
    """
    if extensions is None:
        return search_files(path, '*', recursive, **kwargs)
    
    # 확장자 정규화
    if isinstance(extensions, str):
        extensions = [extensions]
    
    # 패턴 생성
    patterns = []
    for ext in extensions:
        if not ext.startswith('.'):
            ext = '.' + ext
        patterns.append(f'*{ext}')
    
    # 여러 패턴으로 검색
    all_results = []
    for pattern in patterns:
        result = search_files(path, pattern, recursive, **kwargs)
        if result.ok:
            all_results.extend(result.data)
    
    return HelperResult.success(all_results)


def find_files_by_name(
    path: Union[str, Path] = '.',
    name: str = '',
    exact: bool = False,
    case_sensitive: bool = False,
    **kwargs
) -> HelperResult:
    """이름으로 파일 찾기
    
    Args:
        path: 검색 경로
        name: 파일명
        exact: 정확히 일치 여부
        case_sensitive: 대소문자 구분
        **kwargs: search_files에 전달할 추가 인자
        
    Returns:
        HelperResult with file paths
    """
    if exact:
        pattern = name
    else:
        pattern = f'*{name}*'
    
    # 대소문자 구분 처리는 search_files에서 자동으로 됨
    return search_files(path, pattern, **kwargs)
