"""
디렉토리 스캔 함수 - 통합 및 개선된 버전
중복 제거 및 기능 강화
"""
from typing import Dict, List, Any, Optional, Set
from .helper_result import HelperResult
from pathlib import Path
import os
import json
import time

# 전역 캐시
_project_cache = {}

def scan_directory_dict(directory: str = ".", 
                       include_hidden: bool = False,
                       max_depth: Optional[int] = None,
                       file_extensions: Optional[Set[str]] = None,
                       exclude_dirs: Optional[Set[str]] = None) -> HelperResult:
    """
    디렉토리를 스캔하여 구조화된 딕셔너리로 반환

    Args:
        directory: 스캔할 디렉토리 경로
        include_hidden: 숨김 파일/폴더 포함 여부
        max_depth: 최대 탐색 깊이 (None이면 무제한)
        file_extensions: 포함할 파일 확장자 집합 (None이면 모든 파일)
        exclude_dirs: 제외할 디렉토리 이름 집합

    Returns:
        HelperResult with directory structure
    """
    try:
        scan_path = Path(directory).resolve()

        if not scan_path.exists():
            return HelperResult(False, error=f"경로가 존재하지 않습니다: {directory}")

        if not scan_path.is_dir():
            return HelperResult(False, error=f"디렉토리가 아닙니다: {directory}")

        # 기본 제외 디렉토리
        default_exclude = {'.git', '__pycache__', 'node_modules', '.venv', 'venv'}
        if exclude_dirs:
            default_exclude.update(exclude_dirs)

        def should_include_file(file_path: Path) -> bool:
            """파일 포함 여부 결정"""
            if not include_hidden and file_path.name.startswith('.'):
                return False
            if file_extensions and file_path.suffix not in file_extensions:
                return False
            return True

        def should_include_dir(dir_path: Path) -> bool:
            """디렉토리 포함 여부 결정"""
            if not include_hidden and dir_path.name.startswith('.'):
                return False
            if dir_path.name in default_exclude:
                return False
            return True

        def scan_recursive(path: Path, current_depth: int = 0) -> Dict[str, Any]:
            """재귀적으로 디렉토리 스캔"""
            result = {
                'name': path.name,
                'path': str(path),
                'type': 'directory',
                'files': [],
                'directories': []
            }

            if max_depth is not None and current_depth >= max_depth:
                return result

            try:
                for item in sorted(path.iterdir()):
                    if item.is_file() and should_include_file(item):
                        file_info = {
                            'name': item.name,
                            'path': str(item),
                            'size': item.stat().st_size,
                            'extension': item.suffix,
                            'modified': item.stat().st_mtime
                        }
                        result['files'].append(file_info)
                    elif item.is_dir() and should_include_dir(item):
                        if max_depth is None or current_depth < max_depth - 1:
                            subdir = scan_recursive(item, current_depth + 1)
                            result['directories'].append(subdir)
                        else:
                            # 최대 깊이에 도달한 경우 기본 정보만
                            result['directories'].append({
                                'name': item.name,
                                'path': str(item),
                                'type': 'directory'
                            })
            except PermissionError:
                # 권한이 없는 디렉토리는 건너뛰기
                pass

            return result

        # 플랫 구조도 함께 제공
        files = []
        directories = []

        for item in scan_path.iterdir():
            if item.is_file() and should_include_file(item):
                files.append({
                    'name': item.name,
                    'path': str(item),
                    'size': item.stat().st_size
                })
            elif item.is_dir() and should_include_dir(item):
                directories.append({
                    'name': item.name,
                    'path': str(item)
                })

        # 전체 구조 스캔 (max_depth가 0이 아닌 경우)
        tree_structure = None
        if max_depth != 0:
            tree_structure = scan_recursive(scan_path)

        return HelperResult(True, data={
            'files': files,
            'directories': directories,
            'total_files': len(files),
            'total_directories': len(directories),
            'tree': tree_structure,
            'scan_path': str(scan_path)
        })

    except Exception as e:
        return HelperResult(False, error=f"디렉토리 스캔 중 오류: {str(e)}")


def list_file_paths(directory: str = ".", 
                   pattern: str = "*",
                   recursive: bool = True,
                   files_only: bool = True) -> HelperResult:
    """
    파일 경로 목록 반환 (간단한 버전)

    Args:
        directory: 시작 디렉토리
        pattern: 파일 패턴
        recursive: 재귀적 검색 여부
        files_only: 파일만 반환 (False면 디렉토리도 포함)

    Returns:
        HelperResult with list of paths
    """
    try:
        from .search_wrappers import search_files_advanced

        result = search_files_advanced(directory, pattern, recursive)
        if not result.ok:
            return result

        if files_only:
            paths = [item['path'] for item in result.data['results']]
        else:
            # 디렉토리도 포함하려면 scan_directory_dict 사용
            scan_result = scan_directory_dict(directory)
            if scan_result.ok:
                paths = [item['path'] for item in result.data['results']]
                paths.extend([d['path'] for d in scan_result.data['directories']])
            else:
                paths = [item['path'] for item in result.data['results']]

        return HelperResult(True, data=paths)

    except Exception as e:
        return HelperResult(False, error=f"Failed to list paths: {str(e)}")


# 별칭 (하위 호환성)
scan_directory = scan_directory_dict  # 기존 함수명 호환
list_directory = scan_directory_dict  # 기존 함수명 호환
scan_dir = scan_directory_dict       # 짧은 별칭


def cache_project_structure(project_path: str = ".", force_refresh: bool = False) -> HelperResult:
    """
    프로젝트 구조를 캐시에 저장
    
    Args:
        project_path: 프로젝트 경로
        force_refresh: 강제 새로고침 여부
        
    Returns:
        HelperResult with cache status
    """
    global _project_cache
    
    cache_key = str(Path(project_path).resolve())
    
    # 캐시 확인
    if not force_refresh and cache_key in _project_cache:
        cache_data = _project_cache[cache_key]
        if time.time() - cache_data['timestamp'] < 300:  # 5분 캐시
            return HelperResult(True, data={
                'status': 'cached',
                'structure': cache_data['structure']
            })
    
    # 새로 스캔
    scan_result = scan_directory_dict(project_path, include_hidden=False, max_depth=10)
    if not scan_result.ok:
        return scan_result
    
    # 캐시 저장
    _project_cache[cache_key] = {
        'structure': scan_result.data,
        'timestamp': time.time()
    }
    
    return HelperResult(True, data={
        'status': 'refreshed',
        'structure': scan_result.data
    })


def get_project_structure(project_path: str = ".") -> HelperResult:
    """
    캐시된 프로젝트 구조 가져오기
    
    Args:
        project_path: 프로젝트 경로
        
    Returns:
        HelperResult with project structure
    """
    return cache_project_structure(project_path, force_refresh=False)


def search_in_structure(pattern: str, structure: Optional[Dict] = None, 
                       project_path: str = ".") -> HelperResult:
    """
    프로젝트 구조에서 파일 검색
    
    Args:
        pattern: 검색 패턴
        structure: 프로젝트 구조 (None이면 캐시에서 가져옴)
        project_path: 프로젝트 경로
        
    Returns:
        HelperResult with matching files
    """
    try:
        # 구조 가져오기
        if structure is None:
            struct_result = get_project_structure(project_path)
            if not struct_result.ok:
                return struct_result
            structure = struct_result.data['structure']
        
        # 패턴 매칭
        matches = []
        pattern_lower = pattern.lower()
        
        # 파일 검색
        for file_info in structure.get('files', []):
            if pattern_lower in file_info['name'].lower():
                matches.append({
                    'path': file_info['path'],
                    'name': file_info['name'],
                    'type': 'file'
                })
        
        # 디렉토리 검색
        for dir_info in structure.get('directories', []):
            if pattern_lower in dir_info['name'].lower():
                matches.append({
                    'path': dir_info['path'],
                    'name': dir_info['name'],
                    'type': 'directory'
                })
        
        return HelperResult(True, data={
            'matches': matches,
            'count': len(matches),
            'pattern': pattern
        })
        
    except Exception as e:
        return HelperResult(False, error=f"Search failed: {str(e)}")
