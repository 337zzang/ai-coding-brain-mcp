"""검색 관련 헬퍼 함수들"""

import os
import re
import fnmatch
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from datetime import datetime
from .decorators import track_operation
from .context import get_project_context


@track_operation('file', 'scan')
def scan_directory_dict(directory_path):
    """디렉토리 스캔 - 딕셔너리 반환 버전
    
    Args:
        directory_path: 스캔할 디렉토리 경로
        
    Returns:
        dict: {
            'files': {filename: {'size': bytes, 'size_str': '1.2KB'}},
            'directories': [dirname1, dirname2, ...],
            'total_size': total_bytes,
            'stats': {
                'file_count': n,
                'dir_count': n,
                'by_extension': {'.py': count, ...}
            }
        }
    """
    # scan_directory 호출 (리스트 반환)
    scan_list = scan_directory(directory_path)
    
    result = {
        'files': {},
        'directories': [],
        'total_size': 0,
        'stats': {
            'file_count': 0,
            'dir_count': 0,
            'by_extension': {}
        }
    }
    
    for item in scan_list:
        if '[FILE]' in item:
            # "[FILE] filename.ext (123B)" 형식 파싱
            parts = item.replace('[FILE]', '').strip()
            if '(' in parts and ')' in parts:
                filename = parts[:parts.rfind('(')].strip()
                size_str = parts[parts.rfind('(')+1:parts.rfind(')')].strip()
                
                # 크기 변환 (B, KB, MB, GB)
                size_bytes = 0
                try:
                    if size_str.endswith('GB'):
                        size_bytes = int(float(size_str[:-2]) * 1024 * 1024 * 1024)
                    elif size_str.endswith('MB'):
                        size_bytes = int(float(size_str[:-2]) * 1024 * 1024)
                    elif size_str.endswith('KB'):
                        size_bytes = int(float(size_str[:-2]) * 1024)
                    elif size_str.endswith('B'):
                        size_bytes = int(float(size_str[:-1]))
                except ValueError:
                    size_bytes = 0
                
                result['files'][filename] = {
                    'size': size_bytes,
                    'size_str': size_str
                }
                result['total_size'] += size_bytes
                result['stats']['file_count'] += 1
                
                # 확장자별 통계
                if '.' in filename:
                    ext = filename[filename.rfind('.'):]
                    result['stats']['by_extension'][ext] = result['stats']['by_extension'].get(ext, 0) + 1
            else:
                # 크기 정보가 없는 경우
                filename = parts
                result['files'][filename] = {'size': 0, 'size_str': '0B'}
                result['stats']['file_count'] += 1
                
        elif '[DIR]' in item:
            dirname = item.replace('[DIR]', '').strip()
            result['directories'].append(dirname)
            result['stats']['dir_count'] += 1
    
    # 추적 업데이트
    try:
        track_file_access(directory_path, 'scan_directory_dict')
    except:
        pass
    
    return result

@track_operation('search', 'files')
def search_files_advanced(directory, pattern='*', file_extensions=None, exclude_patterns=None, 
                           case_sensitive=False, recursive=True, max_results=100, 
                           include_dirs=False, timeout_ms=30000):
    """
    고급 파일 검색 (추적 포함)
    
    Args:
        directory: 검색할 디렉토리
        pattern: 파일명 패턴 (기본: '*')
        file_extensions: 파일 확장자 필터 (미사용, 호환성 유지)
        exclude_patterns: 제외 패턴 (미사용, 호환성 유지)
        case_sensitive: 대소문자 구분 (미사용, 호환성 유지)
        recursive: 하위 디렉토리 포함 (기본: True)
        max_results: 최대 결과 수 (기본: 100)
        include_dirs: 디렉토리 포함 여부 (기본: False)
        timeout_ms: 타임아웃 (기본: 30000ms)
        
    Returns:
        dict: 검색 결과
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
        include_dirs=include_dirs, 
        timeout_ms=timeout_ms
    )
    
    # 작업 추적
    try:
        track_file_access(directory, 'search_files')
    except:
        pass
        
    return result

@track_operation('search', 'code')
def search_code_content(path: str = '.', pattern: str = '', 
                       file_pattern: str = '*', max_results: int = 50,
                       case_sensitive: bool = False, whole_word: bool = False):
    """코드 내용 검색 (추적 포함) - 원본과 동일한 시그니처
    
    Args:
        path: 검색할 경로
        pattern: 검색 패턴 (정규식 지원)
        file_pattern: 파일 패턴 (예: '*.py')
        max_results: 최대 결과 수
        case_sensitive: 대소문자 구분
        whole_word: 단어 단위 검색
    
    Returns:
        SearchHelper.search_code 결과
    """
    # ----- (1) 추적 -----
    track_file_access('search_code', path)
    
    # ----- (2) SearchHelper 호출 -----
    # _search_code_content는 search_helpers.search_code_content
    result = _search_code_content(
        path=path,
        pattern=pattern,
        file_pattern=file_pattern,
        max_results=max_results,
        case_sensitive=case_sensitive,
        whole_word=whole_word
    )
    
    # ----- (3) 결과에 추적 정보 추가 -----
    if result and 'results' in result:
        for file_result in result['results']:
            if 'file_path' in file_result:
                track_file_access('search_code', file_result['file_path'])
    
    return result

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
    print(f"   root_path: {root_path}")
    print(f"   ignore_patterns 전달값: {ignore_patterns}")
    print(f"   force_rescan: {force_rescan}")
    
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
    for i, pattern in enumerate(ignore_patterns[:10]):
        print(f"   {i+1}. {pattern}")
    if len(ignore_patterns) > 10:
        print(f"   ... 외 {len(ignore_patterns) - 10}개")
    
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
            print(f"   path: {path}")
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



