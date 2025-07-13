"""
ErrorHandlerListener - 오류 처리 및 재시도 리스너
"""
import logging
from typing import List
from ..models import EventType, WorkflowEvent
from .base import BaseEventListener

logger = logging.getLogger(__name__)


class ErrorHandlerListener(BaseEventListener):
    """태스크 실패 시 재시도 처리 리스너"""

    def __init__(self, workflow_manager, retry_limit: int = 3, enabled: bool = True):
        super().__init__(enabled)
        self.workflow_manager = workflow_manager
        self.retry_limit = retry_limit
        self.retry_counts = {}  # task_id -> retry_count

    def get_subscribed_events(self) -> List[EventType]:
        """구독할 이벤트 타입"""
        return [
            EventType.TASK_FAILED,
            EventType.TASK_BLOCKED
        ]

    def handle_event(self, event: WorkflowEvent) -> None:
        """이벤트 처리"""
        if not self.enabled:
            return

        try:
            task_id = event.task_id
            if not task_id:
                return

            # 재시도 횟수 확인
            retry_count = self.retry_counts.get(task_id, 0)
            
            if event.type == EventType.TASK_FAILED:
                if retry_count < self.retry_limit:
                    # 재시도
                    self.retry_counts[task_id] = retry_count + 1
                    logger.info(f"Retrying task {task_id} (attempt {retry_count + 1}/{self.retry_limit})")
                    
                    # WorkflowManager의 retry_task 메서드 호출
                    if hasattr(self.workflow_manager, 'retry_task'):
                        self.workflow_manager.retry_task(task_id)
                else:
                    # 재시도 한계 도달
                    logger.error(f"Task {task_id} failed after {self.retry_limit} retries")
                    if hasattr(self.workflow_manager, 'pause_plan'):
                        self.workflow_manager.pause_plan(f"Task {task_id} failed repeatedly")
                        
            elif event.type == EventType.TASK_BLOCKED:
                # 블록된 태스크 처리
                logger.warning(f"Task {task_id} is blocked")
                details = event.details or {}
                blocker = details.get('blocker', 'Unknown reason')
                
                if hasattr(self.workflow_manager, 'handle_blocked_task'):
                    self.workflow_manager.handle_blocked_task(task_id, blocker)
                    
        except Exception as e:
            logger.error(f"ErrorHandlerListener error: {e}")
