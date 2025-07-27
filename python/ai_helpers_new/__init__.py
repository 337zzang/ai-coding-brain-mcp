"""
AI Helpers New - Ultra Simple Flow System
Flow 개념 없이 Plan만으로 작업하는 극단순 시스템
"""

# 도메인 모델 (Flow 제외)
from .domain.models import Plan, Task, TaskStatus

# Ultra Simple Manager
from .ultra_simple_flow_manager import UltraSimpleFlowManager

# Flow 명령어 시스템
from .simple_flow_commands import flow, wf, help_flow
from .task_logger import EnhancedTaskLogger, create_task_logger, display_plan_tasks

# AI Helpers 핵심 함수들
from .file import *
from .code import *
from .search import *
from .git import *
from .llm import *
from .util import *
from .project import *
from .wrappers import *
from .helpers_integration import *
from .context_integration import *
from .context_reporter import *
from .doc_context_helper import *
from .backup_utils import *

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
    'wf',
    'help_flow',
    "EnhancedTaskLogger",
    "TaskLogger",  # EnhancedTaskLogger의 alias
    "create_task_logger",
    "display_plan_tasks",
]


# TaskLogger alias for backward compatibility
TaskLogger = EnhancedTaskLogger