"""
Event Types for Workflow V3
==========================

기존 통합 이벤트 타입(unified_event_types)을 활용하여
워크플로우 V3 시스템에 특화된 이벤트 클래스들을 정의합니다.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

# 기존 통합 이벤트 타입 import
try:
    from python.events.unified_event_types import EventType
except ImportError:
    # 독립 실행 시 기본 정의
    from enum import Enum
    class EventType(str, Enum):
        PLAN_CREATED = "plan_created"
        PLAN_STARTED = "plan_started"
        PLAN_COMPLETED = "plan_completed"
        PLAN_ARCHIVED = "plan_archived"
        PLAN_UPDATED = "plan_updated"
        TASK_ADDED = "task_added"
        TASK_STARTED = "task_started"
        TASK_COMPLETED = "task_completed"
        TASK_UPDATED = "task_updated"
        CONTEXT_UPDATED = "context_updated"
        CONTEXT_SAVED = "context_saved"
        PROJECT_SWITCHED = "project_switched"
        PROJECT_LOADED = "project_loaded"
        SYSTEM_ERROR = "system_error"
        SYSTEM_WARNING = "system_warning"
        SYSTEM_INFO = "system_info"

# EventBus의 기본 Event 클래스 import
try:
    from .event_bus import Event
except ImportError:
    # 독립 실행 시 기본 Event 클래스 정의
    @dataclass
    class Event:
        """기본 이벤트 클래스"""
        id: str = field(default_factory=lambda: str(uuid.uuid4()))
        type: str = ""
        timestamp: datetime = field(default_factory=datetime.now)
        payload: Dict[str, Any] = field(default_factory=dict)
        metadata: Dict[str, Any] = field(default_factory=dict)

        def __post_init__(self):
            """이벤트 생성 후 처리"""
            if not self.type:
                raise ValueError("Event type is required")

            # 메타데이터에 기본 정보 추가
            self.metadata.update({
                'created_at': self.timestamp.isoformat(),
                'event_id': self.id,
                'event_type': self.type
            })


# === 워크플로우 이벤트 ===

@dataclass
class WorkflowEvent(Event):
    """워크플로우 관련 이벤트 기본 클래스"""
    workflow_id: Optional[str] = None
    project_name: Optional[str] = None

    def __post_init__(self):
        # 메타데이터에 워크플로우 정보 추가
        if self.workflow_id:
            self.metadata['workflow_id'] = self.workflow_id
        if self.project_name:
            self.metadata['project_name'] = self.project_name
        super().__post_init__()


@dataclass
class PlanEvent(WorkflowEvent):
    """플랜 관련 이벤트"""
    plan_id: Optional[str] = None
    plan_name: Optional[str] = None
    plan_status: Optional[str] = None

    def __post_init__(self):
        if self.plan_id:
            self.metadata['plan_id'] = self.plan_id
        super().__post_init__()


@dataclass
class TaskEvent(WorkflowEvent):
    """태스크 관련 이벤트"""
    task_id: Optional[str] = None
    task_title: Optional[str] = None
    task_status: Optional[str] = None
    plan_id: Optional[str] = None

    def __post_init__(self):
        if self.task_id:
            self.metadata['task_id'] = self.task_id
        if self.plan_id:
            self.metadata['plan_id'] = self.plan_id
        super().__post_init__()


# === 컨텍스트 이벤트 ===

@dataclass
class ContextEvent(Event):
    """컨텍스트 관련 이벤트"""
    context_type: str = "workflow"  # workflow, project, task 등
    context_data: Dict[str, Any] = field(default_factory=dict)
    project_name: Optional[str] = None

    def __post_init__(self):
        self.metadata['context_type'] = self.context_type
        if self.project_name:
            self.metadata['project_name'] = self.project_name
        super().__post_init__()


# === 명령어 이벤트 ===

@dataclass
class CommandEvent(Event):
    """명령어 실행 이벤트"""
    command: str = ""
    args: List[str] = field(default_factory=list)
    result: Optional[Any] = None
    success: bool = True
    error: Optional[str] = None

    def __post_init__(self):
        self.metadata['command'] = self.command
        self.metadata['success'] = self.success
        if self.error:
            self.metadata['error'] = self.error
        super().__post_init__()


# === 프로젝트 이벤트 ===

@dataclass
class ProjectEvent(Event):
    """프로젝트 관련 이벤트"""
    project_name: str = ""
    previous_project: Optional[str] = None
    project_path: Optional[str] = None

    def __post_init__(self):
        self.metadata['project_name'] = self.project_name
        if self.previous_project:
            self.metadata['previous_project'] = self.previous_project
        super().__post_init__()


# === 파일 이벤트 ===

@dataclass
class FileEvent(Event):
    """파일 시스템 이벤트"""
    file_path: str = ""
    operation: str = ""  # created, modified, deleted, accessed
    file_type: Optional[str] = None
    size: Optional[int] = None

    def __post_init__(self):
        self.metadata['file_path'] = self.file_path
        self.metadata['operation'] = self.operation
        super().__post_init__()


# === Git 이벤트 ===

@dataclass
class GitEvent(Event):
    """Git 관련 이벤트"""
    repository: Optional[str] = None
    branch: Optional[str] = None
    commit_hash: Optional[str] = None
    operation: str = ""  # commit, push, branch_change 등

    def __post_init__(self):
        self.metadata['operation'] = self.operation
        if self.repository:
            self.metadata['repository'] = self.repository
        if self.branch:
            self.metadata['branch'] = self.branch
        super().__post_init__()


# === 시스템 이벤트 ===

@dataclass
class SystemEvent(Event):
    """시스템 레벨 이벤트"""
    level: str = "info"  # info, warning, error
    message: str = ""
    error_type: Optional[str] = None
    traceback: Optional[str] = None

    def __post_init__(self):
        self.metadata['level'] = self.level
        if self.error_type:
            self.metadata['error_type'] = self.error_type
        super().__post_init__()


# === 이벤트 생성 헬퍼 함수 ===

def create_plan_event(event_type: EventType, **kwargs) -> PlanEvent:
    """플랜 이벤트 생성 헬퍼"""
    return PlanEvent(type=event_type.value, payload=kwargs, **kwargs)


def create_task_event(event_type: EventType, **kwargs) -> TaskEvent:
    """태스크 이벤트 생성 헬퍼"""
    return TaskEvent(type=event_type.value, payload=kwargs, **kwargs)


def create_context_event(event_type: EventType, **kwargs) -> ContextEvent:
    """컨텍스트 이벤트 생성 헬퍼"""
    return ContextEvent(type=event_type.value, payload=kwargs, **kwargs)


def create_command_event(command: str, **kwargs) -> CommandEvent:
    """명령어 이벤트 생성 헬퍼"""
    return CommandEvent(
        type="command_executed",  # 기본 타입
        command=command,
        payload=kwargs,
        **kwargs
    )


def create_project_event(event_type: EventType, **kwargs) -> ProjectEvent:
    """프로젝트 이벤트 생성 헬퍼"""
    return ProjectEvent(type=event_type.value, payload=kwargs, **kwargs)


def create_file_event(event_type: EventType, **kwargs) -> FileEvent:
    """파일 이벤트 생성 헬퍼"""
    return FileEvent(type=event_type.value, payload=kwargs, **kwargs)


def create_git_event(event_type: EventType, **kwargs) -> GitEvent:
    """Git 이벤트 생성 헬퍼"""
    return GitEvent(type=event_type.value, payload=kwargs, **kwargs)


def create_system_event(level: str, message: str, **kwargs) -> SystemEvent:
    """시스템 이벤트 생성 헬퍼"""
    event_type_map = {
        'error': EventType.SYSTEM_ERROR,
        'warning': EventType.SYSTEM_WARNING,
        'info': EventType.SYSTEM_INFO
    }
    event_type = event_type_map.get(level, EventType.SYSTEM_INFO)

    return SystemEvent(
        type=event_type.value,
        level=level,
        message=message,
        payload={'message': message, **kwargs},
        **kwargs
    )


# Export all
__all__ = [
    # 기존 EventType enum
    'EventType',

    # 이벤트 클래스들
    'WorkflowEvent',
    'PlanEvent',
    'TaskEvent',
    'ContextEvent',
    'CommandEvent',
    'ProjectEvent',
    'FileEvent',
    'GitEvent',
    'SystemEvent',

    # 헬퍼 함수들
    'create_plan_event',
    'create_task_event',
    'create_context_event',
    'create_command_event',
    'create_project_event',
    'create_file_event',
    'create_git_event',
    'create_system_event',
]
