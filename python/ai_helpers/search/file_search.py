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

def search_files_advanced(directory, pattern='*', file_extensions=None, exclude_patterns=None, 
                           case_sensitive=False, recursive=True, max_results=100, 
                           timeout_ms=30000, return_details=False):
    """
    고급 파일 검색 (추적 포함) - 개선된 버전
    
    Args:
        directory: 검색할 디렉토리
        pattern: 파일명 패턴 (기본: '*')
        file_extensions: 파일 확장자 필터 (미사용, 호환성 유지)
        exclude_patterns: 제외 패턴 (미사용, 호환성 유지)
        case_sensitive: 대소문자 구분 (미사용, 호환성 유지)
        recursive: 하위 디렉토리 포함 (기본: True)
        max_results: 최대 결과 수 (기본: 100)
        timeout_ms: 타임아웃 (기본: 30000ms)
        return_details: 파일 상세 정보 포함 여부 (기본: False)
        
    Returns:
        HelperResult: 파일 검색 결과
            - ok=True일 때:
              - return_details=False: data는 파일 경로 문자열의 리스트
                ['path/to/file1.py', 'path/to/file2.py', ...]
              - return_details=True: data는 파일 정보 딕셔너리의 리스트
                [
                  {
                    'file_path': str,  # 파일 경로
                    'file_name': str,  # 파일명
                    'size': int,       # 파일 크기 (bytes)
                    'modified': float  # 수정 시간 (timestamp)
                  },
                  ...
                ]
            - metadata 속성에 추가 정보:
              - searched_count: 검색한 항목 수
              - execution_time: 실행 시간
    
    Example:
        >>> # 간단한 파일 경로 리스트
        >>> files = search_files_advanced(".", "*.py")
        >>> for path in files.data[:10]:
        ...     print(path)
        
        >>> # 상세 정보 포함
        >>> files = search_files_advanced(".", "*.py", return_details=True)
        >>> for info in files.data:
        ...     print(f"{info['file_name']} - {info['size']} bytes")
    """
    # 파일 확장자 처리 (호환성 유지)
    if file_extensions:
        if isinstance(file_extensions, list):
            for ext in file_extensions:
                if not ext.startswith('.'):
                    ext = '.' + ext
                if not pattern.endswith('*' + ext):
                    pattern = pattern.rstrip('*') + '*' + ext
                break  # 첫 번째 확장자만 사용
        else:
            ext = file_extensions if file_extensions.startswith('.') else '.' + file_extensions
            if not pattern.endswith('*' + ext):
                pattern = pattern.rstrip('*') + '*' + ext
    
    # 실제 검색 수행
    result = _search_files_advanced(
        path=directory, 
        pattern=pattern, 
        recursive=recursive, 
        max_results=max_results,
        return_details=return_details
    )
    
    # 작업 추적
    try:
        track_file_access(directory, 'search_files')
    except:
        pass
        
    return result


def _search_files_advanced(path: str, pattern: str, recursive: bool = True,
                            include_hidden: bool = False, max_results: int = 1000,
                            include_dirs: bool = False, return_details: bool = False) -> HelperResult:
    """
    파일 검색 내부 구현 - 개선된 버전
    
    Args:
        path: 검색 시작 경로
        pattern: 파일명 패턴 (fnmatch 형식, 대소문자 무시)
        recursive: 하위 디렉토리 재귀 검색 여부
        include_hidden: 숨김 파일/디렉토리 포함 여부
        max_results: 최대 결과 수
        include_dirs: 디렉토리 포함 여부 (현재 미사용)
        return_details: 상세 정보 반환 여부
    
    Returns:
        HelperResult with data as:
        - list of file paths (strings) if return_details=False
          ['path/to/file1.py', 'path/to/file2.py', ...]
        - list of file info dicts if return_details=True
          [
            {
              'file_path': str,    # 전체 경로
              'file_name': str,    # 파일명만
              'size': int,         # 바이트 단위 크기
              'modified': float    # 수정 시간 timestamp
            },
            ...
          ]
        
        metadata 속성:
        - searched_count: 검사한 총 파일 수
        - execution_time: 실행 시간 (초)
    
    Note:
        - 패턴 매칭은 파일명에 대해서만 수행 (경로 제외)
        - os.stat() 실패 시 return_details=True여도 기본 정보만 반환
    """
    import fnmatch
    import time
    
    start_time = time.time()
    results = []
    searched_count = 0
    
    try:
        if recursive:
            for root, dirs, files in os.walk(path):
                # 숨김 디렉토리 제외
                if not include_hidden:
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for filename in files:
                    if not include_hidden and filename.startswith('.'):
                        continue
                        
                    searched_count += 1
                    if fnmatch.fnmatch(filename.lower(), pattern.lower()):
                        file_path = os.path.join(root, filename)
                        
                        if return_details:
                            try:
                                stat = os.stat(file_path)
                                results.append({
                                    'file_path': file_path,
                                    'file_name': filename,
                                    'size': stat.st_size,
                                    'modified': stat.st_mtime
                                })
                            except:
                                # 상세 정보를 가져올 수 없으면 경로만 추가
                                results.append({'file_path': file_path, 'file_name': filename})
                        else:
                            # 기본: 경로만 반환
                            results.append(file_path)
                            
                        if len(results) >= max_results:
                            break
                            
                if len(results) >= max_results:
                    break
        else:
            # 재귀 없이 현재 디렉토리만
            for filename in os.listdir(path):
                file_path = os.path.join(path, filename)
                if os.path.isfile(file_path):
                    if not include_hidden and filename.startswith('.'):
                        continue
                        
                    searched_count += 1
                    if fnmatch.fnmatch(filename.lower(), pattern.lower()):
                        if return_details:
                            try:
                                stat = os.stat(file_path)
                                results.append({
                                    'file_path': file_path,
                                    'file_name': filename,
                                    'size': stat.st_size,
                                    'modified': stat.st_mtime
                                })
                            except:
                                results.append({'file_path': file_path, 'file_name': filename})
                        else:
                            results.append(file_path)
                            
    except Exception as e:
        return HelperResult.fail(f'File search failed: {str(e)}')
    
    # 성공 시 결과 반환
    result = HelperResult.success(results)
    
    # 메타데이터 추가
    result.metadata = {
        'searched_count': searched_count,
        'execution_time': time.time() - start_time
    }
    
    return result

