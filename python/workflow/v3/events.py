"""
Workflow v3 이벤트 시스템
모든 워크플로우 변경사항을 이벤트로 기록하고 처리
"""
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone
from .models import WorkflowEvent, EventType, WorkflowPlan, Task, TaskStatus
from python.ai_helpers.helper_result import HelperResult
import logging

logger = logging.getLogger(__name__)


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
                'archived_at': plan.archived_at.isoformat() if plan.archived_at else datetime.now(timezone.utc).isoformat()
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
