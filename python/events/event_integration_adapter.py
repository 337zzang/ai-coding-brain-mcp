"""
Event Integration Adapter
기존 시스템에 이벤트를 통합하기 위한 어댑터
"""

from typing import Optional
from workflow.workflow_manager import WorkflowManager
from core.context_manager import ContextManager
from events.event_bus import get_event_bus
from events.event_types import (
    EventTypes, WorkflowEvent, TaskEvent, FileEvent,
    create_task_started_event, create_task_completed_event,
    create_file_access_event
)
from events.workflow_context_bridge import get_workflow_context_bridge
import logging

logger = logging.getLogger(__name__)


class EventIntegrationAdapter:
    """기존 시스템에 이벤트를 통합하는 어댑터"""

    def __init__(self):
        self.event_bus = get_event_bus()
        self.bridge = get_workflow_context_bridge()
        self._original_methods = {}

    def integrate_workflow_manager(self, workflow_manager: WorkflowManager):
        """WorkflowManager에 이벤트 발행 통합"""
        logger.info("Integrating events into WorkflowManager")

        # 원본 메서드 저장
        self._original_methods['wf_create_plan'] = workflow_manager.create_plan
        self._original_methods['wf_start_task'] = workflow_manager.start_task
        self._original_methods['wf_complete_task'] = workflow_manager.complete_task

        # 메서드 래핑
        def create_plan_with_event(name: str, description: str = ""):
            # 원본 메서드 호출
            plan = self._original_methods['wf_create_plan'](name, description)

            # 이벤트 발행
            if plan:
                event = WorkflowEvent(
                    EventTypes.WORKFLOW_PLAN_CREATED,
                    plan_id=plan.id,
                    plan_name=plan.name,
                    description=description
                )
                self.event_bus.publish(event)
                logger.debug(f"Published PLAN_CREATED event for {plan.name}")

            return plan

        def start_task_with_event(task_id: str):
            # 원본 메서드 호출
            result = self._original_methods['wf_start_task'](task_id)

            # 이벤트 발행
            if result:
                task = workflow_manager.get_current_task()
                if task:
                    event = create_task_started_event(task.id, task.title)
                    self.event_bus.publish(event)
                    logger.debug(f"Published TASK_STARTED event for {task.title}")

            return result

        def complete_task_with_event(task_id: str, notes: str = ""):
            # 태스크 정보 미리 가져오기
            task = None
            if workflow_manager.current_plan:
                task = workflow_manager.current_plan.get_task_by_id(task_id)

            # 원본 메서드 호출
            result = self._original_methods['wf_complete_task'](task_id, notes)

            # 이벤트 발행
            if result and task:
                event = create_task_completed_event(task.id, task.title, notes)
                self.event_bus.publish(event)
                logger.debug(f"Published TASK_COMPLETED event for {task.title}")

            return result

        # 메서드 교체
        workflow_manager.create_plan = create_plan_with_event
        workflow_manager.start_task = start_task_with_event
        workflow_manager.complete_task = complete_task_with_event

    def integrate_context_manager(self, context_manager: ContextManager):
        """ContextManager에 이벤트 구독 통합"""
        logger.info("Integrating events into ContextManager")

        # 컨텍스트 업데이트 핸들러
        def on_context_update(event):
            update_type = event.data.get('update_type')

            if update_type == 'task_started':
                # 태스크 시작을 컨텍스트에 기록
                if hasattr(context_manager, 'add_workflow_event'):
                    context_manager.add_workflow_event({
                        'type': 'task_started',
                        'task_id': event.data.get('task_id'),
                        'task_title': event.data.get('task_title'),
                        'timestamp': event.timestamp
                    })

            elif update_type == 'file_accessed':
                # 파일 접근을 컨텍스트에 기록
                if hasattr(context_manager, 'add_file_access'):
                    context_manager.add_file_access(
                        event.data.get('file_path'),
                        event.data.get('operation'),
                        event.data.get('task_id')
                    )

        # 이벤트 구독
        self.event_bus.subscribe(EventTypes.CONTEXT_UPDATED, on_context_update)

    def integrate_file_operations(self):
        """파일 작업에 이벤트 발행 통합"""
        logger.info("Integrating events into file operations")

        # ai_helpers의 파일 함수들 래핑
        try:
            import ai_helpers

            if hasattr(ai_helpers, 'create_file'):
                original_create = ai_helpers.create_file

                def create_file_with_event(path, content):
                    # 원본 함수 호출
                    result = original_create(path, content)

                    # 이벤트 발행
                    if result.ok:
                        event = create_file_access_event(path, 'create')
                        self.event_bus.publish(event)

                    return result

                ai_helpers.create_file = create_file_with_event

        except ImportError:
            logger.warning("ai_helpers not available for integration")


# 싱글톤 인스턴스
_adapter_instance = None


def get_event_adapter() -> EventIntegrationAdapter:
    """어댑터 싱글톤 인스턴스 반환"""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = EventIntegrationAdapter()
    return _adapter_instance


def integrate_all():
    """모든 시스템에 이벤트 통합"""
    adapter = get_event_adapter()

    # WorkflowManager 통합
    try:
        from workflow.workflow_manager import WorkflowManager
        wf_manager = WorkflowManager()
        adapter.integrate_workflow_manager(wf_manager)
        logger.info("✓ WorkflowManager 이벤트 통합 완료")
    except Exception as e:
        logger.error(f"WorkflowManager 통합 실패: {e}")

    # ContextManager 통합
    try:
        from core.context_manager import ContextManager
        ctx_manager = ContextManager()
        adapter.integrate_context_manager(ctx_manager)
        logger.info("✓ ContextManager 이벤트 통합 완료")
    except Exception as e:
        logger.error(f"ContextManager 통합 실패: {e}")

    # 파일 작업 통합
    adapter.integrate_file_operations()
    logger.info("✓ 파일 작업 이벤트 통합 완료")

    return adapter
