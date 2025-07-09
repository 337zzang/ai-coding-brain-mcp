"""
Unified Event Types for the entire project
통합 이벤트 타입 정의 - 전체 프로젝트에서 사용

이 모듈은 기존의 분산된 이벤트 타입 정의를 통합합니다:
- python/events/event_types.py의 EventTypes 클래스
- python/workflow/v3/models.py의 EventType enum
"""

from enum import Enum
from typing import Dict, Any

__all__ = ['EventType', 'EVENT_TYPE_MAPPING', 'get_event_type']


class EventType(str, Enum):
    """통합 이벤트 타입 정의
    
    워크플로우 V3와 이벤트 시스템에서 공통으로 사용하는 이벤트 타입입니다.
    """
    
    # === 플랜 관련 이벤트 ===
    PLAN_CREATED = "plan_created"       # 새 플랜 생성
    PLAN_STARTED = "plan_started"       # 플랜 시작 (active 상태 전환)
    PLAN_COMPLETED = "plan_completed"   # 플랜 완료
    PLAN_ARCHIVED = "plan_archived"     # 플랜 보관
    PLAN_UPDATED = "plan_updated"       # 플랜 정보 수정
    PLAN_CANCELLED = "plan_cancelled"   # 플랜 취소
    
    # === 태스크 관련 이벤트 ===
    TASK_ADDED = "task_added"           # 태스크 추가
    TASK_STARTED = "task_started"       # 태스크 시작
    TASK_COMPLETED = "task_completed"   # 태스크 완료
    TASK_CANCELLED = "task_cancelled"   # 태스크 취소
    TASK_UPDATED = "task_updated"       # 태스크 정보 수정
    TASK_FAILED = "task_failed"         # 태스크 실패
    TASK_BLOCKED = "task_blocked"       # 태스크 차단됨
    TASK_UNBLOCKED = "task_unblocked"   # 태스크 차단 해제
    
    # === 노트/메모 관련 이벤트 ===
    NOTE_ADDED = "note_added"           # 노트 추가
    NOTE_UPDATED = "note_updated"       # 노트 수정
    NOTE_DELETED = "note_deleted"       # 노트 삭제
    
    # === 컨텍스트 관련 이벤트 ===
    CONTEXT_UPDATED = "context_updated" # 컨텍스트 업데이트
    CONTEXT_SAVED = "context_saved"     # 컨텍스트 저장
    CONTEXT_LOADED = "context_loaded"   # 컨텍스트 로드
    
    # === 프로젝트 관련 이벤트 ===
    PROJECT_SWITCHED = "project_switched"  # 프로젝트 전환
    PROJECT_LOADED = "project_loaded"      # 프로젝트 로드
    
    # === 세션 관련 이벤트 ===
    SESSION_STARTED = "session_started"    # 세션 시작
    SESSION_RESUMED = "session_resumed"    # 세션 재개
    SESSION_ENDED = "session_ended"        # 세션 종료
    
    # === 파일 시스템 이벤트 ===
    FILE_CREATED = "file_created"          # 파일 생성
    FILE_MODIFIED = "file_modified"        # 파일 수정
    FILE_DELETED = "file_deleted"          # 파일 삭제
    FILE_ACCESSED = "file_accessed"        # 파일 접근
    
    # === Git 이벤트 ===
    GIT_COMMIT_CREATED = "git_commit_created"      # 커밋 생성
    GIT_BRANCH_CHANGED = "git_branch_changed"      # 브랜치 변경
    GIT_PUSH_COMPLETED = "git_push_completed"      # 푸시 완료
    
    # === 시스템 이벤트 ===
    SYSTEM_ERROR = "system_error"          # 시스템 오류
    SYSTEM_WARNING = "system_warning"      # 시스템 경고
    SYSTEM_INFO = "system_info"            # 시스템 정보


# 이전 EventTypes 클래스와의 호환성을 위한 매핑
EVENT_TYPE_MAPPING: Dict[str, EventType] = {
    # 워크플로우 이벤트 매핑
    "workflow.plan.created": EventType.PLAN_CREATED,
    "workflow.plan.completed": EventType.PLAN_COMPLETED,
    "workflow.plan.archived": EventType.PLAN_ARCHIVED,
    "workflow.task.created": EventType.TASK_ADDED,
    "workflow.task.started": EventType.TASK_STARTED,
    "workflow.task.completed": EventType.TASK_COMPLETED,
    "workflow.task.failed": EventType.TASK_FAILED,
    "workflow.task.blocked": EventType.TASK_BLOCKED,
    
    # 컨텍스트 이벤트 매핑
    "context.project.switched": EventType.PROJECT_SWITCHED,
    "context.updated": EventType.CONTEXT_UPDATED,
    "context.saved": EventType.CONTEXT_SAVED,
    "context.loaded": EventType.CONTEXT_LOADED,
    
    # 파일 시스템 이벤트 매핑
    "file.created": EventType.FILE_CREATED,
    "file.modified": EventType.FILE_MODIFIED,
    "file.deleted": EventType.FILE_DELETED,
    "file.accessed": EventType.FILE_ACCESSED,
    
    # Git 이벤트 매핑
    "git.commit.created": EventType.GIT_COMMIT_CREATED,
    "git.branch.changed": EventType.GIT_BRANCH_CHANGED,
    "git.push.completed": EventType.GIT_PUSH_COMPLETED,
    
    # 시스템 이벤트 매핑
    "system.error": EventType.SYSTEM_ERROR,
    "system.warning": EventType.SYSTEM_WARNING,
    "system.info": EventType.SYSTEM_INFO,
}


def get_event_type(old_style_event: str) -> EventType:
    """구 스타일 이벤트 문자열을 EventType enum으로 변환
    
    Args:
        old_style_event: 이전 스타일의 이벤트 문자열 (예: "workflow.task.created")
        
    Returns:
        대응하는 EventType enum 값
        
    Raises:
        ValueError: 매핑되지 않은 이벤트 타입인 경우
    """
    if old_style_event in EVENT_TYPE_MAPPING:
        return EVENT_TYPE_MAPPING[old_style_event]
    
    # 이미 새 스타일인 경우 그대로 반환 시도
    try:
        return EventType(old_style_event)
    except ValueError:
        raise ValueError(f"Unknown event type: {old_style_event}")


# 하위 호환성을 위한 별칭
# 이전 코드에서 EventTypes.WORKFLOW_TASK_CREATED 같은 형태로 사용한 경우를 위해
class EventTypes:
    """Deprecated: Use EventType enum instead
    
    이 클래스는 하위 호환성을 위해 유지됩니다.
    새 코드에서는 EventType enum을 직접 사용하세요.
    """
    # 워크플로우 이벤트
    WORKFLOW_PLAN_CREATED = EventType.PLAN_CREATED.value
    WORKFLOW_PLAN_COMPLETED = EventType.PLAN_COMPLETED.value
    WORKFLOW_PLAN_ARCHIVED = EventType.PLAN_ARCHIVED.value
    
    WORKFLOW_TASK_CREATED = EventType.TASK_ADDED.value
    WORKFLOW_TASK_STARTED = EventType.TASK_STARTED.value
    WORKFLOW_TASK_COMPLETED = EventType.TASK_COMPLETED.value
    WORKFLOW_TASK_FAILED = EventType.TASK_FAILED.value
    WORKFLOW_TASK_BLOCKED = EventType.TASK_BLOCKED.value
    
    # 컨텍스트 이벤트
    CONTEXT_PROJECT_SWITCHED = EventType.PROJECT_SWITCHED.value
    CONTEXT_UPDATED = EventType.CONTEXT_UPDATED.value
    CONTEXT_SAVED = EventType.CONTEXT_SAVED.value
    CONTEXT_LOADED = EventType.CONTEXT_LOADED.value
    
    # 파일 시스템 이벤트
    FILE_CREATED = EventType.FILE_CREATED.value
    FILE_MODIFIED = EventType.FILE_MODIFIED.value
    FILE_DELETED = EventType.FILE_DELETED.value
    FILE_ACCESSED = EventType.FILE_ACCESSED.value
    
    # Git 이벤트
    GIT_COMMIT_CREATED = EventType.GIT_COMMIT_CREATED.value
    GIT_BRANCH_CHANGED = EventType.GIT_BRANCH_CHANGED.value
    GIT_PUSH_COMPLETED = EventType.GIT_PUSH_COMPLETED.value
    
    # 시스템 이벤트
    SYSTEM_ERROR = EventType.SYSTEM_ERROR.value
    SYSTEM_WARNING = EventType.SYSTEM_WARNING.value
    SYSTEM_INFO = EventType.SYSTEM_INFO.value
