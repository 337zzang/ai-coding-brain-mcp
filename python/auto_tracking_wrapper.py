"""
자동 추적 래퍼 - v6.2
- execute_code 환경 개선
- task별 작업 추적 기능 추가
- 캐시 구조 개선
- Git 자동 커밋 통합 (v6.2)
"""
import sys
import os
import json
import functools
from datetime import datetime
from typing import Any, Dict, Optional, Callable

# Git Version Manager 통합
try:
    from git_version_manager import get_git_manager
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    
try:
    from api.public import get_current_context
    from core.context_manager import UnifiedContextManager
except ImportError:
    pass


# 캐시 저장 조건 제어를 위한 전역 변수
_operation_counter = 0
_cache_save_interval = 10  # 10회마다 저장
_excluded_operations = {'read_file', 'search_files_advanced', 'search_code_content', 'scan_directory_dict'}

# Wisdom Hooks 통합
try:
    from .wisdom_hooks import get_wisdom_hooks
    WISDOM_HOOKS_AVAILABLE = True
except ImportError:
    WISDOM_HOOKS_AVAILABLE = False

    def get_current_context():
        return None
    UnifiedContextManager = None

    def update_md_files(context):
        pass

def _get_project_context():
    """프로젝트 컨텍스트를 안전하게 가져옵니다 - execute_code 환경 최적화"""
    try:
        import __main__
        if hasattr(__main__, 'context') and isinstance(__main__.context, dict):
            return __main__.context
        if 'context' in globals() and isinstance(globals()['context'], dict):
            return globals()['context']
        frame = sys._getframe()
        for _ in range(10):
            if not frame:
                break
            if 'context' in frame.f_globals:
                ctx = frame.f_globals['context']
                if isinstance(ctx, dict):
                    return ctx
            if 'context' in frame.f_locals:
                ctx = frame.f_locals['context']
                if isinstance(ctx, dict):
                    return ctx
            frame = frame.f_back
        if UnifiedContextManager:
            manager = UnifiedContextManager()
            return manager.context
        ctx = get_current_context()
        if ctx:
            return ctx
        return {'project_name': 'unknown', 'cache_version': '6.1', 'task_tracking': {}, 'current_task': None}
    except Exception as e:
        print(f'⚠️ Context 획득 실패: {e}')
        return {'project_name': 'unknown', 'task_tracking': {}}

def track_task_operation(task_id: str, operation: str, details: Dict[str, Any]=None):
    """Task 관련 작업을 추적합니다"""
    context = _get_project_context()
    if not context:
        return
    if 'task_tracking' not in context:
        context['task_tracking'] = {}
    if task_id not in context['task_tracking']:
        context['task_tracking'][task_id] = {'operations': [], 'files_modified': set(), 'functions_edited': set(), 'start_time': datetime.now().isoformat(), 'status': 'in_progress'}
    operation_record = {'timestamp': datetime.now().isoformat(), 'operation': operation, 'details': details or {}}
    context['task_tracking'][task_id]['operations'].append(operation_record)

def track_file_operation(operation_type: str):
    """파일 작업 추적 데코레이터 - Task 연동 개선"""

    def decorator(func: Callable) -> Callable:

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            context = _get_project_context()
            current_task = context.get('current_task') if context else None
            file_path = args[0] if args else kwargs.get('path', kwargs.get('filepath', ''))
            result = func(*args, **kwargs)

            # Wisdom Hooks 체크 (create 작업 시) - 개선된 버전
            if WISDOM_HOOKS_AVAILABLE and operation_type == 'create':
                try:
                    from wisdom_hooks import get_wisdom_hooks
                    wisdom_hooks = get_wisdom_hooks()
                    file_path = args[0] if args else kwargs.get('file_path', '')
                    
                    # 실제 백업 체크
                    if file_path and os.path.exists(file_path):
                        wisdom_hooks.check_file_operation(file_path, operation_type)
                    
                    # 코드 패턴 체크 (.py 파일 제외됨)
                    content = args[1] if len(args) > 1 else kwargs.get('content', '')
                    if file_path and content and isinstance(content, str):
                        patterns = wisdom_hooks.check_code_patterns(content, file_path)
                        # 패턴 감지 시 경고는 wisdom_hooks에서 자동 출력됨
                except Exception:
                    pass

            
            # claude_code_ai_brain의 track_file_access 호출
            try:
                from api.public import track_file_access as brain_track_file_access
                brain_track_file_access(file_path, operation_type)
                # 디버그 출력
                if os.environ.get('DEBUG_TRACKING', '').lower() == 'true':
                    print(f"✅ 작업 추적됨: {operation_type} - {os.path.basename(file_path)}")
            except ImportError as e:
                if os.environ.get('DEBUG_TRACKING', '').lower() == 'true':
                    print(f"❌ Import 실패: {e}")
            except Exception as e:
                if os.environ.get('DEBUG_TRACKING', '').lower() == 'true':
                    print(f"❌ 추적 실패: {e}")
            
            if context and current_task:
                track_task_operation(current_task, f'file_{operation_type}', {'file': file_path, 'operation': operation_type, 'success': bool(result)})
                if operation_type in ['write', 'modify', 'replace']:
                    if 'task_tracking' in context and current_task in context['task_tracking']:
                        context['task_tracking'][current_task]['files_modified'].add(file_path)
            if context:
                if 'file_access_history' not in context:
                    context['file_access_history'] = []
                context['file_access_history'].append({'file': file_path, 'operation': operation_type, 'timestamp': datetime.now().isoformat(), 'task_id': current_task})
                if len(context['file_access_history']) > 100:
                    context['file_access_history'] = context['file_access_history'][-100:]
            
            # Git 자동 커밋 (v6.2)
            global _git_commit_counter
            if operation_type in ['create', 'write', 'modify', 'replace']:
                _git_commit_counter += 1
                if _git_commit_counter >= _git_commit_interval:
                    _auto_git_commit(operation_type, file_path, context)
                    _git_commit_counter = 0
            
            return result
        return wrapper
    return decorator

def track_block_operation(operation_type: str):
    """코드 블록 작업 추적 데코레이터 - Task 연동 개선"""

    def decorator(func: Callable) -> Callable:

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            context = _get_project_context()
            current_task = context.get('current_task') if context else None
            file_path = args[0] if args else kwargs.get('file_path', '')
            block_name = args[1] if len(args) > 1 else kwargs.get('block_name', '')
            result = func(*args, **kwargs)
            if context and current_task and result:
                track_task_operation(current_task, f'block_{operation_type}', {'file': file_path, 'block': block_name, 'operation': operation_type})
                if 'task_tracking' in context and current_task in context['task_tracking']:
                    context['task_tracking'][current_task]['functions_edited'].add(f'{file_path}::{block_name}')
            if context and result:
                if 'function_edit_history' not in context:
                    context['function_edit_history'] = []
                context['function_edit_history'].append({'file': file_path, 'function': block_name, 'operation': operation_type, 'timestamp': datetime.now().isoformat(), 'task_id': current_task})
                if len(context['function_edit_history']) > 50:
                    context['function_edit_history'] = context['function_edit_history'][-50:]
            
            # Git 자동 커밋 (v6.2)
            global _git_commit_counter
            if result and operation_type in ['replace', 'insert', 'modify']:
                _git_commit_counter += 1
                if _git_commit_counter >= _git_commit_interval:
                    _auto_git_commit(operation_type, file_path, context)
                    _git_commit_counter = 0
            
            return result
        return wrapper
    return decorator

def auto_update_context(func: Callable) -> Callable:
    """
    함수 실행 후 자동으로 컨텍스트를 업데이트하는 데코레이터
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        global _operation_counter
        result = func(*args, **kwargs)
        
        # 함수명 확인
        func_name = func.__name__
        
        # read/search 작업은 카운터만 증가, 저장하지 않음
        if func_name in _excluded_operations:
            _operation_counter += 1
            return result
            
        # 다른 작업들은 카운터 증가 후 조건부 저장
        _operation_counter += 1
        
        # 10회마다 또는 특정 조건에서만 저장
        if _operation_counter >= _cache_save_interval:
            import claude_code_ai_brain
            if hasattr(claude_code_ai_brain, '_context_manager') and claude_code_ai_brain._context_manager:
                try:
                    claude_code_ai_brain.save_context()
                    _operation_counter = 0  # 카운터 리셋
                except Exception:
                    pass
        
        return result
    
    return wrapper

def track_task_start(task_id: str, task_info: Dict[str, Any]):
    """Task 시작을 추적합니다"""
    context = _get_project_context()
    if not context:
        return
    context['current_task'] = task_id
    track_task_operation(task_id, 'start', task_info)

def track_task_complete(task_id: str):
    """Task 완료를 추적합니다"""
    context = _get_project_context()
    if not context:
        return
    if 'task_tracking' in context and task_id in context['task_tracking']:
        context['task_tracking'][task_id]['status'] = 'completed'
        context['task_tracking'][task_id]['end_time'] = datetime.now().isoformat()
        task_data = context['task_tracking'][task_id]
        summary = {'files_modified': list(task_data.get('files_modified', set())), 'functions_edited': list(task_data.get('functions_edited', set())), 'operation_count': len(task_data.get('operations', [])), 'duration': 'calculated_later'}
        track_task_operation(task_id, 'complete', summary)
    if context.get('current_task') == task_id:
        context['current_task'] = None

def track_file_access(file_path, operation, details=None):
    """파일 접근 추적 헬퍼 함수"""
    context = _get_project_context()
    if not context:
        return
    if 'file_access_history' not in context:
        context['file_access_history'] = []
    access_record = {'file': file_path, 'operation': operation, 'timestamp': datetime.now().isoformat(), 'task_id': context.get('current_task')}
    if details:
        access_record['details'] = details
    context['file_access_history'].append(access_record)
    if len(context['file_access_history']) > 100:
        context['file_access_history'] = context['file_access_history'][-100:]
try:
    # 절대 import로 변경하여 순환 import 문제 해결
    from file_system_helpers import read_file as _read_file, create_file as _create_file, backup_file as _backup_file, restore_backup as _restore_backup, replace_block as _replace_block, insert_block as _insert_block
    from ast_parser_helpers import parse_with_snippets as _parse_with_snippets, get_snippet_preview as _get_snippet_preview
    from search_helpers import scan_directory as _scan_directory, search_files_advanced as _search_files_advanced, search_code_content as _search_code_content
except ImportError as e:
    print(f'Warning: 일부 헬퍼 모듈을 찾을 수 없습니다: {e}')

    def _read_file(*args, **kwargs):
        raise ImportError('file_system_helpers not available')

    def _create_file(*args, **kwargs):
        raise ImportError('file_system_helpers not available')

    def _backup_file(*args, **kwargs):
        raise ImportError('file_system_helpers not available')

    def _restore_backup(*args, **kwargs):
        raise ImportError('file_system_helpers not available')

    def _replace_block(*args, **kwargs):
        raise ImportError('file_system_helpers not available')

    def _insert_block(*args, **kwargs):
        raise ImportError('file_system_helpers not available')

    def _parse_with_snippets(*args, **kwargs):
        raise ImportError('ast_parser_helpers not available')

    def _get_snippet_preview(*args, **kwargs):
        raise ImportError('ast_parser_helpers not available')

    def _scan_directory(*args, **kwargs):
        raise ImportError('search_helpers not available')

    def _search_files_advanced(*args, **kwargs):
        raise ImportError('search_helpers not available')

    def _search_code_content(*args, **kwargs):
        raise ImportError('search_helpers not available')

# ===== 추적 기능이 적용된 최종 함수 정의 =====

# 1. 일반적인 추적 함수들 (데코레이터 체이닝)
read_file = track_file_operation('read')(_read_file)
create_file = auto_update_context(track_file_operation('create')(_create_file))
restore_backup = auto_update_context(track_file_operation('restore')(_restore_backup))
replace_block = auto_update_context(track_block_operation('replace')(_replace_block))
insert_block = auto_update_context(track_block_operation('insert')(_insert_block))

# 2. backup_file: Wisdom Hooks를 위한 추가 로직이 필요하므로 별도 처리
def backup_file_wisdom_wrapper(*args, **kwargs):
    """Wisdom Hooks 추적 로직을 포함하는 내부 래퍼"""
    # file_system_helpers에서 가져온 순수 함수 호출
    result = _backup_file(*args, **kwargs)

    # 백업 성공 시 Wisdom Hooks에 기록
    if result and WISDOM_HOOKS_AVAILABLE:
        try:
            from wisdom_hooks import get_wisdom_hooks
            wisdom_hooks = get_wisdom_hooks()
            file_path = args[0] if args else kwargs.get('filepath', '')
            if file_path:
                wisdom_hooks.track_backup(file_path)
        except Exception as e:
            # 추적 오류는 전체 실행에 영향을 주지 않도록 처리
            if os.environ.get('DEBUG_TRACKING', '').lower() == 'true':
                print(f"❌ Wisdom Hook (backup) 추적 실패: {e}")

    return result

# 최종적으로 backup_file 함수에 모든 데코레이터를 적용
# 순서: task 추적 -> 컨텍스트 자동 업데이트
backup_file = auto_update_context(track_file_operation('backup')(backup_file_wisdom_wrapper))

def parse_with_snippets(file_path, language='auto', include_snippets=True):
    """파일을 파싱하여 구조화된 정보와 코드 스니펫 추출 - 자동 캐시 저장 포함"""
    import os
    from datetime import datetime
    result = _parse_with_snippets(file_path, language, include_snippets)
    if os.path.exists(file_path):
        try:
            from api.public import track_file_access
            track_file_access(file_path, 'parse')
        except:
            pass
    if result and result.get('parsing_success'):
        context = _get_project_context()
        if context:
            if 'analyzed_files' not in context:
                context['analyzed_files'] = {}
            file_info = {'path': file_path, 'language': result.get('language', 'unknown'), 'size': os.path.getsize(file_path), 'last_analyzed': datetime.now().isoformat(), 'functions': len(result.get('functions', [])), 'classes': len(result.get('classes', [])), 'imports': len(result.get('imports', [])), 'function_names': [f.get('name', '') for f in result.get('functions', [])], 'class_names': [c.get('name', '') for c in result.get('classes', [])], 'snippets': []}
            for func in result.get('functions', [])[:10]:
                file_info['snippets'].append({'type': 'function', 'name': func.get('name'), 'line_start': func.get('line_start'), 'line_end': func.get('line_end')})
            for cls in result.get('classes', []):
                file_info['snippets'].append({'type': 'class', 'name': cls.get('name'), 'line_start': cls.get('line_start'), 'line_end': cls.get('line_end')})
            context['analyzed_files'][file_path] = file_info
            if os.environ.get('DEBUG_CACHE', '').lower() == 'true':
                print(f"✅ 캐시 자동 저장: {os.path.basename(file_path)} (함수: {file_info['functions']}개, 클래스: {file_info['classes']}개)")
    return result

def get_snippet_preview(file_path, element_name, element_type='function', max_lines=10, start_line=-1, end_line=-1):
    """코드 스니펫 미리보기 (추적 포함)"""
    import os
    result = _get_snippet_preview(file_path, element_name, element_type, max_lines, start_line, end_line)
    if os.path.exists(file_path):
        try:
            from api.public import track_file_access
            track_file_access(file_path, 'preview')
        except:
            pass
    return result



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
globals()['parse_with_snippets'] = parse_with_snippets
globals()['get_snippet_preview'] = get_snippet_preview
globals()['scan_directory'] = _scan_directory
globals()['search_files_advanced'] = search_files_advanced
globals()['search_code_content'] = search_code_content
globals()['track_file_access'] = track_file_access

# ===== 폴더 구조 캐싱 함수들 =====

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
    context = _get_project_context()
    
    if not force_rescan and context:
        if 'project_structure' in context:
            cached = context['project_structure']
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
        context['project_structure'] = result
        
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


def get_directory_tree(path="/", max_depth=3, show_files=True):
    """디렉토리 트리를 텍스트로 반환
    
    Args:
        path: 시작 경로
        max_depth: 최대 깊이
        show_files: 파일 표시 여부
    
    Returns:
        str: 트리 형태의 텍스트
    """
    structure = get_project_structure()
    
    def build_tree(current_path, depth=0, prefix=""):
        if depth > max_depth:
            return ""
        
        tree = ""
        if current_path not in structure['structure']:
            return tree
            
        info = structure['structure'][current_path]
        
        # 현재 디렉토리의 하위 항목들
        children = info.get('children', [])
        files = info.get('files', []) if show_files else []
        
        # 디렉토리 출력
        for i, child in enumerate(children):
            is_last_dir = (i == len(children) - 1 and len(files) == 0)
            child_path = os.path.join(current_path, child).replace("\\", "/")
            
            connector = "└── " if is_last_dir else "├── "
            tree += f"{prefix}{connector}{child}/\n"
            
            # 재귀적으로 하위 디렉토리 처리
            extension = "    " if is_last_dir else "│   "
            tree += build_tree(child_path, depth + 1, prefix + extension)
        
        # 파일 출력 (최대 5개만)
        if show_files:
            for i, file in enumerate(files[:5]):
                is_last = (i == len(files) - 1) or (i == 4)
                connector = "└── " if is_last else "├── "
                tree += f"{prefix}{connector}{file}\n"
            
            if len(files) > 5:
                tree += f"{prefix}└── ... ({len(files) - 5}개 파일 더)\n"
        
        return tree
    
    # 루트에서 시작
    if path == "/":
        tree = "📁 프로젝트 구조\n"
    else:
        tree = f"📁 {path}\n"
    
    tree += build_tree(path, 0, "")
    return tree


def get_structure_stats():
    """프로젝트 구조 통계 정보 반환
    
    Returns:
        dict: 파일 타입별 통계, 디렉토리 깊이 등
    """
    from collections import defaultdict
    
    structure = get_project_structure()
    
    # 통계 초기화
    stats = {
        'total_files': structure['total_files'],
        'total_dirs': structure['total_dirs'],
        'file_types': defaultdict(int),
        'max_depth': 0,
        'largest_dirs': []
    }
    
    # 파일 타입별 통계
    for path, info in structure['structure'].items():
        if 'files' in info:
            for file_name in info['files']:
                ext = os.path.splitext(file_name)[1].lower()
                if ext:
                    stats['file_types'][ext] += 1
                else:
                    stats['file_types']['[no extension]'] += 1
            
            # 가장 큰 디렉토리들
            if info['file_count'] > 0:
                stats['largest_dirs'].append({
                    'path': path,
                    'file_count': info['file_count']
                })
        
        # 최대 깊이 계산
        depth = path.count('/')
        if depth > stats['max_depth']:
            stats['max_depth'] = depth
    
    # 가장 큰 디렉토리 정렬
    stats['largest_dirs'].sort(key=lambda x: x['file_count'], reverse=True)
    stats['largest_dirs'] = stats['largest_dirs'][:10]  # 상위 10개만
    
    # file_types를 일반 dict로 변환
    stats['file_types'] = dict(stats['file_types'])
    
    return stats

# 새로운 함수들을 전역에 등록
globals()['cache_project_structure'] = cache_project_structure
globals()['get_project_structure'] = get_project_structure
globals()['search_in_structure'] = search_in_structure
globals()['get_directory_tree'] = get_directory_tree
globals()['get_structure_stats'] = get_structure_stats


def force_save_context():
    """특정 명령어(/next 등)에서 즉시 캐시를 저장합니다."""
    global _operation_counter
    import claude_code_ai_brain
    if hasattr(claude_code_ai_brain, '_context_manager') and claude_code_ai_brain._context_manager:
        try:
            claude_code_ai_brain.save_context()
            print("✅ 컨텍스트 즉시 저장 완료")
        except Exception as e:
            print(f"❌ 컨텍스트 저장 실패: {e}")
    else:
        print("⚠️ ContextManager를 찾을 수 없습니다.")


def _auto_git_commit(operation_type: str, file_path: str, context: Optional[Dict] = None):
    """Git 자동 커밋 수행"""
    if not GIT_AVAILABLE:
        return
    
    # 제외할 파일 타입
    exclude_patterns = ['.log', '.tmp', '.cache', '__pycache__', '.pyc']
    if any(pattern in file_path for pattern in exclude_patterns):
        return
    
    # 중요한 작업만 자동 커밋
    commit_operations = ['create', 'write', 'modify', 'replace', 'backup']
    if operation_type not in commit_operations:
        return
    
    try:
        git_manager = get_git_manager()
        
        # 현재 상태 확인
        status = git_manager.git_status()
        if status['clean']:
            return  # 변경사항 없음
        
        # 컨텍스트 정보 가져오기
        task_info = ""
        if context and context.get('current_task'):
            task_info = f"[{context['current_task']}] "
        
        # 자동 커밋 메시지
        file_name = os.path.basename(file_path)
        message = f"{task_info}Auto: {operation_type} {file_name}"
        
        # 커밋 실행
        result = git_manager.git_commit_smart(message, auto_add=True)
        
        if result['success'] and os.environ.get('DEBUG_GIT', '').lower() == 'true':
            print(f"🔄 Git 자동 커밋: {result['commit_hash'][:8]}")
            
    except Exception as e:
        if os.environ.get('DEBUG_GIT', '').lower() == 'true':
            print(f"⚠️ Git 자동 커밋 실패: {e}")


# 자동 커밋 관련 설정
_git_commit_counter = 0
_git_commit_interval = 5  # 5회 작업마다 자동 커밋
_operation_counter = 0  # 카운터 리셋
