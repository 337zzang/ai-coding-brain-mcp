"""
Search 모듈 타입 정의

이 파일은 search 모듈 전체에서 사용하는 타입들을 정의합니다.
"""

from typing import TypedDict, List, Dict, Union, Optional, Any, Literal
from pathlib import Path


# 검색 모드 타입
SearchMode = Literal['files', 'code', 'dirs', 'all', 'auto']
SearchFormat = Literal['list', 'dict', 'grouped', 'auto']


class FileInfo(TypedDict):
    """파일 정보 타입"""
    file_path: str
    file_name: str
    size: int
    modified: float
    

class DirectoryInfo(TypedDict):
    """디렉토리 정보 타입"""
    name: str
    path: str
    file_count: Optional[int]
    dir_count: Optional[int]


class SearchMatch(TypedDict):
    """코드 검색 매치 타입"""
    line_number: int
    code_line: str
    matched_text: str
    file_path: str
    context: Optional[List[str]]
    context_start_line: Optional[int]


class DirectoryScanResult(TypedDict):
    """디렉토리 스캔 결과 타입"""
    files: List[Dict[str, Any]]
    directories: List[Dict[str, Any]]
    total_size: int
    stats: Dict[str, Any]


class SearchResultDict(TypedDict):
    """통합 검색 결과 (dict 형식)"""
    results: List[Union[SearchMatch, FileInfo, DirectoryInfo]]
    count: int
    files: Optional[List[str]]
    metadata: Optional[Dict[str, Any]]


class GroupedSearchResult(TypedDict):
    """그룹화된 검색 결과"""
    results: Dict[str, List[Union[SearchMatch, FileInfo]]]
    count: int
    file_count: int
    metadata: Optional[Dict[str, Any]]


# 검색 결과 반환 타입
SearchResult = Union[
    List[str],                    # 단순 경로 리스트
    List[SearchMatch],            # 코드 매치 리스트
    List[FileInfo],               # 파일 정보 리스트
    SearchResultDict,             # dict 형식
    GroupedSearchResult           # 그룹화된 형식
]
