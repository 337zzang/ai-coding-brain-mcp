"""
AI Helpers Facade Pattern - 안전한 버전
Phase 2-A 구현
"""
import warnings
from typing import Any, Optional
import functools


class SafeNamespace:
    """안전한 네임스페이스 기본 클래스"""
    def __init__(self, module_name: str):
        self._module_name = module_name
        self._module = None
        
    def _get_module(self):
        if self._module is None:
            import importlib
            self._module = importlib.import_module(f'.{self._module_name}', 'ai_helpers_new')
        return self._module
        
    def _safe_getattr(self, name: str, default=None):
        """안전하게 속성 가져오기"""
        try:
            module = self._get_module()
            return getattr(module, name, default)
        except (ImportError, AttributeError):
            return default


class FileNamespace(SafeNamespace):
    """파일 작업 관련 함수들"""
    def __init__(self):
        super().__init__('file')
        module = self._get_module()
        
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
        self.scan_directory = self._safe_getattr('scan_directory', self.list_directory)
        
        # JSON 작업
        self.read_json = self._safe_getattr('read_json')
        self.write_json = self._safe_getattr('write_json')
        
        # 경로 작업
        self.resolve_project_path = self._safe_getattr('resolve_project_path')


class CodeNamespace(SafeNamespace):
    """코드 분석/수정 관련 함수들"""
    def __init__(self):
        super().__init__('code')
        
        self.parse = self._safe_getattr('parse')
        self.view = self._safe_getattr('view')
        self.replace = self._safe_getattr('replace')
        self.insert = self._safe_getattr('insert')
        self.functions = self._safe_getattr('functions')
        self.classes = self._safe_getattr('classes')
        self.delete = self._safe_getattr('delete')


class SearchNamespace(SafeNamespace):
    """검색 관련 함수들"""
    def __init__(self):
        super().__init__('search')
        
        self.files = self._safe_getattr('search_files')
        self.code = self._safe_getattr('search_code')
        self.function = self._safe_getattr('find_function')
        self.class_ = self._safe_getattr('find_class')
        self.grep = self._safe_getattr('grep')
        
        # Phase 1에서 추가된 함수
        self.imports = self._safe_getattr('search_imports')
        self.statistics = self._safe_getattr('get_statistics')


class GitNamespace(SafeNamespace):
    """Git 작업 관련 함수들"""
    def __init__(self):
        super().__init__('git')
        
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


class AiHelpersFacade:
    """
    AI Helpers의 단일 진입점 (Facade Pattern) - 안전한 버전
    
    사용법:
        import ai_helpers_new as h
        
        # 새로운 방식 (권장)
        h.file.read("test.txt")
        h.code.parse("module.py")
        h.search.files("*.py")
        
        # 기존 방식 (여전히 지원)
        h.read("test.txt")
    """
    
    def __init__(self):
        # 네임스페이스 초기화
        self.file = FileNamespace()
        self.code = CodeNamespace()
        self.search = SearchNamespace()
        self.git = GitNamespace()
        
        # 기존 함수들 직접 import (하위 호환성)
        self._setup_legacy_functions()
        
    def _setup_legacy_functions(self):
        """레거시 함수들 직접 노출"""
        # 각 모듈에서 필요한 함수들 가져오기
        try:
            from . import file, code, search, git, project, llm
            
            # File 함수들
            self.read = file.read
            self.write = file.write
            self.append = file.append
            self.exists = file.exists
            self.get_file_info = file.get_file_info
            
            # Code 함수들
            self.parse = code.parse
            self.view = code.view
            self.replace = code.replace
            self.insert = code.insert
            self.functions = code.functions
            self.classes = code.classes
            
            # Search 함수들
            self.search_files = search.search_files
            self.search_code = search.search_code
            self.find_function = search.find_function
            self.find_class = search.find_class
            self.grep = search.grep
            
            # Git 함수들
            self.git_status = git.git_status
            self.git_add = git.git_add
            self.git_commit = git.git_commit
            self.git_diff = git.git_diff
            self.git_log = git.git_log
            self.git_branch = git.git_branch
            self.git_checkout = git.git_checkout
            self.git_checkout_b = git.git_checkout_b
            self.git_merge = git.git_merge
            self.git_push = git.git_push
            self.git_pull = git.git_pull
            
            # Project 함수들
            self.get_current_project = project.get_current_project
            self.flow_project_with_workflow = project.flow_project_with_workflow
            
            # LLM 함수들
            self.ask_o3 = getattr(llm, 'ask_o3', None)
            self.ask_o3_async = getattr(llm, 'ask_o3_async', None)
            self.get_o3_result = getattr(llm, 'get_o3_result', None)
            self.check_o3_status = getattr(llm, 'check_o3_status', None)
            self.show_o3_progress = getattr(llm, 'show_o3_progress', None)
            self.clear_completed_tasks = getattr(llm, 'clear_completed_tasks', None)
            
            # Flow API
            try:
                from . import flow_api
                self.get_flow_api = flow_api.get_flow_api
            except ImportError:
                self.get_flow_api = None
                
            # TaskLogger
            try:
                from . import task_logger
                self.create_task_logger = task_logger.create_task_logger
            except ImportError:
                self.create_task_logger = None
                
            # 추가 함수들 - Phase 1에서 추가된 것들
            self.search_imports = getattr(search, 'search_imports', None)
            self.get_statistics = getattr(search, 'get_statistics', None)
                
        except ImportError as e:
            print(f"Warning: Some modules could not be imported: {e}")
    
    def __repr__(self):
        return (
            "<AiHelpersFacade>\n"
            "  Namespaces: file, code, search, git\n"
            "  Legacy functions: Available for compatibility\n"
            "Use h.<namespace>.<function>() for new code"
        )


# 싱글톤 인스턴스
_facade_instance = None

def get_facade() -> AiHelpersFacade:
    """Facade 싱글톤 인스턴스 반환"""
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = AiHelpersFacade()
    return _facade_instance
