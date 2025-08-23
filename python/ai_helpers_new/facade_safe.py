"""
AI Helpers Facade Pattern - 안전한 버전 (HelperResult 최적화)
Phase 2-A 구현 + REPL 최적화
"""
import warnings
from typing import Any, Optional
import functools
import importlib
import os

# wrappers에서 필요한 것들 임포트
try:
    from .wrappers import safe_execution, ensure_response, HelperResult
except ImportError:
    print("Warning: wrappers module not found. Using fallback.")
    # 폴백 정의
    safe_execution = lambda f: f
    HelperResult = dict
    def ensure_response(data, error=None, **kwargs):
        if error:
            return {'ok': False, 'error': error, 'data': None}
        return {'ok': True, 'data': data}


class SafeNamespace:
    """안전한 네임스페이스 기본 클래스
    모든 함수 호출에 safe_execution 래퍼를 자동으로 적용합니다.
    """
    def __init__(self, module_name: str):
        self._module_name = module_name
        self._module = None
        self._wrapped_cache = {}  # 래핑된 함수 캐시

    def _get_module(self):
        if self._module is None:
            try:
                self._module = importlib.import_module(f'.{self._module_name}', 'ai_helpers_new')
            except ImportError as e:
                print(f"Warning: Failed to load module {self._module_name}: {e}")
                return None
        return self._module

    def _safe_getattr(self, name: str, default=None):
        """안전하게 속성 가져오고, 함수인 경우 safe_execution + 표준화 래핑 적용
        결과적으로 모든 함수가 HelperResult를 반환하도록 보장합니다.
        """
        # 캐시 확인
        if name in self._wrapped_cache:
            return self._wrapped_cache[name]

        module = self._get_module()
        if module is None:
            # 모듈 로드 실패 시 에러 반환 함수
            def error_func(*args, **kwargs):
                return HelperResult({
                    'ok': False, 
                    'error': f'Module {self._module_name} not available',
                    'data': None
                })
            return error_func

        try:
            attr = getattr(module, name, default)

            if callable(attr):
                # 함수인 경우 safe_execution + 표준화 래퍼 적용
                from .wrappers import standardize_api_response
                wrapped = standardize_api_response(safe_execution(attr))
                # 캐시에 저장
                self._wrapped_cache[name] = wrapped
                return wrapped
            return attr
        except AttributeError:
            return default

    def _ensure_helper_result(self, func):
        """함수의 반환값을 HelperResult로 보장하는 래퍼"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # ensure_response를 사용하여 HelperResult로 변환
            return ensure_response(result)
        return wrapper



class FileNamespace(SafeNamespace):
    """파일 작업 관련 함수들 - 모든 함수가 HelperResult 반환"""
    def __init__(self):
        super().__init__('file')
        if self._get_module() is None: return

        # 기본 파일 작업
        self.read = self._safe_getattr('read')
        self.write = self._safe_getattr('write')
        self.append = self._safe_getattr('append')
        self.exists = self._safe_getattr('exists')
        self.info = self._safe_getattr('info')
        self.get_file_info = self._safe_getattr('get_file_info')

        # 디렉토리 작업 (list_directory는 평탄화 적용)
        self.create_directory = self._safe_getattr('create_directory')
        self.list_directory = self._create_flattened_list_directory()
        self.list_files = self._safe_getattr('list_files')
        self.list_dirs = self._safe_getattr('list_dirs')
        self.scan_directory = self._safe_getattr('scan_directory')

        # JSON 작업
        self.read_json = self._safe_getattr('read_json')
        self.write_json = self._safe_getattr('write_json')

        # 백업 파일 정리
        self.cleanup_backups = self._safe_getattr('cleanup_backups')
        self.remove_backups = self._safe_getattr('remove_backups')

        # 경로 작업
        self.resolve_project_path = self._safe_getattr('resolve_project_path')

    def _create_flattened_list_directory(self):
        """list_directory를 평탄화된 형태로 래핑"""
        original_func = self._safe_getattr('list_directory')
        
        @functools.wraps(original_func)
        def flattened_list_directory(*args, **kwargs):
            result = original_func(*args, **kwargs)
            
            # 성공한 경우 평탄화 적용
            if result and result.get('ok') and isinstance(result.get('data'), dict):
                from .wrappers import flatten_list_directory_response
                return flatten_list_directory_response(result)
            
            return result
        
        return flattened_list_directory


class CodeNamespace(SafeNamespace):
    """코드 분석/수정 관련 함수들 - 모든 함수가 HelperResult 반환"""
    def __init__(self):
        super().__init__('code')
        if self._get_module() is None: return

        self.parse = self._safe_getattr('parse')
        self.view = self._safe_getattr('view')
        self.replace = self._safe_getattr('replace')
        self.insert = self._safe_getattr('insert')
        self.functions = self._safe_getattr('functions')
        self.classes = self._safe_getattr('classes')
        self.delete = self._safe_getattr('delete')


class SearchNamespace(SafeNamespace):
    """검색 관련 함수들 - 모든 함수가 HelperResult 반환"""
    def __init__(self):
        super().__init__('search')
        if self._get_module() is None: return

        # 개선된 검색 함수들 (에러 처리 표준화)
        self.files = self._create_improved_search_files()
        self.code = self._create_improved_search_code()
        self.grep = self._safe_getattr('grep')
        self.imports = self._safe_getattr('search_imports')
        self.statistics = self._safe_getattr('get_statistics')

    def _create_improved_search_files(self):
        """search_files를 개선된 에러 처리로 래핑"""
        original_func = getattr(getattr(self._get_module(), 'SearchNamespace', type('', (), {}))(), 'files', None)
        
        @functools.wraps(original_func)
        def improved_search_files(*args, **kwargs):
            result = original_func(*args, **kwargs)
            
            # 빈 결과를 에러로 처리하지 않고 성공으로 변경
            if result and not result.get('ok') and result.get('data') == []:
                return HelperResult({'ok': True, 'data': []})
            
            return result
        
        return improved_search_files

    def _create_improved_search_code(self):
        """search_code를 개선된 에러 처리로 래핑"""
        original_func = self._safe_getattr('search_code')
        
        @functools.wraps(original_func)
        def improved_search_code(*args, **kwargs):
            result = original_func(*args, **kwargs)
            
            # 빈 결과를 에러로 처리하지 않고 성공으로 변경
            if result and not result.get('ok') and result.get('data') == []:
                return HelperResult({'ok': True, 'data': []})
            
            return result
        
        return improved_search_code


class GitNamespace(SafeNamespace):
    """Git 작업 관련 함수들 - 모든 함수가 HelperResult 반환"""
    def __init__(self):
        super().__init__('git')
        if self._get_module() is None: return

        # 기본 Git 명령어
        self.status = self._safe_getattr('git_status')
        self.add = self._safe_getattr('git_add')
        self.commit = self._safe_getattr('git_commit')
        self.diff = self._safe_getattr('git_diff')
        self.log = self._safe_getattr('git_log')

        # 브랜치 관련
        self.branch = self._safe_getattr('git_branch')
        self.checkout = self._safe_getattr('git_checkout')
        self.checkout_b = self._safe_getattr('git_checkout_b')
        self.merge = self._safe_getattr('git_merge')

        # 원격 저장소
        self.push = self._safe_getattr('git_push')
        self.pull = self._safe_getattr('git_pull')

        # 추가 기능
        self.stash = self._safe_getattr('git_stash')
        self.reset = self._safe_getattr('git_reset')
        self.status_normalized = self._safe_getattr('git_status_normalized')
        self.current_branch = self._safe_getattr('current_branch')
        self.get_current_branch = self.current_branch  # 별칭 추가 (테스트 호환성)


class LLMNamespace(SafeNamespace):
    """LLM/O3 작업을 위한 네임스페이스 - 모든 함수가 HelperResult 반환"""
    def __init__(self):
        super().__init__('llm')
        if self._get_module() is None: return

        # O3 기본 함수들
        self.ask = self._safe_getattr('ask_o3_practical')
        self.ask_async = self._safe_getattr('ask_o3_async')
        self.ask_practical = self._safe_getattr('ask_o3_practical')

        # 결과 관리
        self.get_result = self._safe_getattr('get_o3_result')
        self.check_status = self._safe_getattr('check_o3_status')
        self.show_progress = self._safe_getattr('show_o3_progress')

        # 작업 관리
        self.clear_completed = self._safe_getattr('clear_completed_tasks')

    def create_context(self):
        """O3 Context Builder 생성"""
        try:
            from .llm import O3ContextBuilder
            return O3ContextBuilder()
        except ImportError:
            return HelperResult({
                'ok': False,
                'error': 'O3ContextBuilder not available',
                'data': None
            })



class WebNamespace(SafeNamespace):
    """웹 자동화 관련 함수들 - 새로운 모듈 구조 통합"""
    def __init__(self):
        # 새로운 web 모듈 우선 시도
        try:
            # SimpleWebAutomation 사용 (WebAutomation은 없음)
            from .web import (
                SimpleWebAutomation,
                start as web_start, goto as web_goto, 
                click as web_click, type_text as web_type,
                close as web_close, screenshot as web_screenshot,
                execute_js as web_execute_js, list_sessions as web_list_sessions
            )

            # SimpleWebAutomation 인스턴스 생성
            self._web_instance = SimpleWebAutomation()
            self._using_new_module = True

            # 기존 API와 호환되는 메서드들
            self.start = web_start
            self.goto = web_goto
            self.click = web_click
            self.type = web_type
            self.close = web_close
            self.screenshot = web_screenshot
            self.execute_js = web_execute_js
            self.list_sessions = web_list_sessions

            # 새로운 메서드들 - SimpleWebAutomation과 호환
            from .web import wait, get_page_info, get_current_session, set_current_session
            self.wait = wait
            self.get_info = get_page_info
            self.cleanup = web_close

            # 세션 관리
            self.get_current_session = get_current_session
            self.set_current_session = set_current_session

            print("[WebNamespace] Using new web module structure")

        except ImportError as e:
            # 폴백: 기존 web.py 사용
            print(f"[WebNamespace] Falling back to legacy web.py: {e}")
            super().__init__('web')
            self._using_new_module = False

            if self._get_module() is None: 
                return

            # 기존 web.py 함수들
            self.start = self._safe_getattr('web_start')
            self.goto = self._safe_getattr('web_goto')
            self.click = self._safe_getattr('web_click')
            self.type = self._safe_getattr('web_type')
            self.extract = self._safe_getattr('web_extract')
            self.screenshot = self._safe_getattr('web_screenshot')
            self.execute_js = self._safe_getattr('web_execute_js')
            self.wait = self._safe_getattr('web_wait')
            self.close = self._safe_getattr('web_close')
            self.list_sessions = self._safe_getattr('web_list_sessions')

            # 오버레이 관련 (레거시)
            self.get_overlay_actions = self._safe_getattr('web_get_overlay_actions')
            self.record_action = self._safe_getattr('web_record_action')
            self.replay_actions = self._safe_getattr('web_replay_actions')
            self.activate_overlay = self._safe_getattr('web_activate_overlay')
            self.check_and_activate_overlay = self._safe_getattr('web_check_and_activate_overlay')
            self.streaming_setup = self._safe_getattr('web_streaming_setup')
            self.stop_stream = self._safe_getattr('web_stop_stream')
            self.get_stream_data = self._safe_getattr('web_get_stream_data')
            self.record_start = self._safe_getattr('web_record_start')
            self.record_stop = self._safe_getattr('web_record_stop')
            self.get_recorded_actions = self._safe_getattr('web_get_recorded_actions')
            self.save_recording = self._safe_getattr('web_save_recording')
            self.load_recording = self._safe_getattr('web_load_recording')
            self.execute_js_safe = self._safe_getattr('web_execute_js_safe')
            self.create_recorder = self._safe_getattr('web_create_recorder')
            self.debug_info = self._safe_getattr('web_debug_info')
            self.get_page_metrics = self._safe_getattr('web_get_page_metrics')

    def __repr__(self):
        module_type = "new" if getattr(self, '_using_new_module', False) else "legacy"
        return f"<WebNamespace using {module_type} module>"


class ProjectNamespace(SafeNamespace):
    """프로젝트 관리 관련 함수들"""
    def __init__(self):
        super().__init__('project')
        if self._get_module() is None: return

        # 프로젝트 관리 함수들
        self.get_current = self._safe_getattr('get_current_project')
        self.switch = self._safe_getattr('flow_project_with_workflow')
        self.flow_project = self._safe_getattr('flow_project')
        self.select_plan = self._safe_getattr('select_plan_and_show')
        self.select_plan_and_show = self._safe_getattr('select_plan_and_show')
        self.list_projects = self._safe_getattr('list_projects')
        self.scan_directory = self._safe_getattr('scan_directory')
        self.info = self._safe_getattr('project_info')
        self.fix_task_numbers = self._safe_getattr('fix_task_numbers')
        
        # list() 메서드 추가 (list_projects의 별칭)
        self.list = self.list_projects if self.list_projects else lambda: {'ok': False, 'error': 'list_projects not available'}
        
        # get_context 메서드 추가
        get_project_context_func = self._safe_getattr('get_project_context')
        if get_project_context_func:
            # get_project_context는 ProjectContext 객체를 반환하므로 래핑 필요
            def wrapped_get_context():
                try:
                    context_obj = get_project_context_func()
                    if context_obj:
                        return HelperResult({
                            'ok': True, 
                            'data': {
                                'current_project': context_obj.get_project_name() or 'Unknown',
                                'project_path': str(context_obj._project_path) if context_obj._project_path else None,
                                'base_path': str(context_obj._base_path) if context_obj._base_path else None
                            }
                        })
                    return HelperResult({'ok': False, 'error': 'No context available'})
                except Exception as e:
                    return HelperResult({'ok': False, 'error': str(e)})
            self.get_context = wrapped_get_context
        else:
            # 폴백: get_current_project 사용
            get_current = self._safe_getattr('get_current_project')
            if get_current:
                self.get_context = lambda: get_current()
            else:
                self.get_context = lambda: HelperResult({'ok': False, 'error': 'Context not available'})


class MemoryNamespace(SafeNamespace):
    """Claude Code 메모리 연동 관련 함수들 - 현재 비활성화"""
    def __init__(self):
        # memory_sync 모듈이 제거되어 더미 네임스페이스로 유지
        super().__init__('dummy_memory')
        # 모든 메서드는 사용 불가 메시지 반환
        self.sync_with_flow = lambda *args, **kwargs: {'ok': False, 'error': 'Memory sync module not available'}
        self.get_suggestions = lambda *args, **kwargs: {'ok': False, 'error': 'Memory sync module not available'}
        self.save_context = lambda *args, **kwargs: {'ok': False, 'error': 'Memory sync module not available'}
        self.create_sync = lambda *args, **kwargs: {'ok': False, 'error': 'Memory sync module not available'}


class ContextNamespace(SafeNamespace):
    """컨텍스트 캡처 네임스페이스 - 현재 비활성화"""
    def __init__(self):
        # context_capture 모듈이 제거되어 더미 네임스페이스로 유지
        super().__init__('dummy_context')
        # 모든 메서드는 사용 불가 메시지 반환
        self.BrowserContextCapture = lambda *args, **kwargs: {'ok': False, 'error': 'Context capture module not available'}
        self.start_capture = lambda *args, **kwargs: {'ok': False, 'error': 'Context capture module not available'}
        self.capture_and_print = lambda *args, **kwargs: {'ok': False, 'error': 'Context capture module not available'}
        self.quick_start = lambda *args, **kwargs: {'ok': False, 'error': 'Context capture module not available'}


class UnifiedNamespace(SafeNamespace):
    """Flow + Claude Code 통합 관련 함수들"""
    def __init__(self):
        # unified_sync 모듈을 사용하되, 없으면 더미로 처리
# DEPRECATED:         super().__init__('unified_sync')
        
        # 모듈이 없으면 더미 함수들로 설정
        if self._get_module() is None:
            self.create_todo = lambda *args, **kwargs: {'ok': False, 'error': 'Unified sync module not available'}
            self.sync_status = lambda *args, **kwargs: {'ok': False, 'error': 'Unified sync module not available'}
            self.migrate_session = lambda *args, **kwargs: {'ok': False, 'error': 'Unified sync module not available'}
            self.get_status = lambda *args, **kwargs: {'ok': False, 'error': 'Unified sync module not available'}
            self.create_sync = lambda *args, **kwargs: {'ok': False, 'error': 'Unified sync module not available'}
        else:
            # 통합 동기화 함수들 (현재 비활성화)
            pass
# DEPRECATED:             self.create_todo = self._safe_getattr('unified_create_todo')
# DEPRECATED:             self.sync_status = self._safe_getattr('unified_sync_status')
# DEPRECATED:             self.migrate_session = self._safe_getattr('unified_migrate_session')
# DEPRECATED:             self.get_status = self._safe_getattr('get_unified_status')
# DEPRECATED:             self.create_sync = self._safe_getattr('create_unified_sync')


class ExcelNamespace(SafeNamespace):
    """Excel 자동화 네임스페이스 (Windows COM 기반)
    pywin32를 사용한 Excel 조작 기능을 제공합니다.
    """
    def __init__(self):
        super().__init__('excel')
        module = self._get_module()
        if module is None:
            # 모듈이 없을 때 기본 동작
            self.connect = lambda *args, **kwargs: {'ok': False, 'error': 'Excel module not available'}
            self.read = lambda *args, **kwargs: {'ok': False, 'error': 'Excel module not available'}
            self.write = lambda *args, **kwargs: {'ok': False, 'error': 'Excel module not available'}
            self.close = lambda *args, **kwargs: {'ok': False, 'error': 'Excel module not available'}
            self.create_sheet = lambda *args, **kwargs: {'ok': False, 'error': 'Excel module not available'}
            self.delete_sheet = lambda *args, **kwargs: {'ok': False, 'error': 'Excel module not available'}
            self.list_sheets = lambda *args, **kwargs: {'ok': False, 'error': 'Excel module not available'}
            self.format_range = lambda *args, **kwargs: {'ok': False, 'error': 'Excel module not available'}
            self.execute_macro = lambda *args, **kwargs: {'ok': False, 'error': 'Excel module not available'}
        else:
            # Excel 작업 함수들
            self.connect = self._safe_getattr('connect')
            self.read = self._safe_getattr('read')
            self.write = self._safe_getattr('write')
            self.close = self._safe_getattr('close')
            self.create_sheet = self._safe_getattr('create_sheet')
            self.delete_sheet = self._safe_getattr('delete_sheet')
            self.list_sheets = self._safe_getattr('list_sheets')
            self.format_range = self._safe_getattr('format_range')
            self.execute_macro = self._safe_getattr('execute_macro')


class AiHelpersFacade:
    """
    AI Helpers의 단일 진입점 (Facade Pattern) - HelperResult 버전
    모든 함수가 HelperResult를 반환합니다.
    """

    def __init__(self):
        # 네임스페이스 초기화
        self.file = FileNamespace()
        self.code = CodeNamespace()
        self.search = SearchNamespace()
        self.git = GitNamespace()

        # LLM/O3 네임스페이스
        self.llm = LLMNamespace()
        self.o3 = self.llm  # o3는 llm의 별칭

        # Web 네임스페이스
        self.web = WebNamespace()
        
        # Context Capture 추가
        self.context = ContextNamespace()

        # Project 네임스페이스  
        self.project = ProjectNamespace()
        
        # Memory 네임스페이스 (NEW!)
        self.memory = MemoryNamespace()
        
        # Unified 네임스페이스 (Flow + Claude 통합)
# DEPRECATED:         self.unified = UnifiedNamespace()

        # 기존 함수들 직접 import (하위 호환성)
        self._setup_legacy_functions()

    def _wrap_legacy_function(self, func):
        """레거시 함수를 HelperResult 반환하도록 래핑"""
        if not callable(func):
            return func

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)

                if isinstance(result, HelperResult):
                    return result

                if isinstance(result, dict) and 'ok' in result:
                    return HelperResult(result)

                return HelperResult({'ok': True, 'data': result})

            except Exception as e:
                return HelperResult({
                    'ok': False,
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'data': None,
                    'function': func.__name__
                })

        return wrapper

    def _setup_legacy_functions(self):
        """레거시 함수들 직접 노출 - 최소한만 유지 (하위 호환성)"""

        # 각 모듈에서 필요한 함수들 가져오기
        modules = {}
        for mod_name in ['project', 'llm']:
            try:
                modules[mod_name] = importlib.import_module(f'.{mod_name}', 'ai_helpers_new')
            except ImportError:
                modules[mod_name] = None

        # Project 함수들 (하위 호환성 유지 필요)
        if modules['project']:
            p = modules['project']
            self.get_current_project = self._wrap_legacy_function(getattr(p, 'get_current_project', None))
            self.flow_project_with_workflow = self._wrap_legacy_function(getattr(p, 'flow_project_with_workflow', None))
            self.select_plan_and_show = self._wrap_legacy_function(getattr(p, 'select_plan_and_show', None))
            self.fix_task_numbers = self._wrap_legacy_function(getattr(p, 'fix_task_numbers', None))
            self.flow_project = self._wrap_legacy_function(getattr(p, 'flow_project', None))
            self.project_info = self._wrap_legacy_function(getattr(p, 'project_info', None))
            self.list_projects = self._wrap_legacy_function(getattr(p, 'list_projects', None))

        # LLM 함수들 (하위 호환성 유지 필요)
        if modules['llm']:
            l = modules['llm']
            self.ask_o3 = self._wrap_legacy_function(getattr(l, 'ask_o3_practical', None))
            self.ask_o3_async = self._wrap_legacy_function(getattr(l, 'ask_o3_async', None))
            self.get_o3_result = self._wrap_legacy_function(getattr(l, 'get_o3_result', None))
            self.check_o3_status = self._wrap_legacy_function(getattr(l, 'check_o3_status', None))
            self.show_o3_progress = self._wrap_legacy_function(getattr(l, 'show_o3_progress', None))
            self.clear_completed_tasks = self._wrap_legacy_function(getattr(l, 'clear_completed_tasks', None))

        # Flow API와 TaskLogger는 객체 반환이므로 래핑하지 않음
        try:
            from . import flow_api
            self.get_flow_api = flow_api.get_flow_api
        except ImportError:
            self.get_flow_api = None

        # task_logger 모듈 제거됨
        self.create_task_logger = None

    def __repr__(self):
        return (
            "<AiHelpersFacade - HelperResult Optimized v2.0>\n"
            "  Usage: h.<namespace>.<function>() or h.<function>()\n"
# DEPRECATED:             "  Namespaces: file, code, search, git, llm, o3, memory, unified\n"
            "  ✨ All functions return HelperResult for clean REPL output!\n"
# DEPRECATED:             "  🔄 NEW: unified.* for Flow + Claude Code integration!"
        )


# 싱글톤 인스턴스
_facade_instance = None

def get_facade() -> AiHelpersFacade:
    """Facade 싱글톤 인스턴스 반환 - HelperResult 버전"""
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = AiHelpersFacade()
    return _facade_instance