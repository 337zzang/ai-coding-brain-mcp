"""
워크플로우 시스템 v2 - 함수형 API와 중앙 디스패처 기반
"""

from python.workflow.v2.dispatcher import execute_workflow_command, WorkflowDispatcher
from python.workflow.v2.handlers import (
    workflow_start,
    workflow_focus,
    workflow_plan,
    workflow_list_plans,
    workflow_task,
    workflow_tasks,
    workflow_current,
    workflow_next,
    workflow_done,
    workflow_status,
    workflow_history,
    workflow_build,
    workflow_review,
    with_context_save
)

# Version info
__version__ = "2.0.0"
__author__ = "AI Coding Brain MCP"

# Export all
__all__ = [
    # Dispatcher
    'execute_workflow_command',
    'WorkflowDispatcher',

    # Project management
    'workflow_start',
    'workflow_focus',

    # Plan management
    'workflow_plan',
    'workflow_list_plans',

    # Task management
    'workflow_task',
    'workflow_tasks',
    'workflow_current',
    'workflow_next',
    'workflow_done',

    # Status and history
    'workflow_status',
    'workflow_history',

    # Extended features
    'workflow_build',
    'workflow_review',

    # Decorator
    'with_context_save'
]
