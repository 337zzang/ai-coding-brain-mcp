"""
통합 검색 API

모든 검색 기능을 하나의 인터페이스로 통합합니다.
list/dict 형식을 자동으로 변환하여 일관된 사용 경험을 제공합니다.
"""

from typing import Union, List, Dict, Any, Optional
from pathlib import Path

from ..helper_result import HelperResult
from .types import (
    SearchMode, SearchFormat, SearchResult,
    SearchResultDict, GroupedSearchResult
)
from .file_search import search_files
from .code_search import search_code
from .directory_scan import scan_directory


def search_smart(
    pattern: str,
    path: Union[str, Path] = '.',
    mode: SearchMode = 'auto',
    format: SearchFormat = 'auto',
    **kwargs
) -> HelperResult:
    """통합 스마트 검색 API
    
    Args:
        pattern: 검색 패턴
        path: 검색 경로
        mode: 검색 모드
            - 'files': 파일명 검색
            - 'code': 코드 내용 검색
            - 'dirs': 디렉토리 검색
            - 'all': 모든 타입 검색
            - 'auto': 패턴에 따라 자동 결정
        format: 반환 형식
            - 'list': 항상 리스트 반환
            - 'dict': 항상 딕셔너리 반환
            - 'grouped': 파일별로 그룹화
            - 'auto': 결과에 따라 자동 결정
        **kwargs: 각 검색 함수에 전달할 추가 인자
        
    Returns:
        HelperResult with formatted search results
    """
    # 자동 모드 결정
    if mode == 'auto':
        mode = _detect_search_mode(pattern, kwargs)
    
    # 검색 수행
    if mode == 'files':
        result = search_files(path, pattern, **kwargs)
    elif mode == 'code':
        # file_pattern 처리
        file_pattern = kwargs.pop('file_pattern', '*.py')
        result = search_code(path, pattern, file_pattern, **kwargs)
    elif mode == 'dirs':
        result = scan_directory(path, **kwargs)
    elif mode == 'all':
        # 모든 타입 검색
        results = {
            'files': search_files(path, pattern, **kwargs),
            'code': search_code(path, pattern, kwargs.get('file_pattern', '*.py'), **kwargs),
            'dirs': scan_directory(path, **kwargs)
        }
        return _format_combined_results(results, format)
    else:
        return HelperResult.fail(f"지원하지 않는 검색 모드: {mode}")
    
    # 결과 포맷팅
    return _format_search_result(result, format, mode)


def _detect_search_mode(pattern: str, kwargs: dict) -> str:
    """패턴과 인자를 보고 검색 모드 자동 결정"""
    # 정규식 패턴이 있으면 코드 검색
    if any(c in pattern for c in ['^', '$', '\\', '|', '(', ')', '[', ']', '{', '}']):
        return 'code'
    
    # file_pattern이 지정되면 코드 검색
    if 'file_pattern' in kwargs:
        return 'code'
    
    # 확장자 패턴이면 파일 검색
    if pattern.startswith('*.') or pattern.endswith('.*'):
        return 'files'
    
    # 기본값은 파일 검색
    return 'files'


def _format_search_result(
    result: HelperResult,
    format: SearchFormat,
    mode: str
) -> HelperResult:
    """검색 결과를 요청된 형식으로 변환"""
    if not result.ok:
        return result
    
    data = result.get_data([])
    
    # 자동 형식 결정
    if format == 'auto':
        if not data:
            format = 'dict'
        elif mode == 'code' and len(data) > 10:
            format = 'grouped'
        else:
            format = 'dict'
    
    # 형식 변환
    if format == 'list':
        # 이미 리스트인 경우 그대로 반환
        formatted = data
    
    elif format == 'dict':
        # 딕셔너리 형식으로 변환
        formatted = {
            'results': data,
            'count': len(data),
            'mode': mode
        }
        
        # 파일 목록 추가 (코드 검색인 경우)
        if mode == 'code' and data:
            files = list(set(match.get('file_path', '') for match in data))
            formatted['files'] = sorted(files)
    
    elif format == 'grouped':
        # 그룹화 형식
        if mode == 'code':
            grouped = {}
            for match in data:
                file_path = match.get('file_path', 'unknown')
                grouped.setdefault(file_path, []).append(match)
            
            formatted = {
                'results': grouped,
                'count': len(data),
                'file_count': len(grouped)
            }
        else:
            # 코드 검색이 아닌 경우 일반 dict 형식 사용
            formatted = {
                'results': data,
                'count': len(data),
                'mode': mode
            }
    
    else:
        return HelperResult.fail(f"지원하지 않는 형식: {format}")
    
    # 메타데이터 보존
    new_result = HelperResult.success(formatted)
    if hasattr(result, 'metadata'):
        new_result.metadata = result.metadata
    
    return new_result


def _format_combined_results(
    results: Dict[str, HelperResult],
    format: SearchFormat
) -> HelperResult:
    """여러 검색 결과를 통합"""
    combined = {
        'files': [],
        'code_matches': [],
        'directories': [],
        'stats': {
            'file_count': 0,
            'code_match_count': 0,
            'dir_count': 0
        }
    }
    
    # 파일 검색 결과
    if results['files'].ok:
        file_data = results['files'].get_data([])
        combined['files'] = file_data
        combined['stats']['file_count'] = len(file_data)
    
    # 코드 검색 결과
    if results['code'].ok:
        code_data = results['code'].get_data([])
        combined['code_matches'] = code_data
        combined['stats']['code_match_count'] = len(code_data)
    
    # 디렉토리 검색 결과
    if results['dirs'].ok:
        dir_data = results['dirs'].get_data({})
        combined['directories'] = dir_data.get('directories', [])
        combined['stats']['dir_count'] = len(combined['directories'])
    
    return HelperResult.success(combined)



# 편의 함수들

def search(pattern: str, **kwargs) -> HelperResult:
    """간단한 검색 함수 (search_smart의 별칭)"""
    return search_smart(pattern, **kwargs)


def grep(pattern: str, path: str = '.', **kwargs) -> HelperResult:
    """grep 스타일 코드 검색"""
    return search_smart(pattern, path, mode='code', format='grouped', **kwargs)


def find(pattern: str, path: str = '.', **kwargs) -> HelperResult:
    """find 스타일 파일 검색"""
    return search_smart(pattern, path, mode='files', format='list', **kwargs)


def ls(path: str = '.', **kwargs) -> HelperResult:
    """ls 스타일 디렉토리 목록"""
    result = scan_directory(path, max_depth=0, **kwargs)
    if result.ok:
        data = result.data
        items = []
        
        # 디렉토리 먼저
        for d in sorted(data['directories'], key=lambda x: x['name']):
            items.append(f"{d['name']}/")
        
        # 파일
        for f in sorted(data['files'], key=lambda x: x['name']):
            items.append(f['name'])
        
        return HelperResult.success(items)
    return result


def tree(path: str = '.', max_depth: int = 3, **kwargs) -> HelperResult:
    """tree 스타일 디렉토리 트리"""
    from .directory_scan import get_directory_tree
    result = get_directory_tree(path, max_depth, **kwargs)
    if result.ok:
        print(result.data['tree'])
    return result


# 호환성을 위한 래퍼 함수들

def search_code_smart(
    pattern: str,
    path: str = '.',
    file_pattern: str = '*.py',
    format: SearchFormat = 'auto'
) -> HelperResult:
    """기존 search_code의 스마트 버전"""
    return search_smart(
        pattern,
        path,
        mode='code',
        format=format,
        file_pattern=file_pattern
    )


def search_files_smart(
    directory: str,
    pattern: str = '*',
    format: SearchFormat = 'auto',
    **kwargs
) -> HelperResult:
    """기존 search_files의 스마트 버전"""
    return search_smart(
        pattern,
        directory,
        mode='files',
        format=format,
        **kwargs
    )


# Legacy API 호환성 함수들

def list_file_paths(directory, pattern="*", recursive=True):
    """파일 경로 목록 반환

    Args:
        directory: 검색할 디렉토리
        pattern: 파일 패턴 (기본값: "*")
        recursive: 재귀 검색 여부 (기본값: True)

    Returns:
        HelperResult: 성공 시 data에 {'paths': [파일경로들]}
    """
    try:
        from pathlib import Path

        directory = Path(directory).resolve()
        if not directory.exists():
            return HelperResult(ok=False, data=None, error=f"디렉토리가 존재하지 않음: {directory}")

        if recursive:
            files = list(directory.rglob(pattern))
        else:
            files = list(directory.glob(pattern))

        paths = [str(f) for f in files if f.is_file()]

        return HelperResult(ok=True, data={'paths': paths}, error=None)

    except Exception as e:
        return HelperResult(ok=False, data=None, error=f"파일 목록 조회 실패: {str(e)}")


def grep_code(directory, regex, file_pattern='*', **kwargs):
    """
    코드 내용 검색 표준 API (규격 B: Grouped Dict)
    기존 search_code_content의 개선 버전
    """
    from .code_search import search_code_content
    
    result = search_code_content(directory, regex, file_pattern, **kwargs)
    if result.ok:
        data = result.get_data({})
        if 'results' in data:
            # 결과를 파일별로 그룹화
            grouped = {}
            for match in data.get('results', []):
                filepath = match.get('file', '')
                grouped.setdefault(filepath, []).append(match)
            return HelperResult(ok=True, data={
                'success': True,
                'results': grouped
            })
    return result


def scan_dir(directory, as_dict=True, **kwargs):
    """
    디렉토리 스캔 표준 API
    as_dict=True: 기존 형식 유지
    as_dict=False: Path List 형식 (규격 A)
    """
    from .directory_scan import scan_directory_dict
    
    if as_dict:
        return scan_directory_dict(directory)
    else:
        result = scan_directory_dict(directory)
        if result.ok:
            data = result.get_data({})
            paths = [f['path'] for f in data.get('files', [])]
            return HelperResult(ok=True, data={
                'success': True,
                'paths': paths
            })
        return result
