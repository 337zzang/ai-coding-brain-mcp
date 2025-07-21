"""
AI Helpers v2.0 - 통합 헬퍼 모듈
"""

# 기본 imports
from typing import Dict, Any, List, Optional
from .util import ok, err, is_ok, get_data, get_error
from .file import read, write, append, read_json, write_json, exists, info, list_directory
from .code import parse, view, replace, insert, functions, classes
from .search import search_files, search_code, find_function, find_class, grep, find_in_file
from .llm import (
    ask_o3_async, check_o3_status, get_o3_result, 
    save_o3_result,
    show_o3_progress, list_o3_tasks, clear_completed_tasks, prepare_o3_context
)

# Git 함수들
from .git import (
    git_status, git_add, git_commit, git_push, git_pull, 
    git_branch, git_current_branch, git_log, git_diff
)

# Project 함수들  
from .project import (
    get_current_project as _get_current_project_raw,
    detect_project_type,
    scan_directory as _scan_directory_raw,
    scan_directory_dict as _scan_directory_dict_raw,
    create_project_structure,
    fp, flow_project, flow_project_with_workflow
)

# Workflow
from .workflow_manager import (
    WorkflowManager, get_workflow_manager, wf
)
from .context_workflow_manager import ContextWorkflowManager, create_context_workflow_manager


# Flow Project
# Flow project functions are now in project.py
# 모든 public 함수 export
__all__ = [
    # Util
    'ok', 'err', 'is_ok', 'get_data', 'get_error',

    # File
    'read', 'write', 'append', 'read_json', 'write_json', 'exists', 'info', 'list_directory',

    # Code
    'parse', 'view', 'replace', 'insert', 'functions', 'classes',

    # Search
    'search_files', 'search_code', 'find_function', 'find_class', 'grep', 'find_in_file',

    # LLM
    'ask_o3_async', 'check_o3_status', 'get_o3_result',
    'show_o3_progress', 'list_o3_tasks', 'clear_completed_tasks', 'prepare_o3_context',

    # Git
    'git_status', 'git_add', 'git_commit', 'git_push', 'git_pull',
    'git_branch', 'git_current_branch', 'git_log', 'git_diff',

    # Project
    'get_current_project', 'detect_project_type',
    'scan_directory', 'scan_directory_dict', 'create_project_structure',

    # Flow Project
    'fp', 'flow_project', 'flow_project_with_workflow',

    # Workflow
    'WorkflowManager', 'get_workflow_manager', 'wf',
    'ContextWorkflowManager', 'create_context_workflow_manager'
]

# 버전 정보
__version__ = "2.0.0"

# 모듈 정보
def help():
    """AI Helpers v2.0 도움말"""
    return """
AI Helpers v2.0 - 주요 함수:

📁 파일 작업:
  - read(path) / write(path, content) / append(path, content)
  - read_json(path) / write_json(path, data)
  - exists(path) / info(path)

📝 코드 분석/수정:
  - parse(path) / view(path, name)
  - replace(path, old, new) / insert(path, marker, code)
  - functions(path) / classes(path)

🔍 검색:
  - search_files(pattern, path) / search_code(pattern, path)
  - find_function(name, path) / find_class(name, path)
  - grep(pattern, path) / find_in_file(file, pattern)

🤖 LLM:
  - ask_o3(question) / ask_o3_async(question)
  - check_o3_status(task_id) / get_o3_result(task_id)
  - show_o3_progress() / list_o3_tasks()

🔀 Git:
  - git_status() / git_add(files) / git_commit(message)
  - git_push() / git_pull() / git_branch(name)
  - git_log(limit) / git_diff(file)

📂 프로젝트:
  - get_current_project() / scan_directory(path)
  - scan_directory_dict(path) / create_project_structure(name)

모든 함수는 {'ok': bool, 'data': Any} 형식의 dict를 반환합니다.
"""


# ========== API 표준화 래핑 (v2.1) ==========
# project.py의 비표준 함수들을 ok/err 패턴으로 표준화
# 원본 함수는 .raw 속성으로 접근 가능 (하위 호환성)

def scan_directory(path: str = '.') -> Dict[str, Any]:
    """디렉토리 스캔 - 표준 응답 패턴"""
    try:
        files = _scan_directory_raw(path)
        return ok(files, count=len(files), path=path)
    except Exception as e:
        return err(f"scan_directory failed: {str(e)}", path=path)

def scan_directory_dict(path: str = '.', max_depth: int = 3) -> Dict[str, Any]:
    """디렉토리 구조를 딕셔너리로 - 표준 응답 패턴"""
    try:
        structure = _scan_directory_dict_raw(path, max_depth)
        return ok(structure, path=path, max_depth=max_depth)
    except Exception as e:
        return err(f"scan_directory_dict failed: {str(e)}", path=path)

def get_current_project() -> Dict[str, Any]:
    """현재 프로젝트 정보 - 표준 응답 패턴"""
    try:
        project_info = _get_current_project_raw()
        return ok(project_info)
    except Exception as e:
        return err(f"get_current_project failed: {str(e)}")

# 원본 함수 노출 (하위 호환성)
scan_directory.raw = _scan_directory_raw
scan_directory_dict.raw = _scan_directory_dict_raw
get_current_project.raw = _get_current_project_raw

print("[AI Helpers v2.1] API standardization completed")

from .context_manager import ContextManager
