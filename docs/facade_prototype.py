"""
AI Helpers Facade Pattern - 프로토타입
Phase 2-A 구현 예시
"""
import warnings
from typing import Any, Optional
import functools

# 기존 모듈들 import
from . import file, code, search, git, llm, project, wrappers


class DeprecatedFunction:
    """하위 호환성을 위한 Deprecated 함수 래퍼"""

    def __init__(self, old_func, new_path: str):
        self.old_func = old_func
        self.new_path = new_path
        functools.update_wrapper(self, old_func)

    def __call__(self, *args, **kwargs):
        warnings.warn(
            f"{self.old_func.__name__}() is deprecated. "
            f"Use {self.new_path}() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.old_func(*args, **kwargs)


class FileNamespace:
    """파일 작업 관련 함수들"""

    def __init__(self):
        # 기존 함수들을 네임스페이스로 이동
        self.read = file.read
        self.write = file.write
        self.append = file.append
        self.exists = file.exists
        self.get_info = file.get_file_info
        self.scan_directory = file.scan_directory

    def __repr__(self):
        return "<FileNamespace: read, write, append, exists, get_info, scan_directory>"


class CodeNamespace:
    """코드 분석/수정 관련 함수들"""

    def __init__(self):
        self.parse = code.parse
        self.view = code.view
        self.replace = code.replace
        self.insert = code.insert
        self.functions = code.functions
        self.classes = code.classes

    def __repr__(self):
        return "<CodeNamespace: parse, view, replace, insert, functions, classes>"


class SearchNamespace:
    """검색 관련 함수들"""

    def __init__(self):
        self.files = search.search_files
        self.code = search.search_code
        self.function = search.find_function
        self.class_ = search.find_class
        self.imports = search.search_imports  # Phase 1에서 추가됨

    def __repr__(self):
        return "<SearchNamespace: files, code, function, class_, imports>"


class GitNamespace:
    """Git 작업 관련 함수들"""

    def __init__(self):
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

    def __repr__(self):
        return "<GitNamespace: status, add, commit, diff, log, branch, ...>"


class FlowNamespace:
    """Flow/Task 관리 관련 함수들"""

    def __init__(self):
        from . import ultra_simple_flow_manager as flow_mgr
        self.api = flow_mgr.get_flow_api
        self.project = flow_mgr.flow_project_with_workflow
        self.create_logger = flow_mgr.create_task_logger

    def __repr__(self):
        return "<FlowNamespace: api, project, create_logger>"


class AiHelpersFacade:
    """
    AI Helpers의 단일 진입점 (Facade Pattern)

    사용법:
        from ai_helpers_new import helpers

        # 새로운 방식 (권장)
        helpers.file.read("test.txt")
        helpers.code.parse("module.py")
        helpers.search.files("*.py")

        # 기존 방식 (deprecated but supported)
        helpers.read("test.txt")  # DeprecationWarning 발생
    """

    def __init__(self):
        # 네임스페이스 초기화
        self.file = FileNamespace()
        self.code = CodeNamespace()
        self.search = SearchNamespace()
        self.git = GitNamespace()
        self.flow = FlowNamespace()

        # O3/LLM은 그대로 유지 (복잡도 때문에)
        self.ask_o3 = llm.ask_o3
        self.ask_o3_async = llm.ask_o3_async
        self.get_o3_result = llm.get_o3_result

        # 프로젝트 관리
        self.get_current_project = project.get_current_project

        # 기존 flat API 하위 호환성 (deprecated)
        self._setup_legacy_compatibility()

    def _setup_legacy_compatibility(self):
        """기존 flat API 스타일 지원 (deprecated)"""

        # 파일 관련
        self.read = DeprecatedFunction(self.file.read, "helpers.file.read")
        self.write = DeprecatedFunction(self.file.write, "helpers.file.write")
        self.append = DeprecatedFunction(self.file.append, "helpers.file.append")
        self.exists = DeprecatedFunction(self.file.exists, "helpers.file.exists")

        # 코드 관련
        self.parse = DeprecatedFunction(self.code.parse, "helpers.code.parse")
        self.replace = DeprecatedFunction(self.code.replace, "helpers.code.replace")
        self.insert = DeprecatedFunction(self.code.insert, "helpers.code.insert")

        # 검색 관련
        self.search_files = DeprecatedFunction(self.search.files, "helpers.search.files")
        self.search_code = DeprecatedFunction(self.search.code, "helpers.search.code")
        self.find_function = DeprecatedFunction(self.search.function, "helpers.search.function")
        self.find_class = DeprecatedFunction(self.search.class_, "helpers.search.class_")

        # Git 관련
        self.git_status = DeprecatedFunction(self.git.status, "helpers.git.status")
        self.git_commit = DeprecatedFunction(self.git.commit, "helpers.git.commit")

    def stats(self) -> dict:
        """Facade 사용 통계"""
        return {
            'namespaces': ['file', 'code', 'search', 'git', 'flow'],
            'total_functions': 223,  # 기존 개수
            'organized_functions': {
                'file': 6,
                'code': 6,
                'search': 5,
                'git': 11,
                'flow': 3,
                'llm': 3,
                'legacy': 189  # 아직 정리 안 된 것들
            }
        }

    def __repr__(self):
        return (
            "<AiHelpersFacade>
"
            "  Namespaces: file, code, search, git, flow
"
            "  O3/LLM: ask_o3, ask_o3_async, get_o3_result
"
            "  Legacy: 189 functions (deprecated)
"
            "Use helpers.<namespace>.<function>() for new code"
        )


# 싱글톤 인스턴스
_facade_instance = None

def get_facade() -> AiHelpersFacade:
    """Facade 싱글톤 인스턴스 반환"""
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = AiHelpersFacade()
    return _facade_instance


# 사용 예시
if __name__ == "__main__":
    helpers = get_facade()

    # 새로운 방식
    content = helpers.file.read("test.txt")
    helpers.code.parse("module.py")
    results = helpers.search.files("*.py")

    # 기존 방식 (경고 발생)
    content_old = helpers.read("test.txt")  # DeprecationWarning

    # 통계
    print(helpers.stats())
