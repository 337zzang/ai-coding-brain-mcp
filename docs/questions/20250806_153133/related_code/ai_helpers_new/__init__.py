
# 방어적 import 헬퍼
def _safe_import(module_path, names, package=None):
    """안전한 import - 실패 시 기본값 반환"""
    results = {}
    try:
        # __import__는 package 키워드 인자를 지원하지 않음
        # package는 상대 import 시 현재 패키지명으로 사용
        if package and module_path.startswith('.'):
            # 상대 import를 절대 import로 변환
            full_module_path = package + module_path
            module = __import__(full_module_path, fromlist=names)
        else:
            module = __import__(module_path, fromlist=names)

        for name in names:
            try:
                results[name] = getattr(module, name)
            except AttributeError:
                print(f"[WARNING] {name} not found in {module_path}")
                # 기본 함수 생성
                results[name] = lambda *args, **kwargs: {
                    "ok": False, 
                    "error": f"{name} not available"
                }
    except ImportError as e:
        print(f"[WARNING] Failed to import {module_path}: {e}")
        # 모든 이름에 대해 기본값 설정
        for name in names:
            results[name] = lambda *args, **kwargs: {
                "ok": False,
                "error": f"{module_path} not available"
            }

    return results


"""
AI Helpers New - Ultra Simple Flow System
Flow 개념 없이 Plan만으로 작업하는 극단순 시스템
"""

# 도메인 모델 (Flow 제외)
from .domain.models import Plan, Task, TaskStatus

# Ultra Simple Manager
from .ultra_simple_flow_manager import UltraSimpleFlowManager

# Flow 명령어 시스템
# 방어적 import
_flow_imports = _safe_import('.simple_flow_commands', ['flow'], __package__)
flow = _flow_imports.get('flow', lambda x: {"ok": False, "error": "flow not available"})
from .flow_api import get_flow_api, FlowAPI
from .flow_api import FlowAPI
from .task_logger import EnhancedTaskLogger, create_task_logger, display_plan_tasks

# Core 모듈
from .core import *

# AI Helpers 핵심 함수들
from .file import *
from .code import *
from .search import *
from .git import (
    git_status, git_add, git_commit, git_push,
    git_pull, git_branch, git_current_branch, git_log,
    git_diff, git_checkout, git_checkout_b, git_stash,
    git_stash_pop, git_stash_list, git_reset_hard, git_merge,
    git_branch_d, git_rebase
)
from .llm import *
from .util import *
from .project import *
from .wrappers import *
from .helpers_integration import *
from .context_integration import *
from .context_reporter import *
from .doc_context_helper import *
from .backup_utils import *
from .excel import *

# 편의 함수
def get_flow_manager(project_path=None):
    return UltraSimpleFlowManager(project_path)

__all__ = [
    'EnhancedTaskLogger',
    'FlowAPI',
    'O3ContextBuilder',
    'Plan',
    'Response',
    'ScanOptions',
    'Task',
    'TaskLogger',
    'TaskStatus',
    'UltraSimpleFlowManager',
    'append',
    'ask_o3_practical',
    'classes',
    'create_directory',
    'create_task_logger',
    'display_plan_tasks',
    'exists',
    'file_info',
    'find_class',
    'find_function',
    'find_project_path',
    'flow',
    'flow_project',
    'flow_project_with_workflow',
    'fp',
    'functions',
    'get_current_project',
    'get_flow_api',
    'get_flow_manager',
    'git_add',
    'git_branch',
    'git_branch_d',
    'git_checkout',
    'git_checkout_b',
    'git_commit',
    'git_diff',
    'git_log',
    'git_merge',
    'git_pull',
    'git_push',
    'git_rebase',
    'git_reset_hard',
    'git_stash',
    'git_stash_list',
    'git_stash_pop',
    'git_status',
    'grep',
    'help_flow',
    'info',
    'insert',
    'list_directory',
    'move_file',
    'parse',
    'quick_o3_context',
    'read',
    'read_json',
    'replace',
    'resolve_project_path',
    'safe_replace',
    'scan_directory',
    'search_code',
    'search_files',
    'view',
    'write',
    'write_json',
    'fix_task_numbers',
    'validate_flow_response', 
    'get_task_safe',
    'git_status_normalized'
]


# TaskLogger alias for backward compatibility
TaskLogger = EnhancedTaskLogger

# Web Automation Helpers
try:
    from api.web_automation_helpers import (
        web_start, web_stop, web_status,
        web_goto, web_click, web_type,
        web_extract, web_extract_table, web_wait,
        web_screenshot, web_generate_script, web_get_data,
        web_extract_batch, web_extract_attributes, web_extract_form,
        # 레코딩 함수
        web_record_start, web_record_stop, web_record_status,
        web_demo,
        # 세션 유지 함수 (2025-08-06)
        web_connect, web_disconnect, web_check_session,
        web_list_sessions, web_goto_session,
        # 팝업 처리 함수 (2025-08-06)
        handle_popup, handle_alert, wait_and_click,
        handle_modal_by_class, close_popup, confirm_popup, cancel_popup,
        # 기존 브라우저 연결 함수 (2025-08-06)
        connect_to_existing_browser, launch_browser_with_debugging, get_browser_ws_endpoint
    )
    
    # __all__에 web 함수들 추가
    __all__.extend([
        'web_start', 'web_stop', 'web_status',
        'web_goto', 'web_click', 'web_type',
        'web_extract', 'web_extract_table', 'web_wait',
        'web_screenshot', 'web_generate_script', 'web_get_data',
        'web_extract_batch', 'web_extract_attributes', 'web_extract_form',
        'web_record_start', 'web_record_stop', 'web_record_status',
        'web_demo',
        # 세션 유지 함수
        'web_connect', 'web_disconnect', 'web_check_session',
        'web_list_sessions', 'web_goto_session',
        # 팝업 처리 함수
        'handle_popup', 'handle_alert', 'wait_and_click',
        'handle_modal_by_class', 'close_popup', 'confirm_popup', 'cancel_popup',
        # 기존 브라우저 연결 함수
        'connect_to_existing_browser', 'launch_browser_with_debugging', 'get_browser_ws_endpoint'
    ])
except ImportError as e:
    print(f"Warning: Web automation helpers not available: {e}")

# Flow API 인스턴스 getter
def get_flow_api():
    """Flow API 인스턴스 반환

    Returns:
        FlowAPI: Flow API 인스턴스
    """
    from .flow_api import FlowAPI
    from .ultra_simple_flow_manager import UltraSimpleFlowManager

    manager = UltraSimpleFlowManager()
    return FlowAPI(manager)
# Task Logger Helpers (v76.1)
from .task_logger_helpers import (
    get_task_logger,
    log_test_result,
    log_code_change,
    log_analysis,
    log_progress
)
