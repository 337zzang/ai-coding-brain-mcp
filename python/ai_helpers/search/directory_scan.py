"""
디렉토리 스캔 전문 모듈

디렉토리 구조를 스캔하고 분석하는 기능을 제공합니다.
"""

import os
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from datetime import datetime

from ..helper_result import HelperResult
from .types import DirectoryScanResult
from .core import (
    normalize_path,
    should_ignore,
    DEFAULT_IGNORE_PATTERNS
)


def scan_directory(
    path: Union[str, Path] = '.',
    max_depth: int = -1,
    include_hidden: bool = False,
    ignore_patterns: Optional[List[str]] = None
) -> HelperResult:
    """디렉토리 스캔 (딕셔너리 형식)
    
    Args:
        path: 스캔할 디렉토리 경로
        max_depth: 최대 깊이 (-1은 무제한)
        include_hidden: 숨김 파일/디렉토리 포함 여부
        ignore_patterns: 무시할 패턴 리스트
        
    Returns:
        HelperResult with DirectoryScanResult
    """
    # 경로 정규화
    directory_path = normalize_path(path)
    
    if not directory_path.exists():
        return HelperResult.fail(f"디렉토리가 존재하지 않음: {directory_path}")
    
    if not directory_path.is_dir():
        return HelperResult.fail(f"디렉토리가 아님: {directory_path}")
    
    # 무시 패턴 설정
    if ignore_patterns is None:
        ignore_patterns = DEFAULT_IGNORE_PATTERNS
    
    result = {
        'files': [],
        'directories': [],
        'total_size': 0,
        'stats': {
            'file_count': 0,
            'dir_count': 0,
            'by_extension': {}
        }
    }
    
    def scan_recursive(dir_path: Path, current_depth: int = 0):
        """재귀적으로 디렉토리 스캔"""
        if max_depth != -1 and current_depth > max_depth:
            return
        
        try:
            for item in dir_path.iterdir():
                # 숨김 항목 처리
                if not include_hidden and item.name.startswith('.'):
                    continue
                
                # 무시 패턴 체크
                if should_ignore(item, ignore_patterns):
                    continue
                
                try:
                    if item.is_file():
                        size = item.stat().st_size
                        result['files'].append({
                            'name': item.name,
                            'path': str(item),
                            'size': size
                        })
                        result['total_size'] += size
                        result['stats']['file_count'] += 1
                        
                        # 확장자별 통계
                        ext = item.suffix.lower()
                        if ext:
                            result['stats']['by_extension'][ext] = \
                                result['stats']['by_extension'].get(ext, 0) + 1
                    
                    elif item.is_dir():
                        result['directories'].append({
                            'name': item.name,
                            'path': str(item)
                        })
                        result['stats']['dir_count'] += 1
                        
                        # 하위 디렉토리 스캔
                        scan_recursive(item, current_depth + 1)
                        
                except (PermissionError, OSError):
                    continue
                    
        except (PermissionError, OSError):
            pass
    
    # 스캔 시작
    scan_recursive(directory_path)
    
    return HelperResult.success(result)



def get_directory_tree(
    path: Union[str, Path] = '.',
    max_depth: int = 3,
    show_files: bool = True,
    **kwargs
) -> HelperResult:
    """디렉토리 트리 구조 생성
    
    Args:
        path: 시작 경로
        max_depth: 최대 깊이
        show_files: 파일 표시 여부
        **kwargs: scan_directory에 전달할 추가 인자
        
    Returns:
        HelperResult with tree structure
    """
    # 디렉토리 스캔
    scan_result = scan_directory(path, max_depth, **kwargs)
    if not scan_result.ok:
        return scan_result
    
    data = scan_result.data
    
    # 트리 구조 생성
    tree_lines = []
    base_path = normalize_path(path)
    tree_lines.append(str(base_path.name) + "/")
    
    def build_tree(base: Path, prefix: str = "", depth: int = 0):
        if max_depth != -1 and depth >= max_depth:
            return
        
        items = []
        
        # 디렉토리 추가
        for dir_info in data['directories']:
            dir_path = Path(dir_info['path'])
            if dir_path.parent == base:
                items.append(('d', dir_info['name']))
        
        # 파일 추가
        if show_files:
            for file_info in data['files']:
                file_path = Path(file_info['path'])
                if file_path.parent == base:
                    items.append(('f', file_info['name']))
        
        # 정렬
        items.sort(key=lambda x: (x[0], x[1]))
        
        # 출력
        for i, (item_type, name) in enumerate(items):
            is_last = i == len(items) - 1
            
            if is_last:
                tree_lines.append(prefix + "└── " + name + ("/" if item_type == 'd' else ""))
                new_prefix = prefix + "    "
            else:
                tree_lines.append(prefix + "├── " + name + ("/" if item_type == 'd' else ""))
                new_prefix = prefix + "│   "
            
            # 디렉토리면 재귀
            if item_type == 'd':
                build_tree(base / name, new_prefix, depth + 1)
    
    build_tree(base_path, "", 0)
    
    return HelperResult.success({
        'tree': '\n'.join(tree_lines),
        'stats': data['stats']
    })


def analyze_directory(
    path: Union[str, Path] = '.',
    **kwargs
) -> HelperResult:
    """디렉토리 상세 분석
    
    Args:
        path: 분석할 경로
        **kwargs: scan_directory에 전달할 추가 인자
        
    Returns:
        HelperResult with detailed analysis
    """
    # 디렉토리 스캔
    scan_result = scan_directory(path, **kwargs)
    if not scan_result.ok:
        return scan_result
    
    data = scan_result.data
    
    # 상세 분석
    analysis = {
        'summary': {
            'total_files': data['stats']['file_count'],
            'total_directories': data['stats']['dir_count'],
            'total_size': data['total_size'],
            'total_size_mb': round(data['total_size'] / (1024 * 1024), 2)
        },
        'by_extension': data['stats']['by_extension'],
        'largest_files': [],
        'newest_files': [],
        'file_types': {}
    }
    
    # 가장 큰 파일들
    files_with_details = []
    for file_info in data['files']:
        try:
            file_path = Path(file_info['path'])
            stat = file_path.stat()
            files_with_details.append({
                **file_info,
                'modified': stat.st_mtime
            })
        except:
            pass
    
    # 크기순 정렬
    files_by_size = sorted(files_with_details, key=lambda x: x['size'], reverse=True)
    analysis['largest_files'] = files_by_size[:10]
    
    # 수정시간순 정렬
    files_by_time = sorted(files_with_details, key=lambda x: x['modified'], reverse=True)
    analysis['newest_files'] = files_by_time[:10]
    
    # 파일 타입 분류
    for ext, count in data['stats']['by_extension'].items():
        file_type = get_file_type(ext)
        analysis['file_types'][file_type] = analysis['file_types'].get(file_type, 0) + count
    
    return HelperResult.success(analysis)


def get_file_type(extension: str) -> str:
    """확장자로 파일 타입 분류"""
    ext = extension.lower()
    
    if ext in ['.py', '.pyw']:
        return 'Python'
    elif ext in ['.js', '.jsx', '.ts', '.tsx']:
        return 'JavaScript/TypeScript'
    elif ext in ['.html', '.htm', '.css', '.scss', '.less']:
        return 'Web'
    elif ext in ['.json', '.yaml', '.yml', '.xml', '.toml']:
        return 'Config'
    elif ext in ['.md', '.rst', '.txt']:
        return 'Documentation'
    elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico']:
        return 'Image'
    elif ext in ['.zip', '.tar', '.gz', '.7z', '.rar']:
        return 'Archive'
    else:
        return 'Other'
