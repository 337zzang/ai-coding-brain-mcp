"""
직접 호출을 이벤트로 대체하는 리스너들
"""
from typing import Dict, Any, List
import logging
from pathlib import Path
import json

from ..models import EventType, WorkflowEvent
from .base import BaseEventListener

logger = logging.getLogger(__name__)


class TaskAutoProgressListener(BaseEventListener):
    """태스크 완료 시 자동으로 다음 태스크 시작"""

    def __init__(self, workflow_manager, enabled: bool = True):
        super().__init__(enabled)
        self.workflow_manager = workflow_manager

    def get_subscribed_events(self) -> List[EventType]:
        return [EventType.TASK_COMPLETED]

    def handle_event(self, event: WorkflowEvent) -> None:
        """태스크 완료 시 자동으로 다음 태스크 시작"""
        if not self.enabled:
            return
            
        try:
            # 다음 태스크 자동 시작
            if hasattr(self.workflow_manager, 'auto_start_next_task'):
                self.workflow_manager.auto_start_next_task()
                logger.info("Auto-started next task")
        except Exception as e:
            logger.error(f"TaskAutoProgressListener error: {e}")


class PlanAutoArchiveListener(BaseEventListener):
    """플랜 완료 시 자동 보관"""

    def __init__(self, workflow_manager, enabled: bool = True):
        super().__init__(enabled)
        self.workflow_manager = workflow_manager

    def get_subscribed_events(self) -> List[EventType]:
        return [EventType.PLAN_COMPLETED]

    def handle_event(self, event: WorkflowEvent) -> None:
        """플랜 완료 시 자동 보관"""
        if not self.enabled:
            return
            
        try:
            # 플랜 자동 보관
            if hasattr(self.workflow_manager, 'archive_completed_plan'):
                self.workflow_manager.archive_completed_plan(event.plan_id)
                logger.info(f"Auto-archived completed plan: {event.plan_id}")
        except Exception as e:
            logger.error(f"PlanAutoArchiveListener error: {e}")


# Export all listeners
__all__ = [
    'TaskAutoProgressListener',
    'PlanAutoArchiveListener',
    'ContextSyncListener',
    'AutoSaveListener',
    'GitCommitListener'
]


