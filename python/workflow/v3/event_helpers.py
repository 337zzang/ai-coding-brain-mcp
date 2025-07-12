"""
이벤트 발행 헬퍼 함수들

이벤트 발행을 더 쉽고 일관되게 만들기 위한 헬퍼 함수들입니다.
"""
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime

from python.workflow.v3.models import WorkflowEvent, Task, WorkflowPlan
from python.events.unified_event_types import EventType
from python.workflow.v3.events import EventBuilder

logger = logging.getLogger(__name__)


class EventPublisher:
    """이벤트 발행 헬퍼 클래스

    WorkflowManager에서 사용할 수 있는 간편한 이벤트 발행 메서드들을 제공합니다.
    """

    def __init__(self, event_handler_func):
        """
        Args:
            event_handler_func: 실제 이벤트를 처리하는 함수 (예: manager._add_event)
        """
        self._publish = event_handler_func

    def plan_lifecycle(self, plan: WorkflowPlan, action: str, **details) -> None:
        """플랜 생명주기 이벤트 발행

        Args:
            plan: WorkflowPlan 객체
            action: 'created', 'started', 'completed', 'archived'
            **details: 추가 상세 정보
        """
        event_map = {
            'created': EventBuilder.plan_created,
            'started': EventBuilder.plan_started,
            'completed': EventBuilder.plan_completed,
            'archived': EventBuilder.plan_archived,
        }

        if action not in event_map:
            logger.warning(f"Unknown plan action: {action}")
            return

        event = event_map[action](plan, **details)
        self._publish(event)
        logger.debug(f"Published plan {action} event for {plan.id}")

    def task_lifecycle(self, plan_id: str, task: Task, action: str, **details) -> None:
        """태스크 생명주기 이벤트 발행

        Args:
            plan_id: 플랜 ID
            task: Task 객체
            action: 'added', 'started', 'completed', 'failed', 'blocked', 'unblocked'
            **details: 추가 상세 정보
        """
        event_builders = {
            'added': lambda: EventBuilder.task_added(plan_id, task),
            'started': lambda: EventBuilder.task_started(plan_id, task),
            'completed': lambda: EventBuilder.task_completed(
                plan_id, task, details.get('note', '')
            ),
            'failed': lambda: EventBuilder.task_failed(
                plan_id, task, details.get('error', 'Unknown error')
            ),
            'blocked': lambda: EventBuilder.task_blocked(
                plan_id, task, details.get('blocker', 'Unknown')
            ),
            'unblocked': lambda: EventBuilder.task_unblocked(plan_id, task),
        }

        if action not in event_builders:
            logger.warning(f"Unknown task action: {action}")
            return

        event = event_builders[action]()
        self._publish(event)
        logger.debug(f"Published task {action} event for {task.id}")

    def batch_events(self, events: List[WorkflowEvent]) -> None:
        """여러 이벤트를 한번에 발행

        Args:
            events: WorkflowEvent 리스트
        """
        for event in events:
            self._publish(event)
        logger.debug(f"Published {len(events)} events in batch")

    def custom_event(self, event_type: EventType, plan_id: str = "", 
                    task_id: str = "", **details) -> None:
        """커스텀 이벤트 발행

        Args:
            event_type: EventType
            plan_id: 플랜 ID (선택)
            task_id: 태스크 ID (선택)
            **details: 이벤트 상세 정보
        """
        event = WorkflowEvent(
            type=event_type,
            plan_id=plan_id,
            task_id=task_id,
            timestamp=datetime.now(),
            user=details.pop('user', 'system'),
            details=details
        )
        self._publish(event)
        logger.debug(f"Published custom event: {event_type.value}")


def create_event_publisher(event_handler) -> EventPublisher:
    """EventPublisher 인스턴스 생성

    Args:
        event_handler: 이벤트 핸들러 함수

    Returns:
        EventPublisher 인스턴스
    """
    return EventPublisher(event_handler)


# 표준 이벤트 체인 정의
EVENT_CHAINS = {
    EventType.TASK_COMPLETED: [
        # 태스크 완료 시 자동으로 발생하는 이벤트들
        EventType.CONTEXT_UPDATED,
        # Git 커밋은 GitAutoCommitListener가 처리
    ],
    EventType.PLAN_COMPLETED: [
        EventType.CONTEXT_SAVED,
        # Git 커밋은 GitAutoCommitListener가 처리
    ],
    EventType.TASK_FAILED: [
        EventType.CONTEXT_UPDATED,
        # ErrorHandlerListener가 재시도 또는 플랜 일시정지 처리
    ],
}


def get_chained_events(trigger_event: EventType) -> List[EventType]:
    """트리거 이벤트에 연결된 이벤트 목록 반환

    Args:
        trigger_event: 트리거 이벤트 타입

    Returns:
        연결된 이벤트 타입 리스트
    """
    return EVENT_CHAINS.get(trigger_event, [])
