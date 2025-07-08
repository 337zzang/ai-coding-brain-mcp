"""
Workflow v2 시스템
"""

# Models
from workflow.v2.models import WorkflowPlan, Task, TaskStatus, PlanStatus

# Manager
from workflow.v2.manager import WorkflowV2Manager

# Handlers - 실제 함수명 사용
from workflow.v2.handlers import (
    workflow_start, workflow_focus, workflow_plan, workflow_task,
    workflow_status, workflow_current, workflow_next, workflow_done,
    workflow_history, workflow_build, workflow_review
)

# Dispatcher
from workflow.v2.dispatcher import execute_workflow_command

# Aliases for compatibility
get_status = workflow_status
create_plan = workflow_plan
add_task = workflow_task
complete_current_task = workflow_done

__all__ = [
    # Models
    'WorkflowPlan', 'Task', 'TaskStatus', 'PlanStatus',

    # Manager
    'WorkflowV2Manager',

    # Handlers
    'workflow_start', 'workflow_focus', 'workflow_plan', 'workflow_task',
    'workflow_status', 'workflow_current', 'workflow_next', 'workflow_done',
    'workflow_history', 'workflow_build', 'workflow_review',

    # Aliases
    'get_status', 'create_plan', 'add_task', 'complete_current_task',

    # Dispatcher
    'execute_workflow_command',
]

__version__ = "2.0.0"
