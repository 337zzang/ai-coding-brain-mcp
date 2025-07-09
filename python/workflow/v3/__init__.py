"""
Workflow v3 - 이벤트 기반 워크플로우 시스템
"""

# 버전 정보
__version__ = "3.0.0"

# models.py exports
from .models import (
    TaskStatus,
    PlanStatus,
    EventType,
    WorkflowEvent,
    Task,
    WorkflowPlan,
    WorkflowState
)

# events.py exports
from .events import (
    EventProcessor,
    EventBuilder,
    EventStore
)

# parser.py exports
from .parser import (
    CommandParser,
    ParsedCommand
)

# manager.py exports
from .manager import WorkflowManager

# dispatcher.py exports
from .dispatcher import WorkflowDispatcher, execute_workflow_command

# storage.py exports  
from .storage import WorkflowStorage

# context_integration.py exports
from .context_integration import ContextIntegration

# errors.py exports
from .errors import (
    ErrorCode,
    WorkflowError,
    ErrorMessages,
    InputValidator,
    ErrorHandler,
    SuccessMessages
)

# migration.py exports
from .migration import (
    WorkflowMigrator,
    BatchMigrator
)

# 편의를 위한 전체 export
__all__ = [
    # Enums
    'TaskStatus',
    'PlanStatus', 
    'EventType',
    
    # Models
    'WorkflowEvent',
    'Task',
    'WorkflowPlan',
    'WorkflowState',
    
    # Event System
    'EventProcessor',
    'EventBuilder',
    'EventStore',
    
    # Parser
    'CommandParser',
    'ParsedCommand',
    
    # Manager
    'WorkflowManager',
    
    # Storage
    'WorkflowStorage',
    
    # Context Integration
    'ContextIntegration',
    
    # Error Handling
    'ErrorCode',
    'WorkflowError',
    'ErrorMessages',
    'InputValidator',
    'ErrorHandler',
    'SuccessMessages',
    
    # Migration
    'WorkflowMigrator',
    'BatchMigrator',
]
