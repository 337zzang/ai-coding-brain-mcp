"""
Workflow v3 이벤트 시스템
모든 워크플로우 변경사항을 이벤트로 기록하고 처리
"""
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone, timedelta

# 한국 표준시(KST) 정의
KST = timezone(timedelta(hours=9))
from .models import WorkflowEvent, EventType, WorkflowPlan, Task, TaskStatus
from python.ai_helpers.helper_result import HelperResult
import logging

logger = logging.getLogger(__name__)

__all__ = ['EventProcessor', 'EventBuilder', 'EventStore', 'GitAutoCommitListener', 'EventBus']


class EventProcessor:
    """이벤트 처리기"""
    
    def __init__(self):
        self.handlers: Dict[EventType, Callable] = {}
        self._register_default_handlers()
        
    def _register_default_handlers(self):
        """기본 이벤트 핸들러 등록"""
        # 현재는 로깅만 수행, 추후 확장 가능
        for event_type in EventType:
            self.handlers[event_type] = self._default_handler
            
    def _default_handler(self, event: WorkflowEvent) -> None:
        """기본 이벤트 핸들러 - 로깅"""
        logger.info(f"Event: {event.type.value} - Plan: {event.plan_id[:8]}... Task: {event.task_id[:8] if event.task_id else 'N/A'}")
        
    def process(self, event: WorkflowEvent) -> None:
        """이벤트 처리"""
        handler = self.handlers.get(event.type, self._default_handler)
        try:
            handler(event)
        except Exception as e:
            logger.error(f"Error processing event {event.id}: {str(e)}")
            

class EventBuilder:
    """이벤트 생성 헬퍼"""
    
    @staticmethod
    def plan_created(plan: WorkflowPlan, user: str = "system") -> WorkflowEvent:
        """플랜 생성 이벤트"""
        return WorkflowEvent(
            type=EventType.PLAN_CREATED,
            plan_id=plan.id,
            user=user,
            details={
                'name': plan.name,
                'description': plan.description
            }
        )

        
    @staticmethod
    def plan_started(plan: WorkflowPlan, user: str = "system") -> WorkflowEvent:
        """플랜 시작 이벤트"""
        return WorkflowEvent(
            type=EventType.PLAN_STARTED,
            plan_id=plan.id,
            user=user,
            details={
                'name': plan.name,
                'task_count': len(plan.tasks)
            }
        )
        
    @staticmethod
    def plan_completed(plan: WorkflowPlan, user: str = "system") -> WorkflowEvent:
        """플랜 완료 이벤트"""
        return WorkflowEvent(
            type=EventType.PLAN_COMPLETED,
            plan_id=plan.id,
            user=user,
            details={
                'name': plan.name,
                'total_tasks': len(plan.tasks),
                'completed_tasks': len([t for t in plan.tasks if t.status == TaskStatus.COMPLETED]),
                'stats': plan.stats
            }
        )
        
    @staticmethod
    def plan_archived(plan: WorkflowPlan, user: str = "system") -> WorkflowEvent:
        """플랜 아카이브 이벤트"""
        return WorkflowEvent(
            type=EventType.PLAN_ARCHIVED,
            plan_id=plan.id,
            user=user,
            details={
                'name': plan.name,
                'archived_at': plan.archived_at.isoformat() if plan.archived_at else datetime.now(KST).isoformat()
            }
        )
        
    @staticmethod
    def task_added(plan_id: str, task: Task, user: str = "system") -> WorkflowEvent:
        """태스크 추가 이벤트"""
        return WorkflowEvent(
            type=EventType.TASK_ADDED,
            plan_id=plan_id,
            task_id=task.id,
            user=user,
            details={
                'title': task.title,
                'description': task.description
            }
        )

        
    @staticmethod
    def task_started(plan_id: str, task: Task, user: str = "system") -> WorkflowEvent:
        """태스크 시작 이벤트"""
        return WorkflowEvent(
            type=EventType.TASK_STARTED,
            plan_id=plan_id,
            task_id=task.id,
            user=user,
            details={
                'title': task.title
            }
        )
        
    @staticmethod
    def task_completed(plan_id: str, task: Task, note: str = "", user: str = "system") -> WorkflowEvent:
        """태스크 완료 이벤트"""
        return WorkflowEvent(
            type=EventType.TASK_COMPLETED,
            plan_id=plan_id,
            task_id=task.id,
            user=user,
            details={
                'title': task.title,
                'duration': task.duration,
                'note': note
            }
        )
        
    @staticmethod
    def task_cancelled(plan_id: str, task: Task, reason: str = "", user: str = "system") -> WorkflowEvent:
        """태스크 취소 이벤트"""
        return WorkflowEvent(
            type=EventType.TASK_CANCELLED,
            plan_id=plan_id,
            task_id=task.id,
            user=user,
            details={
                'title': task.title,
                'reason': reason
            }
        )
        
    @staticmethod
    def task_failed(plan_id: str, task: Task, error: str, user: str = "system") -> WorkflowEvent:
        """태스크 실패 이벤트"""
        return WorkflowEvent(
            type=EventType.TASK_FAILED,
            plan_id=plan_id,
            task_id=task.id,
            user=user,
            details={
                'title': task.title,
                'error': error,
                'status': 'failed'
            }
        )
        
    @staticmethod
    def task_blocked(plan_id: str, task: Task, blocker: str, user: str = "system") -> WorkflowEvent:
        """태스크 차단 이벤트"""
        return WorkflowEvent(
            type=EventType.TASK_BLOCKED,
            plan_id=plan_id,
            task_id=task.id,
            user=user,
            details={
                'title': task.title,
                'blocker': blocker,
                'status': 'blocked'
            }
        )
        
    @staticmethod
    def task_unblocked(plan_id: str, task: Task, user: str = "system") -> WorkflowEvent:
        """태스크 차단 해제 이벤트"""
        return WorkflowEvent(
            type=EventType.TASK_UNBLOCKED,
            plan_id=plan_id,
            task_id=task.id,
            user=user,
            details={
                'title': task.title,
                'status': task.status.value
            }
        )
        
    @staticmethod
    def task_updated(plan_id: str, task: Task, changes: Dict[str, Any], user: str = "system") -> WorkflowEvent:
        """태스크 업데이트 이벤트"""
        return WorkflowEvent(
            type=EventType.TASK_UPDATED,
            plan_id=plan_id,
            task_id=task.id,
            user=user,
            details={
                'title': task.title,
                'changes': changes
            }
        )



class EventStore:
    """이벤트 저장소 - 메모리 기반"""
    
    def __init__(self):
        self.events: List[WorkflowEvent] = []
        self.processor = EventProcessor()
        
    def add(self, event: WorkflowEvent) -> None:
        """이벤트 추가"""
        self.events.append(event)
        self.processor.process(event)
        
    def get_events_for_plan(self, plan_id: str) -> List[WorkflowEvent]:
        """특정 플랜의 이벤트 조회"""
        return [e for e in self.events if e.plan_id == plan_id]
        
    def get_events_for_task(self, task_id: str) -> List[WorkflowEvent]:
        """특정 태스크의 이벤트 조회"""
        return [e for e in self.events if e.task_id == task_id]
        
    def get_events_by_type(self, event_type: EventType) -> List[WorkflowEvent]:
        """특정 타입의 이벤트 조회"""
        return [e for e in self.events if e.type == event_type]
        
    def get_recent_events(self, limit: int = 10) -> List[WorkflowEvent]:
        """최근 이벤트 조회"""
        return sorted(self.events, key=lambda e: e.timestamp, reverse=True)[:limit]
        
    def clear(self) -> None:
        """모든 이벤트 삭제"""
        self.events.clear()
        
    def to_list(self) -> List[Dict[str, Any]]:
        """이벤트 목록을 딕셔너리 리스트로 변환"""
        return [e.to_dict() for e in self.events]
        
    def from_list(self, events_data: List[Dict[str, Any]]) -> None:
        """딕셔너리 리스트에서 이벤트 복원"""
        self.events = [WorkflowEvent.from_dict(e) for e in events_data]
        
    def get_plan_summary(self, plan_id: str) -> Dict[str, Any]:
        """플랜의 이벤트 요약"""
        plan_events = self.get_events_for_plan(plan_id)
        
        summary = {
            'total_events': len(plan_events),
            'created_at': None,
            'started_at': None,
            'completed_at': None,
            'archived_at': None,
            'tasks_added': 0,
            'tasks_completed': 0
        }
        
        for event in plan_events:
            if event.type == EventType.PLAN_CREATED:
                summary['created_at'] = event.timestamp
            elif event.type == EventType.PLAN_STARTED:
                summary['started_at'] = event.timestamp
            elif event.type == EventType.PLAN_COMPLETED:
                summary['completed_at'] = event.timestamp
            elif event.type == EventType.PLAN_ARCHIVED:
                summary['archived_at'] = event.timestamp
            elif event.type == EventType.TASK_ADDED:
                summary['tasks_added'] += 1
            elif event.type == EventType.TASK_COMPLETED:
                summary['tasks_completed'] += 1
                
        return summary


class GitAutoCommitListener:
    """Git 자동 커밋 이벤트 리스너"""
    
    def __init__(self, helpers=None):
        """
        Args:
            helpers: helpers 객체 (Git 명령 실행용)
        """
        self.helpers = helpers
        self.enabled = True
        self.auto_commit_events = {
            EventType.TASK_COMPLETED,
            EventType.PLAN_COMPLETED,
            EventType.PLAN_ARCHIVED
        }
        
    def handle_event(self, event: WorkflowEvent) -> None:
        """이벤트 처리 - Git 자동 커밋"""
        if not self.enabled or not self.helpers:
            return
            
        if event.type not in self.auto_commit_events:
            return
            
        try:
            # Git 상태 확인
            status = self.helpers.git_status()
            if not status.ok or not status.data.get('modified'):
                return
                
            # 자동 커밋 메시지 생성
            commit_message = self._generate_commit_message(event)
            
            # Git add 및 commit
            add_result = self.helpers.git_add(".")
            if add_result.ok:
                commit_result = self.helpers.git_commit(commit_message)
                if commit_result.ok:
                    logger.info(f"[GIT] 자동 커밋 성공: {commit_message}")
                else:
                    logger.warning(f"[GIT] 커밋 실패: {commit_result.error}")
            else:
                logger.warning(f"[GIT] add 실패: {add_result.error}")
                
        except Exception as e:
            logger.error(f"[GIT] 자동 커밋 중 오류: {e}")
            
    def _generate_commit_message(self, event: WorkflowEvent) -> str:
        """이벤트에 따른 커밋 메시지 생성"""
        messages = {
            EventType.TASK_COMPLETED: f"workflow: 태스크 완료 - {event.details.get('title', 'Unknown')}",
            EventType.PLAN_COMPLETED: f"workflow: 플랜 완료 - {event.details.get('name', 'Unknown')}",
            EventType.PLAN_ARCHIVED: f"workflow: 플랜 보관 - {event.details.get('name', 'Unknown')}"
        }
        
        base_message = messages.get(event.type, "workflow: 자동 저장")
        
        # 노트가 있으면 추가
        if event.details.get('note'):
            base_message += f"\n\n{event.details['note']}"
            
        return base_message
        
    def set_enabled(self, enabled: bool) -> None:
        """자동 커밋 활성화/비활성화"""
        self.enabled = enabled
        logger.info(f"[GIT] 자동 커밋 {'활성화' if enabled else '비활성화'}")


class EventBus:
    """이벤트 버스 - 이벤트 리스너 관리"""
    
    def __init__(self):
        self.listeners: List[Any] = []
        
    def register(self, listener: Any) -> None:
        """리스너 등록"""
        if hasattr(listener, 'handle_event'):
            self.listeners.append(listener)
            logger.info(f"[EventBus] 리스너 등록: {listener.__class__.__name__}")
        else:
            logger.warning(f"[EventBus] 리스너에 handle_event 메서드가 없음: {listener}")
            
    def unregister(self, listener: Any) -> None:
        """리스너 제거"""
        if listener in self.listeners:
            self.listeners.remove(listener)
            logger.info(f"[EventBus] 리스너 제거: {listener.__class__.__name__}")
            
    def emit(self, event: WorkflowEvent) -> None:
        """모든 리스너에 이벤트 전달"""
        for listener in self.listeners:
            try:
                listener.handle_event(event)
            except Exception as e:
                logger.error(f"[EventBus] 리스너 오류 ({listener.__class__.__name__}): {e}")
