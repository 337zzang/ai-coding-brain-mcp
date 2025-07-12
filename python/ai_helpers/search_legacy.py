"""AI Helpers Search Module - Refactored Version"""

# 새 모듈에서 함수들을 import
from .search.file_search import search_files_advanced, _search_files_advanced
from .search.code_search import search_code_content, _search_code_content
from .search.directory_scan import scan_directory, scan_directory_dict, cache_project_structure

# 기존 search.py의 나머지 함수들은 유지
import os
import re
import glob
import fnmatch
from typing import List, Dict, Optional, Union, Tuple, Any
from pathlib import Path

from .helper_result import HelperResult

# 나머지 헬퍼 함수들과 상수들
"""검색 관련 헬퍼 함수들"""
from .helper_result import HelperResult

import os
import re
import fnmatch
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from datetime import datetime
from .decorators import track_operation
from .context import get_project_context
from .utils import track_file_access



@track_operation('file', 'scan')
@track_operation('search', 'code')
# Auto-tracking wrapper에서 이동된 함수들
def search_in_structure(pattern, search_type="all"):
    """캐시된 구조에서 파일/디렉토리 검색
    
    Args:
        pattern: 검색 패턴 (glob 형식)
        search_type: "file", "dir", "all"
    
    Returns:
        list: 검색 결과 리스트
    """
    import fnmatch
    
    # 캐시된 구조 가져오기
    structure = get_project_structure()
    
    results = []
    
    for path, info in structure['structure'].items():
        if info.get('error'):
            continue
            
        # 디렉토리 검색
        if search_type in ["dir", "all"] and info['type'] == 'directory':
            dir_name = os.path.basename(path.rstrip('/'))
            if dir_name and fnmatch.fnmatch(dir_name, pattern):
                results.append({
                    'type': 'directory',
                    'path': path,
                    'name': dir_name,
                    'file_count': info.get('file_count', 0),
                    'dir_count': info.get('dir_count', 0)
                })
        
        # 파일 검색
        if search_type in ["file", "all"] and 'files' in info:
            for file_name in info['files']:
                if fnmatch.fnmatch(file_name, pattern):
                    file_path = os.path.join(path, file_name).replace("\\", "/")
                    results.append({
                        'type': 'file',
                        'path': file_path,
                        'name': file_name,
                        'parent': path
                    })
    
    return results



def get_project_structure(force_rescan=False):
    """캐시된 프로젝트 구조 반환 (필요시 자동 스캔)
    
    Args:
        force_rescan: 강제 재스캔 여부
    
    Returns:
        dict: 프로젝트 구조 정보
    """
    return cache_project_structure(force_rescan=force_rescan)




# TODO: include_dirs 로직 구현 필요


# ================== Search API 표준화 추가 코드 ==================
# 두 가지 표준 반환 규격을 위한 헬퍼 함수들

def _format_as_path_list(results):
    """결과를 Path List 형식으로 변환"""
    if isinstance(results, list):
        # results가 dict 리스트인 경우
        if results and isinstance(results[0], dict) and 'path' in results[0]:
            return {'paths': [r['path'] for r in results]}
        # results가 이미 path 리스트인 경우
        return {'paths': results}
    return {'paths': []}

def _format_as_grouped_dict(results, group_key='file'):
    """결과를 Grouped Dict 형식으로 변환"""
    grouped = {}
    if isinstance(results, list):
        for item in results:
            if isinstance(item, dict) and group_key in item:
                key = item[group_key]
                grouped.setdefault(key, []).append(item)
    return {'results': grouped}

# 새로운 표준 API 함수들
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
    result = search_code_content(directory, regex, file_pattern, **kwargs)
    if result.get('success'):
        # 결과를 파일별로 그룹화
        grouped = {}
        for match in result.get('results', []):
            filepath = match.get('file', '')
            grouped.setdefault(filepath, []).append(match)
        return {
            'success': True,
            'results': grouped
        }
    return result

def scan_dir(directory, as_dict=True, **kwargs):
    """
    디렉토리 스캔 표준 API
    as_dict=True: 기존 형식 유지
    as_dict=False: Path List 형식 (규격 A)
    """
    if as_dict:
        return scan_directory_dict(directory)
    else:
        data = scan_directory_dict(directory)
        paths = [f['path'] for f in data.get('files', [])]
        return {
            'success': True,
            'paths': paths
        }

# ================== 끝 ==================

# Export할 함수들 정의
__all__ = [
    # 디렉토리 관련
    'scan_directory', 'scan_directory_dict', 'cache_project_structure',
    'get_project_structure', 'search_in_structure',
    
    # 파일 검색
    'search_files_advanced', '_search_files_advanced',
    
    # 코드 검색
    'search_code_content', '_search_code_content',
    
    # 표준 API
    'list_file_paths', 'grep_code', 'scan_dir'
]
