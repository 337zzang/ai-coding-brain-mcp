"""
Workflow v3 - 이벤트 기반 워크플로우 시스템
"""

from .manager import WorkflowManager
from .dispatcher import WorkflowDispatcher
from .storage import WorkflowStorage
from .models import (
    WorkflowState,
    WorkflowPlan,
    Task,  # WorkflowTask 대신 Task 사용
    WorkflowEvent,
    TaskStatus,
    WorkflowError
)
from .event_types import EventType
from .events import EventProcessor, EventBuilder, EventStore
from .workflow_event_adapter import WorkflowEventAdapter

__all__ = [
    # Core
    "WorkflowManager",
    "WorkflowDispatcher", 
    "WorkflowStorage",

    # Models
    "WorkflowState",
    "WorkflowPlan",
    "Task",
    "WorkflowEvent",
    "TaskStatus",
    "WorkflowError",

    # Events
    "EventType",
    "EventProcessor",
    "EventBuilder",
    "EventStore",
    "WorkflowEventAdapter",
]

# 버전 정보
__version__ = "3.0.0"
