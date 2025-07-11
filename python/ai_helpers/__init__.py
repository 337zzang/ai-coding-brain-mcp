"""
AI Helpers - 통합 헬퍼 모듈 v14.0 (Simplified)
단순화되고 명확한 import 구조
"""
import logging
import sys
import os
from typing import Dict, Any, List, Optional

# 로깅 설정
logger = logging.getLogger("ai_helpers")
logger.setLevel(logging.INFO)

# Helper Result - 가장 먼저 import
from .helper_result import HelperResult

# File 관련
from .file import (
    read_file, write_file, create_file, append_to_file
)

# Git 관련
from .git import (
    git_status, git_add, git_commit, git_push, git_pull,
    git_branch, git_log, git_diff, git_stash, git_stash_pop,
    git_commit_smart, git_branch_smart, is_git_repository, git_init,
    GIT_AVAILABLE
)

# Search 관련 - 하위 모듈에서 직접 import
from .search.directory_scan import (
    scan_directory,
    scan_directory_dict,
    cache_project_structure,
    get_project_structure,
    search_in_structure
)

from .search.file_search import (
    search_files_advanced,
    _search_files_advanced
)

from .search.code_search import (
    search_code_content,
    _search_code_content
)

from .search.unified import (
    list_file_paths,
    grep_code,
    scan_dir
)

# Search wrappers
from .search_wrappers import (
    search_code, find_class, find_function, find_import
)

# Optional 모듈들 - try/except로 처리
# Compile 관련
try:
    from .compile import (
        check_syntax, compile_project, parse_code, parse_with_snippets,
        replace_block, insert_block, get_snippet_preview
    )
except ImportError as e:
    logger.warning(f"⚠️ compile 모듈 로드 실패: {e}")

# Build 관련
try:
    from .build import build_project
except ImportError as e:
    logger.warning(f"⚠️ build 모듈 로드 실패: {e}")

# Code 관련
try:
    from .code import (
        ASTParser, EnhancedFunctionReplacer, FunctionReplacer,
        ClassReplacer, BlockInsertTransformer
    )
except ImportError as e:
    logger.warning(f"⚠️ code 모듈 로드 실패: {e}")

# Context 관련
try:
    from .context import (
        get_context, save_context, update_context, initialize_context,
        get_project_context, track_file_operation, track_function_edit,
        track_operation
    )
except ImportError as e:
    logger.warning(f"⚠️ context 모듈 로드 실패: {e}")

# Project 관련
try:
    from .project import (
        detect_project_type, install_dependencies, get_project_progress,
        get_system_summary
    )
except ImportError as e:
    logger.warning(f"⚠️ project 모듈 로드 실패: {e}")

# Utils 관련
try:
    from .utils import (
        get_current_phase, complete_current_phase, create_standard_phases,
        quick_task, task, complete, progress, reset_project, update_cache,
        get_cache_value, track_file_access, get_value, safe_print
    )
except ImportError as e:
    logger.warning(f"⚠️ utils 모듈 로드 실패: {e}")

# Legacy replacements
try:
    from .legacy_replacements import (
        cmd_flow, get_current_project, list_functions, list_tasks,
        get_pending_tasks, get_work_tracking_summary, get_event_history,
        run_command, get_flow_instance, edit_block, update_symbol_index,
        get_verbose, set_verbose
    )
except ImportError as e:
    logger.warning(f"⚠️ legacy_replacements 모듈 로드 실패: {e}")

# API 관련
try:
    from .api import toggle_api, list_apis, check_api_enabled
except ImportError as e:
    logger.warning(f"⚠️ api 모듈 로드 실패: {e}")

# Workflow 함수 정의
def workflow(command: str):
    """워크플로우 명령어 실행"""
    try:
        # workflow.v3 패키지 경로 추가
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        from workflow.v3 import execute_workflow_command
        return execute_workflow_command(command)
    except Exception as e:
        return HelperResult(False, error=str(e))

# Flow 관련 함수들
def flow_project(project_name: str) -> Dict[str, Any]:
    """프로젝트 전환"""
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
            
        from enhanced_flow import cmd_flow_with_context
        result = cmd_flow_with_context(project_name)
        return HelperResult(ok=True, data=result, error=None)
    except Exception as e:
        logger.error(f"flow_project 실행 실패: {e}")
        return HelperResult(ok=False, data=None, error=str(e))

def start_project(project_name: str, init_git: bool = True) -> Dict[str, Any]:
    """새 프로젝트 생성"""
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
            
        from enhanced_flow import start_project as _start_project_func
        result = _start_project_func(project_name, init_git)
        return result
    except Exception as e:
        logger.error(f"start_project 실행 실패: {e}")
        return {'success': False, 'error': f"프로젝트 생성 실패: {str(e)}"}

# 모듈 로드 상태 추적
_load_status = {
    'core': True,  # helper_result, file, git, search는 필수
    'optional': {}  # 선택적 모듈들의 로드 상태
}

def get_load_status() -> Dict[str, Any]:
    """모듈 로드 상태 반환"""
    return _load_status

# __all__ 정의 - 명시적으로 export할 항목들
__all__ = [
    # Core
    'HelperResult',
    
    # File operations
    'read_file', 'write_file', 'create_file', 'append_to_file',
    'scan_directory', 'scan_directory_dict',
    
    # Git operations
    'git_status', 'git_add', 'git_commit', 'git_push', 'git_pull',
    'git_branch', 'git_log', 'git_diff', 'git_stash', 'git_stash_pop',
    'git_commit_smart', 'git_branch_smart', 'is_git_repository', 'git_init',
    'GIT_AVAILABLE',
    
    # Search operations
    'search_files_advanced', '_search_files_advanced',
    'search_code_content', '_search_code_content',
    'cache_project_structure', 'get_project_structure', 'search_in_structure',
    'list_file_paths', 'grep_code', 'scan_dir',
    'search_code', 'find_class', 'find_function', 'find_import',
    
    # Workflow
    'workflow', 'flow_project', 'start_project',
    
    # Utilities
    'get_load_status',
]

# Optional 모듈의 함수들도 __all__에 추가 (존재하는 경우에만)
optional_exports = [
    # Compile
    'check_syntax', 'compile_project', 'parse_code', 'parse_with_snippets',
    'replace_block', 'insert_block', 'get_snippet_preview',
    
    # Build
    'build_project',
    
    # Code
    'ASTParser', 'EnhancedFunctionReplacer', 'FunctionReplacer',
    'ClassReplacer', 'BlockInsertTransformer',
    
    # Context
    'get_context', 'save_context', 'update_context', 'initialize_context',
    'get_project_context', 'track_file_operation', 'track_function_edit',
    'track_operation',
    
    # Project
    'detect_project_type', 'install_dependencies', 'get_project_progress',
    'get_system_summary',
    
    # Utils
    'get_current_phase', 'complete_current_phase', 'create_standard_phases',
    'quick_task', 'task', 'complete', 'progress', 'reset_project',
    'update_cache', 'get_cache_value', 'track_file_access', 'get_value',
    'safe_print',
    
    # Legacy
    'cmd_flow', 'get_current_project', 'list_functions', 'list_tasks',
    'get_pending_tasks', 'get_work_tracking_summary', 'get_event_history',
    'run_command', 'get_flow_instance', 'edit_block', 'update_symbol_index',
    'get_verbose', 'set_verbose',
    
    # API
    'toggle_api', 'list_apis', 'check_api_enabled',
]

# 실제로 로드된 함수만 __all__에 추가
for name in optional_exports:
    if name in globals():
        __all__.append(name)

logger.info(f"AI Helpers 초기화 완료 - {len(__all__)}개 함수 export")
