"""
Workflow System
===============
효율적인 상태 기반 워크플로우 시스템
"""

# 기존 API 호환성을 위한 import
from .manager import WorkflowManager

# 새로운 컴포넌트들
from .core import WorkflowEngine, StateManager, WorkflowState, TaskState
from .messaging import MessageController

__all__ = [
    # 기존 API (호환성)
    'WorkflowManager',

    # 새로운 API
    'WorkflowEngine',
    'StateManager', 
    'WorkflowState',
    'TaskState',
    'MessageController'
]
