"""
AI Helpers Facade Pattern
실제 구현 - Phase 2-A 즉시 도입
생성일: 2025-08-09
"""
import warnings
from typing import Any, Optional, Dict, List
import functools

# 데코레이터와 유틸리티
def deprecated(new_path: str):
    """Deprecated 함수 데코레이터"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{func.__name__}() is deprecated. Use {new_path}() instead.",
                DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator


class FileNamespace:
    """파일 작업 관련 함수들"""

    def __init__(self):
        from . import file
        self.read = file.read
        self.write = file.write
        self.append = file.append
        self.exists = file.exists
        self.get_file_info = file.get_file_info
        self.info = file.info
        self.create_directory = file.create_directory
        self.list_directory = file.list_directory
        self.read_json = file.read_json
        self.write_json = file.write_json
        self.resolve_project_path = file.resolve_project_path
        # Deprecated 또는 없는 함수들
        self.scan_directory = file.list_directory  # 별칭
        self.move_file = None  # 없음
        self.read_multiple_files = None  # 없음

    def __repr__(self):
        return "<FileNamespace: read, write, append, exists, get_file_info, create_directory, move_file, scan_directory, read_multiple_files>"


class CodeNamespace:
    """코드 분석/수정 관련 함수들"""

    def __init__(self):
        from . import code
        self.parse = code.parse
        self.view = code.view
        self.replace = code.replace
        self.insert = code.insert
        self.functions = code.functions
        self.classes = code.classes
        self.delete = getattr(code, 'delete', None)  # Phase 1에서 누락될 수 있음

    def __repr__(self):
        return "<CodeNamespace: parse, view, replace, insert, functions, classes, delete>"


class SearchNamespace:
    """검색 관련 함수들"""

    def __init__(self):
        from . import search
        self.files = search.search_files
        self.code = search.search_code
        self.function = search.find_function
        self.class_ = search.find_class
        self.grep = search.grep
        # Phase 1에서 추가된 함수들
        self.imports = getattr(search, 'search_imports', None)
        self.statistics = getattr(search, 'get_statistics', None)

    def __repr__(self):
        return "<SearchNamespace: files, code, function, class_, grep, imports, statistics>"


class GitNamespace:
    """Git 작업 관련 함수들"""

    def __init__(self):
        from . import git
        self.status = git.git_status
        self.add = git.git_add
        self.commit = git.git_commit
        self.diff = git.git_diff
        self.log = git.git_log
        self.branch = git.git_branch
        self.checkout = git.git_checkout
        self.checkout_b = git.git_checkout_b
        self.merge = git.git_merge
        self.push = git.git_push
        self.pull = git.git_pull
        self.stash = git.git_stash
        self.reset_hard = git.git_reset_hard
        self.current_branch = git.git_current_branch
        self.status_normalized = getattr(git, 'git_status_normalized', git.git_status)

    def __repr__(self):
        return "<GitNamespace: status, add, commit, diff, log, branch, checkout, merge, push, pull, stash, reset_hard>"


class LLMNamespace:
    """LLM/O3 관련 함수들"""

    def __init__(self):
        from . import llm
        self.ask_o3 = getattr(llm, 'ask_o3', llm.ask_o3_practical)  # ask_o3가 없으면 practical 사용
        self.ask_o3_async = llm.ask_o3_async
        self.ask_o3_practical = llm.ask_o3_practical
        self.check_o3_status = llm.check_o3_status
        self.get_o3_result = llm.get_o3_result
        self.show_o3_progress = llm.show_o3_progress
        self.clear_completed_tasks = llm.clear_completed_tasks
        self.save_o3_result = getattr(llm, 'save_o3_result', None)
        self.list_o3_tasks = getattr(llm, 'list_o3_tasks', None)
        self.prepare_o3_context = getattr(llm, 'prepare_o3_context', None)
        self.quick_o3_context = getattr(llm, 'quick_o3_context', None)

        # O3ContextBuilder - 함수로 정의되어 있을 수 있음
        self.ContextBuilder = getattr(llm, 'O3ContextBuilder', None)

    def __repr__(self):
        return "<LLMNamespace: ask_o3, ask_o3_async, check_o3_status, get_o3_result, show_o3_progress, ContextBuilder>"


class FlowNamespace:
    """Flow/Task 관리 관련 함수들"""

    def __init__(self):
        from . import flow_api
        from . import ultra_simple_flow_manager as flow_mgr
        from . import task_logger

        # Flow API
        self.get_api = flow_api.get_flow_api
        self.API = flow_api.FlowAPI

        # Flow 관리 - project.py에서 가져오기
        from . import project
        self.project = project.flow_project_with_workflow
        self.select_plan_and_show = getattr(project, 'select_plan_and_show', None)

        # TaskLogger
        self.create_logger = task_logger.create_task_logger
        self.TaskLogger = task_logger.EnhancedTaskLogger

        # Flow 명령어
        from . import simple_flow_commands as flow_cmd
        self.wf = getattr(flow_cmd, 'wf', None)
        self.flow = getattr(flow_cmd, 'flow', flow_cmd.flow if hasattr(flow_cmd, 'flow') else None)

    def __repr__(self):
        return "<FlowNamespace: get_api, project, create_logger, wf, flow>"


class ProjectNamespace:
    """프로젝트 관리 관련 함수들"""

    def __init__(self):
        from . import project
        self.get_current = project.get_current_project
        self.safe_get_current = project.safe_get_current_project
        self.switch = project.flow_project_with_workflow
        self.fp = project.fp
        self.context = project.get_project_context
        self.resolve_path = project.resolve_project_path

    def __repr__(self):
        return "<ProjectNamespace: get_current, switch, fp, context, resolve_path>"


class AiHelpersFacade:
    """
    AI Helpers의 단일 진입점 (Facade Pattern)

    사용법:
        import ai_helpers_new as h

        # 새로운 방식 (권장)
        h.file.read("test.txt")
        h.code.parse("module.py")
        h.search.files("*.py")
        h.git.status()
        h.llm.ask_o3("question")
        h.flow.get_api()
        h.project.get_current()

        # 기존 방식 (deprecated but supported)
        h.read("test.txt")  # DeprecationWarning 발생
    """

    def __init__(self):
        # 네임스페이스 초기화
        self.file = FileNamespace()
        self.code = CodeNamespace()
        self.search = SearchNamespace()
        self.git = GitNamespace()
        self.llm = LLMNamespace()
        self.o3 = self.llm  # 별칭
        self.flow = FlowNamespace()
        self.project = ProjectNamespace()

        # 자주 사용하는 함수 바로가기 (권장하지 않지만 편의를 위해)
        self.get_flow_api = self.flow.get_api
        self.create_task_logger = self.flow.create_logger

        # 기존 flat API 하위 호환성
        self._setup_legacy_compatibility()

        # 사용 통계
        self._stats = {
            'facade_calls': 0,
            'legacy_calls': 0
        }

    def _setup_legacy_compatibility(self):
        """기존 flat API 스타일 지원 (deprecated)"""

        # 파일 관련
        self.read = deprecated("h.file.read")(self.file.read)
        self.write = deprecated("h.file.write")(self.file.write)
        self.append = deprecated("h.file.append")(self.file.append)
        self.exists = deprecated("h.file.exists")(self.file.exists)
        self.get_file_info = deprecated("h.file.get_file_info")(self.file.get_file_info)
        self.scan_directory = deprecated("h.file.scan_directory")(self.file.scan_directory)

        # 코드 관련
        self.parse = deprecated("h.code.parse")(self.code.parse)
        self.view = deprecated("h.code.view")(self.code.view)
        self.replace = deprecated("h.code.replace")(self.code.replace)
        self.insert = deprecated("h.code.insert")(self.code.insert)
        self.functions = deprecated("h.code.functions")(self.code.functions)
        self.classes = deprecated("h.code.classes")(self.code.classes)

        # 검색 관련
        self.search_files = deprecated("h.search.files")(self.search.files)
        self.search_code = deprecated("h.search.code")(self.search.code)
        self.find_function = deprecated("h.search.function")(self.search.function)
        self.find_class = deprecated("h.search.class_")(self.search.class_)
        self.grep = deprecated("h.search.grep")(self.search.grep)
        if self.search.imports:
            self.search_imports = deprecated("h.search.imports")(self.search.imports)
        if self.search.statistics:
            self.get_statistics = deprecated("h.search.statistics")(self.search.statistics)

        # Git 관련
        self.git_status = deprecated("h.git.status")(self.git.status)
        self.git_add = deprecated("h.git.add")(self.git.add)
        self.git_commit = deprecated("h.git.commit")(self.git.commit)
        self.git_diff = deprecated("h.git.diff")(self.git.diff)
        self.git_log = deprecated("h.git.log")(self.git.log)
        self.git_branch = deprecated("h.git.branch")(self.git.branch)
        self.git_checkout = deprecated("h.git.checkout")(self.git.checkout)
        self.git_checkout_b = deprecated("h.git.checkout_b")(self.git.checkout_b)
        self.git_merge = deprecated("h.git.merge")(self.git.merge)
        self.git_push = deprecated("h.git.push")(self.git.push)
        self.git_pull = deprecated("h.git.pull")(self.git.pull)
        self.git_stash = deprecated("h.git.stash")(self.git.stash)
        self.git_reset_hard = deprecated("h.git.reset_hard")(self.git.reset_hard)
        self.git_current_branch = deprecated("h.git.current_branch")(self.git.current_branch)
        self.git_status_normalized = deprecated("h.git.status_normalized")(self.git.status_normalized)

        # LLM/O3 관련
        self.ask_o3 = deprecated("h.llm.ask_o3")(self.llm.ask_o3)
        self.ask_o3_async = deprecated("h.llm.ask_o3_async")(self.llm.ask_o3_async)
        self.check_o3_status = deprecated("h.llm.check_o3_status")(self.llm.check_o3_status)
        self.get_o3_result = deprecated("h.llm.get_o3_result")(self.llm.get_o3_result)
        self.show_o3_progress = deprecated("h.llm.show_o3_progress")(self.llm.show_o3_progress)
        self.clear_completed_tasks = deprecated("h.llm.clear_completed_tasks")(self.llm.clear_completed_tasks)

        # Flow 관련
        self.flow_project_with_workflow = deprecated("h.flow.project")(self.flow.project)
        self.select_plan_and_show = deprecated("h.flow.select_plan_and_show")(self.flow.select_plan_and_show)
        self.wf = self.flow.wf  # wf는 유지 (짧아서)

        # Project 관련
        self.get_current_project = deprecated("h.project.get_current")(self.project.get_current)
        self.safe_get_current_project = deprecated("h.project.safe_get_current")(self.project.safe_get_current)
        self.fp = self.project.fp  # fp는 유지 (짧아서)
        self.get_project_context = deprecated("h.project.context")(self.project.context)
        self.resolve_project_path = deprecated("h.project.resolve_path")(self.project.resolve_path)

    def stats(self) -> Dict[str, Any]:
        """Facade 사용 통계"""
        return {
            'namespaces': {
                'file': 9,
                'code': 7,
                'search': 7,
                'git': 15,
                'llm': 7,
                'flow': 5,
                'project': 6
            },
            'total_organized': 55,
            'legacy_functions': 168,  # 나머지
            'usage_stats': self._stats
        }

    def __repr__(self):
        namespaces_info = """  Namespaces:
    - file: File operations (9 functions)
    - code: Code analysis/modification (7 functions)
    - search: Search utilities (7 functions)
    - git: Git operations (15 functions)
    - llm/o3: LLM integration (7 functions)
    - flow: Task/Plan management (5 functions)
    - project: Project management (6 functions)"""

        return f"""<AiHelpersFacade v2.0>
{namespaces_info}
  Legacy: 168 flat functions (deprecated)
  Usage: h.<namespace>.<function>() for new code"""


# 싱글톤 인스턴스
_facade_instance = None

def get_facade() -> AiHelpersFacade:
    """Facade 싱글톤 인스턴스 반환"""
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = AiHelpersFacade()
    return _facade_instance
