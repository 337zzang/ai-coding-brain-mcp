"""
AI Helpers Facade Pattern - 최소 작동 버전
Phase 2-A 구현
"""
import warnings
from typing import Any, Dict
import functools


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
        self.info = file.info
        self.get_file_info = file.get_file_info
        self.create_directory = file.create_directory
        self.list_directory = file.list_directory
        self.read_json = file.read_json
        self.write_json = file.write_json


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


class AiHelpersFacade:
    """AI Helpers의 단일 진입점 (Facade Pattern) - 최소 버전"""
    
    def __init__(self):
        # 네임스페이스 초기화
        self.file = FileNamespace()
        self.code = CodeNamespace()
        self.search = SearchNamespace()
        self.git = GitNamespace()
        
        # LLM 네임스페이스 (간단한 버전)
        class SimpleLLM:
            pass
        self.llm = SimpleLLM()
        self.o3 = self.llm  # 별칭
        
        # Flow 네임스페이스 (간단한 버전)
        class SimpleFlow:
            pass
        self.flow = SimpleFlow()
        
        # Project 네임스페이스 (간단한 버전)
        class SimpleProject:
            pass
        self.project = SimpleProject()
        
        # LLM 관련 (네임스페이스와 직접 노출)
        from . import llm
        self.llm.ask_o3_async = llm.ask_o3_async
        self.llm.ask_o3_practical = llm.ask_o3_practical
        self.llm.check_o3_status = llm.check_o3_status
        self.llm.get_o3_result = llm.get_o3_result
        self.llm.show_o3_progress = llm.show_o3_progress
        self.llm.clear_completed_tasks = llm.clear_completed_tasks
        # 직접 노출도 유지
        self.ask_o3_async = llm.ask_o3_async
        self.ask_o3_practical = llm.ask_o3_practical
        self.check_o3_status = llm.check_o3_status
        self.get_o3_result = llm.get_o3_result
        self.show_o3_progress = llm.show_o3_progress
        self.clear_completed_tasks = llm.clear_completed_tasks
        
        # Flow 관련 (네임스페이스와 직접 노출)
        from . import flow_api
        self.flow.get_api = flow_api.get_flow_api
        # 직접 노출도 유지
        self.get_flow_api = flow_api.get_flow_api
        
        # Project 관련 (네임스페이스와 직접 노출)
        from . import project
        self.project.get_current = project.get_current_project
        # 직접 노출도 유지
        self.get_current_project = project.get_current_project
        # fp는 다른 모듈에 있을 수 있음
        self.fp = getattr(project, 'fp', None)
        
        # 기존 flat API 하위 호환성
        self._setup_legacy_compatibility()
    
    def _setup_legacy_compatibility(self):
        """기존 flat API 스타일 지원 (deprecated)"""
        
        # 파일 관련
        self.read = deprecated("h.file.read")(self.file.read)
        self.write = deprecated("h.file.write")(self.file.write)
        self.append = deprecated("h.file.append")(self.file.append)
        self.exists = deprecated("h.file.exists")(self.file.exists)
        
        # 코드 관련
        self.parse = deprecated("h.code.parse")(self.code.parse)
        self.replace = deprecated("h.code.replace")(self.code.replace)
        self.insert = deprecated("h.code.insert")(self.code.insert)
        
        # 검색 관련
        self.search_files = deprecated("h.search.files")(self.search.files)
        self.search_code = deprecated("h.search.code")(self.search.code)
        self.find_function = deprecated("h.search.function")(self.search.function)
        self.find_class = deprecated("h.search.class_")(self.search.class_)
        
        # Git 관련
        self.git_status = deprecated("h.git.status")(self.git.status)
        self.git_commit = deprecated("h.git.commit")(self.git.commit)
        
        # LLM 관련
        self.ask_o3 = deprecated("h.ask_o3_practical")(self.ask_o3_practical)
    
    def stats(self) -> Dict[str, Any]:
        """Facade 사용 통계"""
        return {
            'namespaces': {
                'file': 10,
                'code': 6,
                'search': 7,
                'git': 11
            },
            'total_organized': 34,
            'legacy_functions': 189  # 나머지
        }
    
    def __repr__(self):
        return """<AiHelpersFacade v2.0 - Minimal>
  Namespaces:
    - file: File operations (10 functions)
    - code: Code analysis/modification (6 functions)
    - search: Search utilities (7 functions)
    - git: Git operations (11 functions)
  Direct: ask_o3_*, get_flow_api, get_current_project
  Legacy: Deprecated flat functions
  Usage: h.<namespace>.<function>() for new code"""


# 싱글톤 인스턴스
_facade_instance = None

def get_facade() -> AiHelpersFacade:
    """Facade 싱글톤 인스턴스 반환"""
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = AiHelpersFacade()
    return _facade_instance
