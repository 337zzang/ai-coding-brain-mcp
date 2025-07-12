"""
WorkflowEventAdapter - 워크플로우와 EventBus를 연결하는 어댑터
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .event_bus import EventBus, Event
from .models import WorkflowEvent, EventType
from .events import EventBuilder
import uuid

logger = logging.getLogger(__name__)


class WorkflowEventAdapter:
    """워크플로우 이벤트를 EventBus로 전달하는 어댑터"""

    def __init__(self, workflow_manager):
        self.workflow_manager = workflow_manager
        self.event_bus = EventBus()
        self.event_bus.start()
        logger.info("WorkflowEventAdapter initialized with EventBus")
        self._register_handlers()


    def add_listener(self, event_type: str, handler):
        """이벤트 리스너 추가"""
        self.event_bus.subscribe(event_type, handler)
        logger.debug(f"Added listener for {event_type}")

    def remove_listener(self, event_type: str, handler):
        """이벤트 리스너 제거"""
        self.event_bus.unsubscribe(event_type, handler)
        logger.debug(f"Removed listener for {event_type}")

    def add_workflow_listener(self, listener):
        """BaseEventListener 인터페이스를 구현한 리스너 추가"""
        if hasattr(listener, 'get_subscribed_events') and hasattr(listener, 'handle_event'):
            # 구독할 이벤트 타입 가져오기
            event_types = listener.get_subscribed_events()

            # 각 이벤트 타입에 대해 핸들러 등록
            for event_type in event_types:
                event_type_str = event_type.value if hasattr(event_type, 'value') else str(event_type)

                # 래퍼 함수 생성 (Event를 WorkflowEvent로 변환)
                def create_handler(listener_ref):
                    def handler(event):
                        # Event를 WorkflowEvent로 변환
                        workflow_event = self._convert_event_to_workflow_event(event)
                        if workflow_event:
                            listener_ref.handle_event(workflow_event)
                    return handler

                self.event_bus.subscribe(event_type_str, create_handler(listener))
                logger.debug(f"Added workflow listener for {event_type_str}")

    def _convert_event_to_workflow_event(self, event) -> Optional[WorkflowEvent]:
        """EventBus의 Event를 WorkflowEvent로 변환"""
        try:
            from .event_types import EventType

            # EventType 찾기
            event_type = None
            for et in EventType:
                if et.value == event.type:
                    event_type = et
                    break

            if not event_type:
                logger.warning(f"Unknown event type: {event.type}")
                return None

            # WorkflowEvent 생성
            data = event.data if hasattr(event, 'data') else {}
            workflow_event = WorkflowEvent(
                id=event.id if hasattr(event, 'id') else str(uuid.uuid4()),
                type=event_type,
                timestamp=event.timestamp if hasattr(event, 'timestamp') else datetime.now(),
                plan_id=data.get('plan_id', ''),
                task_id=data.get('task_id'),
                user=data.get('user', 'system'),
                details=data.get('details', {}),
                metadata=data.get('metadata', {})
            )

            return workflow_event
        except Exception as e:
            logger.error(f"Error converting Event to WorkflowEvent: {e}")
            return None

    def _register_handlers(self):
        """기본 핸들러 등록"""
        # PROJECT_SWITCHED 이벤트 핸들러
        self.event_bus.subscribe("project_switched", self._on_project_switched)

    def _on_project_switched(self, event):
        """프로젝트 전환 이벤트 처리"""
        logger.info(f"Project switched event: {event}")

    def _convert_workflow_event_to_event(self, workflow_event: WorkflowEvent) -> Event:
        """WorkflowEvent를 EventBus의 Event로 변환"""
        from .event_bus import Event

        # 디버깅: WorkflowEvent 타입 확인
        if not hasattr(workflow_event, 'type'):
            logger.error(f"WorkflowEvent has no type attribute: {type(workflow_event)}, {workflow_event}")
            return None

        # Event 객체 생성 - type을 생성자에 전달
        event_type = workflow_event.type.value if hasattr(workflow_event.type, 'value') else str(workflow_event.type)
        
        if not event_type:
            logger.error(f"Event type is empty: workflow_event.type={workflow_event.type}")
            return None
        
        event = Event(
            id=workflow_event.id,
            type=event_type,
            timestamp=workflow_event.timestamp,
            payload={
                'plan_id': workflow_event.plan_id,
                'task_id': workflow_event.task_id,
                'user': workflow_event.user,
                'details': workflow_event.details,
                'metadata': workflow_event.metadata
            }
        )

        return event


    def publish_workflow_event(self, workflow_event: WorkflowEvent):
        """WorkflowEvent를 EventBus로 발행"""
        if not isinstance(workflow_event, WorkflowEvent):
            logger.error(f"Invalid event type: {type(workflow_event)}, expected WorkflowEvent but got {workflow_event}")
            return

        try:
            # EventBus로 발행
            event = self._convert_workflow_event_to_event(workflow_event)
            if event:
                self.event_bus.publish(event)
                logger.debug(f"Published {workflow_event.type} event to EventBus")
            else:
                logger.error(f"Failed to convert WorkflowEvent to Event: {workflow_event}")
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")

    def publish_plan_created(self, plan):
        """플랜 생성 이벤트 발행"""
        event = EventBuilder.plan_created(plan)
        self.publish_workflow_event(event)

    def publish_plan_started(self, plan):
        """플랜 시작 이벤트 발행"""
        event = EventBuilder.plan_started(plan)
        self.publish_workflow_event(event)

    def publish_plan_completed(self, plan):
        """플랜 완료 이벤트 발행"""
        event = EventBuilder.plan_completed(plan)
        self.publish_workflow_event(event)

    def publish_task_added(self, task, plan):
        """태스크 추가 이벤트 발행"""
        event = EventBuilder.task_added(plan.id, task)
        self.publish_workflow_event(event)

    def publish_task_started(self, task, plan):
        """태스크 시작 이벤트 발행"""
        event = EventBuilder.task_started(plan.id, task)
        self.publish_workflow_event(event)

    def publish_task_completed(self, task, plan):
        """태스크 완료 이벤트 발행"""
        event = EventBuilder.task_completed(plan.id, task)
        self.publish_workflow_event(event)

    def publish_task_failed(self, task, plan, error: str):
        """태스크 실패 이벤트 발행"""
        error_details = {
            'error': error,
            'task_title': task.title,
            'error_type': 'TaskExecutionError'
        }
        event = EventBuilder.task_failed(plan.id, task, error_details)
        self.publish_workflow_event(event)

    def cleanup(self):
        """정리 작업"""
        if self.event_bus:
            self.event_bus.stop()
            logger.info("EventBus stopped")
