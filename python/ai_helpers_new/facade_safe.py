"""
AI Helpers Facade Pattern - 안전한 버전 (HelperResult 최적화)
Phase 2-A 구현 + REPL 최적화
"""
import warnings
from typing import Any, Optional
import functools
import importlib

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
        """안전하게 속성 가져오고, 함수인 경우 safe_execution 래핑 적용
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
                # 함수인 경우 래퍼 적용
                wrapped = safe_execution(attr)
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

        # 디렉토리 작업
        self.create_directory = self._safe_getattr('create_directory')
        self.list_directory = self._safe_getattr('list_directory')
        _list_dir = self._safe_getattr('list_directory')
        self.scan_directory = self._safe_getattr('scan_directory', _list_dir)

        # JSON 작업
        self.read_json = self._safe_getattr('read_json')
        self.write_json = self._safe_getattr('write_json')

        # 경로 작업
        self.resolve_project_path = self._safe_getattr('resolve_project_path')


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

        self.files = self._safe_getattr('search_files')
        self.code = self._safe_getattr('search_code')
        self.function = self._safe_getattr('find_function')
        self.class_ = self._safe_getattr('find_class')
        self.grep = self._safe_getattr('grep')

        # Phase 1에서 추가된 함수
        self.imports = self._safe_getattr('search_imports')
        self.statistics = self._safe_getattr('get_statistics')


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
    """웹 자동화 관련 함수들"""
    def __init__(self):
        super().__init__('web')
        if self._get_module() is None: return

        # 웹 자동화 함수들
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

        # Project 네임스페이스  
        self.project = ProjectNamespace()


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
        """레거시 함수들 직접 노출 - 모두 HelperResult 반환"""

        # 각 모듈에서 필요한 함수들 가져오기
        modules = {}
        for mod_name in ['file', 'code', 'search', 'git', 'project', 'llm']:
            try:
                modules[mod_name] = importlib.import_module(f'.{mod_name}', 'ai_helpers_new')
            except ImportError:
                modules[mod_name] = None

        # File 함수들 (HelperResult 래핑)
        if modules['file']:
            self.read = self._wrap_legacy_function(getattr(modules['file'], 'read', None))
            self.write = self._wrap_legacy_function(getattr(modules['file'], 'write', None))
            self.append = self._wrap_legacy_function(getattr(modules['file'], 'append', None))
            self.exists = self._wrap_legacy_function(getattr(modules['file'], 'exists', None))
            self.get_file_info = self._wrap_legacy_function(getattr(modules['file'], 'get_file_info', None))

        # Code 함수들 (HelperResult 래핑)
        if modules['code']:
            self.parse = self._wrap_legacy_function(getattr(modules['code'], 'parse', None))
            self.view = self._wrap_legacy_function(getattr(modules['code'], 'view', None))
            self.replace = self._wrap_legacy_function(getattr(modules['code'], 'replace', None))
            self.insert = self._wrap_legacy_function(getattr(modules['code'], 'insert', None))
            self.functions = self._wrap_legacy_function(getattr(modules['code'], 'functions', None))
            self.classes = self._wrap_legacy_function(getattr(modules['code'], 'classes', None))

        # Search 함수들 (HelperResult 래핑)
        if modules['search']:
            s = modules['search']
            self.search_files = self._wrap_legacy_function(getattr(s, 'search_files', None))
            self.search_code = self._wrap_legacy_function(getattr(s, 'search_code', None))
            self.find_function = self._wrap_legacy_function(getattr(s, 'find_function', None))
            self.find_class = self._wrap_legacy_function(getattr(s, 'find_class', None))
            self.grep = self._wrap_legacy_function(getattr(s, 'grep', None))
            self.search_imports = self._wrap_legacy_function(getattr(s, 'search_imports', None))
            self.get_statistics = self._wrap_legacy_function(getattr(s, 'get_statistics', None))

        # Git 함수들 (HelperResult 래핑)
        if modules['git']:
            g = modules['git']
            self.git_status = self._wrap_legacy_function(getattr(g, 'git_status', None))
            self.git_add = self._wrap_legacy_function(getattr(g, 'git_add', None))
            self.git_commit = self._wrap_legacy_function(getattr(g, 'git_commit', None))
            self.git_diff = self._wrap_legacy_function(getattr(g, 'git_diff', None))
            self.git_log = self._wrap_legacy_function(getattr(g, 'git_log', None))
            self.git_branch = self._wrap_legacy_function(getattr(g, 'git_branch', None))
            self.git_checkout = self._wrap_legacy_function(getattr(g, 'git_checkout', None))
            self.git_checkout_b = self._wrap_legacy_function(getattr(g, 'git_checkout_b', None))
            self.git_merge = self._wrap_legacy_function(getattr(g, 'git_merge', None))
            self.git_push = self._wrap_legacy_function(getattr(g, 'git_push', None))
            self.git_pull = self._wrap_legacy_function(getattr(g, 'git_pull', None))

        # Project 함수들 (HelperResult 래핑)
        if modules['project']:
            p = modules['project']
            self.get_current_project = self._wrap_legacy_function(getattr(p, 'get_current_project', None))
            self.flow_project_with_workflow = self._wrap_legacy_function(getattr(p, 'flow_project_with_workflow', None))
            self.select_plan_and_show = self._wrap_legacy_function(getattr(p, 'select_plan_and_show', None))
            self.fix_task_numbers = self._wrap_legacy_function(getattr(p, 'fix_task_numbers', None))
            self.flow_project = self._wrap_legacy_function(getattr(p, 'flow_project', None))
            self.project_info = self._wrap_legacy_function(getattr(p, 'project_info', None))
            self.list_projects = self._wrap_legacy_function(getattr(p, 'list_projects', None))

        # LLM 함수들 (HelperResult 래핑)
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

        try:
            from . import task_logger
            self.create_task_logger = task_logger.create_task_logger
        except ImportError:
            self.create_task_logger = None

    def __repr__(self):
        return (
            "<AiHelpersFacade - HelperResult Optimized v2.0>\n"
            "  Usage: h.<namespace>.<function>() or h.<function>()\n"
            "  Namespaces: file, code, search, git, llm, o3\n"
            "  ✨ All functions return HelperResult for clean REPL output!"
        )


# 싱글톤 인스턴스
_facade_instance = None

def get_facade() -> AiHelpersFacade:
    """Facade 싱글톤 인스턴스 반환 - HelperResult 버전"""
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = AiHelpersFacade()
    return _facade_instance