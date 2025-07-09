"""
Event Bus Event Classes
이벤트 버스 시스템과 통합되는 특화된 이벤트 클래스들

이 모듈은 event_bus.Event를 상속받는 특화된 이벤트 클래스들을 정의합니다.
워크플로우 V3의 WorkflowEvent와는 별개의 클래스들입니다.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional
from events.event_bus import Event, EventPriority


@dataclass
class BusWorkflowEvent(Event):
    """이벤트 버스용 워크플로우 관련 이벤트
    
    Note: workflow.v3.models.WorkflowEvent와는 다른 클래스입니다.
    이벤트 버스 시스템과의 통합을 위한 클래스입니다.
    """
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


# 하위 호환성을 위한 별칭
WorkflowEvent = BusWorkflowEvent
