"""
Event Types Definition
프로젝트에서 사용되는 모든 이벤트 타입 정의
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional
from events.event_bus import Event, EventPriority


# 이벤트 타입 상수
class EventTypes:
    """이벤트 타입 상수 정의"""

    # 워크플로우 이벤트
    WORKFLOW_PLAN_CREATED = "workflow.plan.created"
    WORKFLOW_PLAN_COMPLETED = "workflow.plan.completed"
    WORKFLOW_PLAN_ARCHIVED = "workflow.plan.archived"

    WORKFLOW_TASK_CREATED = "workflow.task.created"
    WORKFLOW_TASK_STARTED = "workflow.task.started"
    WORKFLOW_TASK_COMPLETED = "workflow.task.completed"
    WORKFLOW_TASK_FAILED = "workflow.task.failed"
    WORKFLOW_TASK_BLOCKED = "workflow.task.blocked"

    # 컨텍스트 이벤트
    CONTEXT_PROJECT_SWITCHED = "context.project.switched"
    CONTEXT_UPDATED = "context.updated"
    CONTEXT_SAVED = "context.saved"
    CONTEXT_LOADED = "context.loaded"

    # 파일 시스템 이벤트
    FILE_CREATED = "file.created"
    FILE_MODIFIED = "file.modified"
    FILE_DELETED = "file.deleted"
    FILE_ACCESSED = "file.accessed"

    # Git 이벤트
    GIT_COMMIT_CREATED = "git.commit.created"
    GIT_BRANCH_CHANGED = "git.branch.changed"
    GIT_PUSH_COMPLETED = "git.push.completed"

    # 시스템 이벤트
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"
    SYSTEM_INFO = "system.info"


# 특화된 이벤트 클래스들
@dataclass
class WorkflowEvent(Event):
    """워크플로우 관련 이벤트"""
    def __init__(self, event_type: str, plan_id: Optional[str] = None, 
                 task_id: Optional[str] = None, **kwargs):
        data = {
            'plan_id': plan_id,
            'task_id': task_id,
            **kwargs
        }
        super().__init__(type=event_type, data=data)


@dataclass
class TaskEvent(Event):
    """태스크 관련 이벤트"""
    def __init__(self, event_type: str, task_id: str, task_title: str, 
                 status: Optional[str] = None, **kwargs):
        data = {
            'task_id': task_id,
            'task_title': task_title,
            'status': status,
            **kwargs
        }
        super().__init__(type=event_type, data=data, priority=EventPriority.HIGH)


@dataclass
class FileEvent(Event):
    """파일 시스템 관련 이벤트"""
    def __init__(self, event_type: str, file_path: str, operation: str, 
                 task_id: Optional[str] = None, **kwargs):
        data = {
            'file_path': file_path,
            'operation': operation,
            'task_id': task_id,  # 현재 작업 중인 태스크 ID
            **kwargs
        }
        super().__init__(type=event_type, data=data)


@dataclass
class ContextEvent(Event):
    """컨텍스트 관련 이벤트"""
    def __init__(self, event_type: str, project_name: Optional[str] = None, 
                 update_type: Optional[str] = None, **kwargs):
        data = {
            'project_name': project_name,
            'update_type': update_type,
            **kwargs
        }
        super().__init__(type=event_type, data=data, priority=EventPriority.HIGH)


@dataclass
class GitEvent(Event):
    """Git 관련 이벤트"""
    def __init__(self, event_type: str, branch: Optional[str] = None, 
                 commit_hash: Optional[str] = None, message: Optional[str] = None, **kwargs):
        data = {
            'branch': branch,
            'commit_hash': commit_hash,
            'message': message,
            **kwargs
        }
        super().__init__(type=event_type, data=data)


# 이벤트 생성 헬퍼 함수들
def create_task_started_event(task_id: str, task_title: str) -> TaskEvent:
    """태스크 시작 이벤트 생성"""
    return TaskEvent(
        EventTypes.WORKFLOW_TASK_STARTED,
        task_id=task_id,
        task_title=task_title,
        status="IN_PROGRESS"
    )


def create_task_completed_event(task_id: str, task_title: str, notes: str = "") -> TaskEvent:
    """태스크 완료 이벤트 생성"""
    return TaskEvent(
        EventTypes.WORKFLOW_TASK_COMPLETED,
        task_id=task_id,
        task_title=task_title,
        status="COMPLETED",
        completion_notes=notes
    )


def create_file_access_event(file_path: str, operation: str, task_id: Optional[str] = None) -> FileEvent:
    """파일 접근 이벤트 생성"""
    return FileEvent(
        EventTypes.FILE_ACCESSED,
        file_path=file_path,
        operation=operation,
        task_id=task_id
    )


def create_project_switch_event(old_project: str, new_project: str) -> ContextEvent:
    """프로젝트 전환 이벤트 생성"""
    return ContextEvent(
        EventTypes.CONTEXT_PROJECT_SWITCHED,
        project_name=new_project,
        old_project=old_project
    )
