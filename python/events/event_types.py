"""
Event Types - 통합 이벤트 타입 Re-export 모듈

이 모듈은 통합 이벤트 타입 시스템의 진입점입니다.
모든 이벤트 타입 정의는 unified_event_types.py에서 관리됩니다.

특화된 이벤트 클래스들은 event_bus_events.py로 이동되었습니다.
"""

from typing import Optional

# 통합 이벤트 타입 전체 re-export
from events.unified_event_types import (
    EventType,
    EventTypes,
    EVENT_TYPE_MAPPING,
    get_event_type
)

# 특화된 이벤트 클래스들 (하위 호환성)
from events.event_bus_events import (
    WorkflowEvent,  # BusWorkflowEvent의 별칭
    TaskEvent,
    FileEvent,
    ContextEvent,
    GitEvent
)

# Export 리스트
__all__ = [
    # 이벤트 타입
    'EventType',
    'EventTypes',
    'EVENT_TYPE_MAPPING',
    'get_event_type',
    # 특화된 이벤트 클래스
    'WorkflowEvent',
    'TaskEvent',
    'FileEvent',
    'ContextEvent',
    'GitEvent',
    # 헬퍼 함수
    'create_task_started_event',
    'create_task_completed_event',
    'create_file_access_event',
    'create_project_switch_event'
]


# 이벤트 생성 헬퍼 함수들 (EventType enum 사용으로 개선)
def create_task_started_event(task_id: str, task_title: str) -> TaskEvent:
    """태스크 시작 이벤트 생성"""
    return TaskEvent(
        EventType.TASK_STARTED.value,  # enum 값 사용
        task_id=task_id,
        task_title=task_title,
        status="IN_PROGRESS"
    )


def create_task_completed_event(task_id: str, task_title: str, notes: str = "") -> TaskEvent:
    """태스크 완료 이벤트 생성"""
    return TaskEvent(
        EventType.TASK_COMPLETED.value,  # enum 값 사용
        task_id=task_id,
        task_title=task_title,
        status="COMPLETED",
        completion_notes=notes
    )


def create_file_access_event(file_path: str, operation: str, task_id: Optional[str] = None) -> FileEvent:
    """파일 접근 이벤트 생성"""
    return FileEvent(
        EventType.FILE_ACCESSED.value,  # enum 값 사용
        file_path=file_path,
        operation=operation,
        task_id=task_id
    )


def create_project_switch_event(old_project: str, new_project: str) -> ContextEvent:
    """프로젝트 전환 이벤트 생성"""
    return ContextEvent(
        EventType.PROJECT_SWITCHED.value,  # enum 값 사용
        project_name=new_project,
        old_project=old_project
    )
