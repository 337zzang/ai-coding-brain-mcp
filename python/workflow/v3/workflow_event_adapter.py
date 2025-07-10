"""
Workflow Event Adapter
=====================

WorkflowManager가 EventBus를 사용하도록 하는 어댑터입니다.
상태 변경 시 이벤트를 발행하고, 프로젝트 전환 이벤트를 구독합니다.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from python.workflow.v3.event_bus import event_bus
from python.workflow.v3.event_types import (
    EventType,
    create_plan_event,
    create_task_event,
    create_project_event,
    create_context_event
)

logger = logging.getLogger(__name__)


class WorkflowEventAdapter:
    """
    WorkflowManager와 EventBus를 연결하는 어댑터

    WorkflowManager의 상태 변경을 이벤트로 발행하고,
    외부 이벤트를 구독하여 WorkflowManager에 전달합니다.
    """

    def __init__(self, workflow_manager):
        """
        Args:
            workflow_manager: WorkflowV3Manager 인스턴스
        """
        self.workflow_manager = workflow_manager
        self._register_handlers()

        logger.info("WorkflowEventAdapter initialized")

    def _register_handlers(self):
        """이벤트 핸들러 등록"""
        # 프로젝트 전환 이벤트 구독
        event_bus.subscribe(EventType.PROJECT_SWITCHED.value, self._on_project_switched)

        logger.debug("Event handlers registered in WorkflowEventAdapter")

    def _on_project_switched(self, event):
        """PROJECT_SWITCHED 이벤트 핸들러"""
        if hasattr(event, 'project_name'):
            logger.info(f"Received PROJECT_SWITCHED event: {event.project_name}")

            # WorkflowManager의 프로젝트 전환 처리
            # 이미 WorkflowManager가 프로젝트별로 인스턴스화되므로
            # 여기서는 상태 저장 후 PROJECT_LOADED 이벤트 발행

            # 현재 상태 저장
            if self.workflow_manager.state.current_plan:
                self.workflow_manager.save_data()

            # PROJECT_LOADED 이벤트 발행
            loaded_event = create_project_event(
                EventType.PROJECT_LOADED,
                project_name=event.project_name,
                workflow_info={
                    'has_active_plan': bool(self.workflow_manager.state.current_plan),
                    'plan_name': self.workflow_manager.state.current_plan.name if self.workflow_manager.state.current_plan else None,
                    'total_tasks': len(self.workflow_manager.state.current_plan.tasks) if self.workflow_manager.state.current_plan else 0
                }
            )
            event_bus.publish(loaded_event)

    # === 플랜 관련 이벤트 발행 ===

    def publish_plan_created(self, plan):
        """플랜 생성 이벤트 발행"""
        event = create_plan_event(
            EventType.PLAN_CREATED,
            plan_id=plan.id,
            plan_name=plan.name,
            plan_status=plan.status.value,
            project_name=self.workflow_manager.project_name,
            description=plan.description
        )
        event_bus.publish(event)
        logger.debug(f"Published PLAN_CREATED: {plan.name}")

    def publish_plan_started(self, plan):
        """플랜 시작 이벤트 발행"""
        event = create_plan_event(
            EventType.PLAN_STARTED,
            plan_id=plan.id,
            plan_name=plan.name,
            plan_status=plan.status.value,
            project_name=self.workflow_manager.project_name
        )
        event_bus.publish(event)
        logger.debug(f"Published PLAN_STARTED: {plan.name}")

    def publish_plan_completed(self, plan):
        """플랜 완료 이벤트 발행"""
        event = create_plan_event(
            EventType.PLAN_COMPLETED,
            plan_id=plan.id,
            plan_name=plan.name,
            plan_status=plan.status.value,
            project_name=self.workflow_manager.project_name,
            completed_at=datetime.now().isoformat()
        )
        event_bus.publish(event)
        logger.debug(f"Published PLAN_COMPLETED: {plan.name}")

    def publish_plan_archived(self, plan):
        """플랜 보관 이벤트 발행"""
        event = create_plan_event(
            EventType.PLAN_ARCHIVED,
            plan_id=plan.id,
            plan_name=plan.name,
            plan_status=plan.status.value,
            project_name=self.workflow_manager.project_name,
            archived_at=datetime.now().isoformat()
        )
        event_bus.publish(event)
        logger.debug(f"Published PLAN_ARCHIVED: {plan.name}")

    # === 태스크 관련 이벤트 발행 ===

    def publish_task_added(self, task, plan):
        """태스크 추가 이벤트 발행"""
        event = create_task_event(
            EventType.TASK_ADDED,
            task_id=task.id,
            task_title=task.title,
            task_status=task.status.value,
            plan_id=plan.id,
            project_name=self.workflow_manager.project_name
        )
        event_bus.publish(event)
        logger.debug(f"Published TASK_ADDED: {task.title}")

    def publish_task_started(self, task, plan):
        """태스크 시작 이벤트 발행"""
        event = create_task_event(
            EventType.TASK_STARTED,
            task_id=task.id,
            task_title=task.title,
            task_status=task.status.value,
            plan_id=plan.id,
            project_name=self.workflow_manager.project_name
        )
        event_bus.publish(event)
        logger.debug(f"Published TASK_STARTED: {task.title}")

    def publish_task_completed(self, task, plan):
        """태스크 완료 이벤트 발행"""
        event = create_task_event(
            EventType.TASK_COMPLETED,
            task_id=task.id,
            task_title=task.title,
            task_status=task.status.value,
            plan_id=plan.id,
            project_name=self.workflow_manager.project_name,
            completed_at=datetime.now().isoformat()
        )
        event_bus.publish(event)
        logger.debug(f"Published TASK_COMPLETED: {task.title}")

    # === 컨텍스트 동기화 이벤트 ===

    def publish_context_update(self, context_type: str, data: Dict[str, Any]):
        """컨텍스트 업데이트 이벤트 발행"""
        event = create_context_event(
            EventType.CONTEXT_UPDATED,
            context_type=context_type,
            context_data=data,
            project_name=self.workflow_manager.project_name
        )
        event_bus.publish(event)
        logger.debug(f"Published CONTEXT_UPDATED: {context_type}")

    def cleanup(self):
        """정리 작업 (이벤트 핸들러 제거)"""
        event_bus.unsubscribe(EventType.PROJECT_SWITCHED.value, self._on_project_switched)
        logger.info("WorkflowEventAdapter cleanup completed")


# === WorkflowManager 확장 함수 ===

def inject_event_publishing(workflow_manager):
    """
    기존 WorkflowManager에 이벤트 발행 기능 주입

    메서드를 래핑하여 상태 변경 시 자동으로 이벤트를 발행합니다.
    """
    # EventAdapter 생성
    adapter = WorkflowEventAdapter(workflow_manager)
    workflow_manager._event_adapter = adapter

    # 원본 메서드 저장
    original_create_plan = workflow_manager.create_plan
    original_add_task = workflow_manager.add_task
    original_complete_task = workflow_manager.complete_task
    original_archive_current_plan = workflow_manager.archive_current_plan

    # 메서드 래핑
    def create_plan_with_event(*args, **kwargs):
        result = original_create_plan(*args, **kwargs)
        if result and workflow_manager.state.current_plan:
            adapter.publish_plan_created(workflow_manager.state.current_plan)
        return result

    def add_task_with_event(*args, **kwargs):
        result = original_add_task(*args, **kwargs)
        if result and workflow_manager.state.current_plan:
            # 방금 추가된 태스크 찾기
            tasks = workflow_manager.state.current_plan.tasks
            if tasks:
                new_task = tasks[-1]  # 마지막 태스크가 새로 추가된 것
                adapter.publish_task_added(new_task, workflow_manager.state.current_plan)
        return result

    def complete_task_with_event(task_id: str, *args, **kwargs):
        # 태스크 찾기
        task = None
        if workflow_manager.state.current_plan:
            for t in workflow_manager.state.current_plan.tasks:
                if t.id == task_id:
                    task = t
                    break

        result = original_complete_task(task_id, *args, **kwargs)

        if result and task and workflow_manager.state.current_plan:
            adapter.publish_task_completed(task, workflow_manager.state.current_plan)

        return result

    def archive_with_event(*args, **kwargs):
        plan = workflow_manager.state.current_plan
        result = original_archive_current_plan(*args, **kwargs)

        if result and plan:
            adapter.publish_plan_archived(plan)

        return result

    # 메서드 교체
    workflow_manager.create_plan = create_plan_with_event
    workflow_manager.add_task = add_task_with_event
    workflow_manager.complete_task = complete_task_with_event
    workflow_manager.archive_current_plan = archive_with_event

    logger.info("Event publishing injected into WorkflowManager")

    return adapter
