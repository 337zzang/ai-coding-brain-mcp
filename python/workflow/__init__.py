"""
Improved Workflow System
=======================
단순화된 워크플로우 시스템 - 단일 파일 기반
"""

from .improved_manager import ImprovedWorkflowManager
from .models import (
    Task, WorkflowPlan, WorkflowEvent,
    TaskStatus, PlanStatus, EventType
)

# 기본 export
WorkflowManager = ImprovedWorkflowManager  # 하위 호환성

__all__ = [
    # Manager
    'ImprovedWorkflowManager',
    'WorkflowManager',  # 별칭

    # Models
    'Task',
    'WorkflowPlan', 
    'WorkflowEvent',

    # Enums
    'TaskStatus',
    'PlanStatus',
    'EventType',
]

__version__ = "3.1.0"
