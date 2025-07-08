"""검색 관련 헬퍼 함수들"""
from .helper_result import HelperResult

import os
import re
import fnmatch
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from datetime import datetime
from ai_helpers.decorators import track_operation
from ai_helpers.context import get_project_context
from ai_helpers.utils import track_file_access



def scan_directory(path: str = '.', level: int = 1) -> List[str]:
    """
    디렉토리를 재귀적으로 스캔하여 파일 목록 반환
    
    Args:
        path: 스캔할 디렉토리 경로
        level: 스캔 깊이 (1 = 현재 디렉토리만, -1 = 무제한)
    
    Returns:
        List[str]: 파일 경로 리스트
    """
    files = []
    try:
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isfile(item_path):
                files.append(item_path)
            elif os.path.isdir(item_path) and level != 1:
                next_level = level - 1 if level > 1 else -1
                files.extend(scan_directory(item_path, next_level))
    except (PermissionError, OSError):
        pass
    return files

@track_operation('file', 'scan')
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

@track_operation('search', 'code')
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
