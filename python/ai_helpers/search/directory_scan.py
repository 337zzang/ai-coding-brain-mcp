"""
디렉토리 스캔 전문 모듈

디렉토리 구조를 스캔하고 분석하는 기능을 제공합니다.
"""

import os
import time
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

def scan_directory_dict(directory_path):
    """디렉토리 스캔 - 딕셔너리 반환 버전

    Args:
        directory_path: 스캔할 디렉토리 경로

    Returns:
        HelperResult: 성공 시 data에 {
            'files': [{'name': str, 'path': str, 'size': int}],
            'directories': [{'name': str, 'path': str}],
            'total_size': total_bytes,
            'stats': {
                'file_count': n,
                'dir_count': n,
                'by_extension': {'.py': count, ...}
            }
        }
    """
    try:
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

        directory_path = Path(directory_path).resolve()

        if not directory_path.exists():
            return HelperResult(ok=False, data=None, error=f"디렉토리가 존재하지 않음: {directory_path}")

        if not directory_path.is_dir():
            return HelperResult(ok=False, data=None, error=f"디렉토리가 아님: {directory_path}")

        for item in directory_path.iterdir():
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
                        result['stats']['by_extension'][ext] = result['stats']['by_extension'].get(ext, 0) + 1

                elif item.is_dir():
                    result['directories'].append({
                        'name': item.name,
                        'path': str(item)
                    })
                    result['stats']['dir_count'] += 1

            except (PermissionError, OSError):
                continue

        return HelperResult(ok=True, data=result, error=None)

    except Exception as e:
        return HelperResult(ok=False, data=None, error=f"디렉토리 스캔 실패: {str(e)}")


def cache_project_structure(root_path=".", ignore_patterns=None, force_rescan=False):
    """프로젝트 구조를 스캔하고 캐시에 저장
    
    Args:
        root_path: 스캔할 루트 경로
        ignore_patterns: 무시할 패턴 리스트
        force_rescan: 강제 재스캔 여부
    
    Returns:
        dict: 프로젝트 구조 정보
    """
    import fnmatch
    from datetime import datetime
    from pathlib import Path
    
    # DEBUG: print("\n🔍 DEBUG: cache_project_structure 시작")
    # print(f"   root_path: {root_path}")  # MCP JSON 응답 오염 방지
    # print(f"   ignore_patterns 전달값: {ignore_patterns}")  # MCP JSON 응답 오염 방지
    # print(f"   force_rescan: {force_rescan}")  # MCP JSON 응답 오염 방지
    
    # 기본 무시 패턴
    # 기본 무시 패턴 - 더 포괄적으로 개선
    if ignore_patterns is None:
        ignore_patterns = [
            # Python 관련
            "__pycache__", "*.pyc", "*.pyo", "*.pyd", ".Python",
            ".pytest_cache", ".mypy_cache", 
            
            # 가상환경
            ".venv", "venv", "ENV", "env",
            
            # 빌드/배포
            "dist", "build", "*.egg-info", "node_modules",
            
            # 버전 관리
            ".git", ".svn", ".hg",
            
            # IDE/에디터
            ".vscode", ".idea", "*.swp", "*.swo",
            
            # 백업/임시 파일 - 중요!
            "backup", "backups", "*.bak", "*.backup",
            ".mcp_backup_*", "backup_*", "backup_test_suite",
            
            # 테스트 - 중요!
            "test", "tests", "test_*", "*_test",
            
            # 캐시/세션 - 중요!
            ".cache", ".ai_cache", "cache", ".sessions",
            "session_cache",
            
            # 로그
            "logs", "*.log",
            
            # 데이터베이스
            "*.db", "*.sqlite*", "chroma_db",
            
            # 기타
            ".vibe", "output", "tmp", "temp"
        ]
    
    # DEBUG: print(f"\n📋 DEBUG: 무시 패턴 ({len(ignore_patterns)}개):")
    # for i, pattern in enumerate(ignore_patterns[:10]):
    #     print(f"   {i+1}. {pattern}")  # MCP JSON 응답 오염 방지
    # if len(ignore_patterns) > 10:
    #     print(f"   ... 외 {len(ignore_patterns) - 10}개")  # MCP JSON 응답 오염 방지
    
    # 캐시 확인
    cache_key = "project_structure"
    context = get_project_context()
    
    if not force_rescan and context:
        if 'project_structure' in context:
            cached = context.metadata.get('project_structure', {})
        else:
            # _context_manager를 통해서도 확인
            try:
                from core.context_manager import get_context_manager
                _context_manager = get_context_manager()
                if _context_manager and hasattr(_context_manager, 'get_value'):
                    cached = _context_manager.get_value(cache_key)
                else:
                    cached = None
            except:
                cached = None
        
        if cached:
            # 캐시 유효성 검사 (24시간)
            try:
                last_scan = datetime.fromisoformat(cached['last_scan'])
                age_hours = (datetime.now() - last_scan).total_seconds() / 3600
                
                if age_hours < 24:
                    print(f"✅ 캐시된 구조 사용 (스캔 후 {age_hours:.1f}시간 경과)")
                    return cached
            except:
                pass
    
    # 새로 스캔
    print("🔍 프로젝트 구조 스캔 중...")
    structure = {}
    total_files = 0
    total_dirs = 0
    
    def should_ignore(path):
        """경로가 무시 패턴에 매치되는지 확인"""
        import fnmatch
        
        # 처음 10번만 디버깅
        if not hasattr(should_ignore, 'call_count'):
            should_ignore.call_count = 0
        
        if should_ignore.call_count < 10:
            # DEBUG: print(f"\n🔍 DEBUG: should_ignore 호출 #{should_ignore.call_count + 1}")
            # print(f"   path: {path}")  # MCP JSON 응답 오염 방지
            should_ignore.call_count += 1
        path_str = str(path)
        path_parts = Path(path).parts
        path_name = Path(path).name
        
        # 디버깅: 처음 몇 개만 출력
        global debug_count
        if 'debug_count' not in globals():
            debug_count = 0
        
        for pattern in ignore_patterns:
            # 와일드카드 패턴 처리
            if '*' in pattern or '?' in pattern:
                # 파일명에 대해 패턴 매칭
                if fnmatch.fnmatch(path_name, pattern):
                    if debug_count < 5:
                        print(f"   🚫 Ignored (wildcard): {path_name} matches {pattern}")
                        debug_count += 1
                    return True
            else:
                # 정확한 매칭 (디렉토리 이름 등)
                if pattern in path_parts:
                    if debug_count < 5:
                        print(f"   🚫 Ignored (exact): {pattern} in {path_parts}")
                        debug_count += 1
                    return True
                # 파일명 매칭
                if path_name == pattern:
                    if debug_count < 5:
                        print(f"   🚫 Ignored (name): {path_name} == {pattern}")
                        debug_count += 1
                    return True
        
        return False
    def scan_recursive(dir_path, relative_path="/"):
        """디렉토리를 재귀적으로 스캔"""
        nonlocal total_files, total_dirs
        
        if should_ignore(dir_path):
            return
        
        try:
            items = os.listdir(dir_path)
            dirs = []
            files = []
            
            for item in items:
                item_path = os.path.join(dir_path, item)
                if os.path.isdir(item_path):
                    if not should_ignore(item_path):
                        dirs.append(item)
                        total_dirs += 1
                else:
                    if not should_ignore(item_path):
                        files.append(item)
                        total_files += 1
            
            # 현재 디렉토리 정보 저장
            structure[relative_path] = {
                "type": "directory",
                "children": sorted(dirs),
                "files": sorted(files),
                "file_count": len(files),
                "dir_count": len(dirs),
                "last_modified": os.path.getmtime(dir_path)
            }
            
            # 하위 디렉토리 스캔
            for dir_name in dirs:
                sub_dir_path = os.path.join(dir_path, dir_name)
                sub_relative_path = os.path.join(relative_path, dir_name).replace("\\", "/")
                scan_recursive(sub_dir_path, sub_relative_path)
                
        except PermissionError:
            structure[relative_path] = {
                "type": "directory",
                "error": "Permission denied"
            }
    
    # 스캔 시작
    root_abs = os.path.abspath(root_path)
    scan_recursive(root_abs, "/")
    
    result = {
        "root": root_abs,
        "last_scan": datetime.now().isoformat(),
        "total_files": total_files,
        "total_dirs": total_dirs,
        "structure": structure
    }
    
    # 캐시에 저장
    if context:
        context.metadata['project_structure'] = result
        
        # _context_manager를 통해서도 저장
        try:
            from core.context_manager import get_context_manager
            _context_manager = get_context_manager()
            if _context_manager and hasattr(_context_manager, 'update_cache'):
                _context_manager.update_cache(cache_key, result)
        except:
            pass
        
        print(f"💾 구조 캐시 저장 완료 ({total_files}개 파일, {total_dirs}개 디렉토리)")
    
    return result


def get_project_structure(force_rescan=False):
    """캐시된 프로젝트 구조 반환 (필요시 자동 스캔)
    
    Args:
        force_rescan: 강제 재스캔 여부
    
    Returns:
        dict: 프로젝트 구조 정보
    """
    return cache_project_structure(force_rescan=force_rescan)


def search_in_structure(pattern, search_type="all"):
    """캐시된 구조에서 파일/디렉토리 검색
    
    Args:
        pattern: 검색 패턴 (glob 형식)
        search_type: "file", "dir", "all"
    
    Returns:
        list: 검색 결과 리스트
    """
    import fnmatch
    import os
    
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
                        'dir': path
                    })
    
    return results


