"""ErrorCollectorListener - 오류 수집 및 보고 리스너"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import logging

from ..models import EventType, WorkflowEvent
from .base import BaseEventListener

logger = logging.getLogger(__name__)


class ErrorCollectorListener(BaseEventListener):
    """오류 수집 및 보고 리스너"""

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self.error_log_path = Path("memory/error_log.json")
        self.errors = {}

    def get_subscribed_events(self) -> List[EventType]:
        """구독할 이벤트 타입"""
        return [EventType.TASK_FAILED]

    def handle_event(self, event: WorkflowEvent) -> None:
        """이벤트 처리"""
        if not self.enabled:
            return

        if event.type == EventType.TASK_FAILED:
            self._collect_error(event)

    def _collect_error(self, event: WorkflowEvent) -> None:
        """오류 수집"""
        plan_id = event.plan_id or "unknown"
        error_entry = {
            "timestamp": event.timestamp,
            "task_id": event.task_id,
            "error": event.details.get("error", "Unknown") if event.details else "Unknown"
        }

        if plan_id not in self.errors:
            self.errors[plan_id] = []
        self.errors[plan_id].append(error_entry)

        # 저장
        self.error_log_path.parent.mkdir(exist_ok=True)
        self.error_log_path.write_text(
            json.dumps(self.errors, indent=2),
            encoding='utf-8'
        )

        print(f"⚠️ 오류 수집됨: {error_entry}")
