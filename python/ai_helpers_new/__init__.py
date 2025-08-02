"""
AI Helpers New - Ultra Simple Flow System
Flow 개념 없이 Plan만으로 작업하는 극단순 시스템
"""

# 도메인 모델 (Flow 제외)
from .domain.models import Plan, Task, TaskStatus

# Ultra Simple Manager
from .ultra_simple_flow_manager import UltraSimpleFlowManager

# Flow 명령어 시스템
from .simple_flow_commands import flow, help_flow
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
    'UltraSimpleFlowManager',
    'Plan',
    'Task', 
    'TaskStatus',
    'get_flow_manager',
    'flow',
    'help_flow',
    "EnhancedTaskLogger",
    "TaskLogger",  # EnhancedTaskLogger의 alias
    "create_task_logger",
    "display_plan_tasks",
    "Response",
    "ScanOptions",
    'ask_o3_practical',
    'O3ContextBuilder',
    'quick_o3_context',
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
        web_demo
    )
    
    # __all__에 web 함수들 추가
    __all__.extend([
        'web_start', 'web_stop', 'web_status',
        'web_goto', 'web_click', 'web_type',
        'web_extract', 'web_extract_table', 'web_wait',
        'web_screenshot', 'web_generate_script', 'web_get_data',
        'web_extract_batch', 'web_extract_attributes', 'web_extract_form',
        'web_record_start', 'web_record_stop', 'web_record_status',
        'web_demo'
    ])
except ImportError as e:
    print(f"Warning: Web automation helpers not available: {e}")
