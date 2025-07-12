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


class ContextSyncListener(BaseEventListener):
    """컨텍스트 동기화를 이벤트 기반으로 처리"""

    def __init__(self, context_integration, enabled: bool = True):
        super().__init__(enabled)
        self.context = context_integration

    def get_subscribed_events(self) -> List[EventType]:
        return [
            EventType.PLAN_CREATED,
            EventType.PLAN_STARTED,
            EventType.PLAN_COMPLETED,
            EventType.TASK_ADDED,
            EventType.TASK_COMPLETED
        ]

    def handle_event(self, event: WorkflowEvent) -> None:
        if not self.enabled:
            return

        try:
            # 플랜 관련 이벤트
            if event.type in [EventType.PLAN_CREATED, EventType.PLAN_STARTED]:
                plan = event.details.get('plan') if event.details else None
                if plan:
                    self.context.sync_plan_summary(plan)

            elif event.type == EventType.PLAN_COMPLETED:
                self.context.sync_plan_summary(None)  # 플랜 완료 시 초기화

            # 중요 이벤트 기록
            if event.type in [EventType.PLAN_CREATED, EventType.PLAN_COMPLETED, 
                            EventType.TASK_COMPLETED]:
                self.context.record_event(event)

        except Exception as e:
            logger.error(f"ContextSyncListener error: {e}")


class AutoSaveListener(BaseEventListener):
    """자동 저장을 이벤트 기반으로 처리"""

    def __init__(self, storage, enabled: bool = True):
        super().__init__(enabled)
        self.storage = storage
        self.save_counter = 0
        self.save_interval = 5  # 5개 이벤트마다 저장

    def get_subscribed_events(self) -> List[EventType]:
        # 모든 이벤트 타입 구독
        return list(EventType)

    def handle_event(self, event: WorkflowEvent) -> None:
        if not self.enabled:
            return

        self.save_counter += 1

        # 중요 이벤트는 즉시 저장
        important_events = [
            EventType.PLAN_CREATED,
            EventType.PLAN_COMPLETED,
            EventType.TASK_COMPLETED,
            EventType.TASK_FAILED
        ]

        if event.type in important_events or self.save_counter >= self.save_interval:
            try:
                # WorkflowManager의 상태를 가져와서 저장
                # 실제 구현에서는 WorkflowManager 참조 필요
                logger.debug(f"AutoSave triggered by {event.type}")
                self.save_counter = 0
            except Exception as e:
                logger.error(f"AutoSaveListener error: {e}")


class GitCommitListener(BaseEventListener):
    """Git 자동 커밋을 이벤트 기반으로 처리"""

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self.pending_changes = []

    def get_subscribed_events(self) -> List[EventType]:
        return [
            EventType.TASK_COMPLETED,
            EventType.PLAN_COMPLETED
        ]

    def handle_event(self, event: WorkflowEvent) -> None:
        if not self.enabled:
            return

        try:
            details = event.details or {}

            if event.type == EventType.TASK_COMPLETED:
                task_title = details.get('title', 'Task')
                commit_message = f"✅ Complete: {task_title}"
                self._auto_commit(commit_message)

            elif event.type == EventType.PLAN_COMPLETED:
                plan_name = details.get('name', 'Plan')
                commit_message = f"🎉 Complete Plan: {plan_name}"
                self._auto_commit(commit_message)

        except Exception as e:
            logger.error(f"GitCommitListener error: {e}")

    def _auto_commit(self, message: str):
        """Git 자동 커밋 수행"""
        try:
            # 실제 구현에서는 helpers.git_add(), helpers.git_commit() 사용
            logger.info(f"Auto-commit: {message}")
        except Exception as e:
            logger.debug(f"Auto-commit failed: {e}")


class AuditLogListener(BaseEventListener):
    """감사 로그를 이벤트 기반으로 처리"""

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self.audit_log_path = Path("memory/audit_log.json")
        self.audit_entries = []

    def get_subscribed_events(self) -> List[EventType]:
        return list(EventType)  # 모든 이벤트 감사

    def handle_event(self, event: WorkflowEvent) -> None:
        if not self.enabled:
            return

        audit_entry = {
            'timestamp': event.timestamp,
            'event_type': event.type.value if hasattr(event.type, 'value') else str(event.type),
            'event_id': event.id,
            'plan_id': event.plan_id,
            'task_id': event.task_id,
            'user': event.user,
            'metadata': event.metadata
        }

        self.audit_entries.append(audit_entry)

        # 10개마다 파일에 저장
        if len(self.audit_entries) >= 10:
            self._save_audit_log()

    def _save_audit_log(self):
        """감사 로그 저장"""
        try:
            existing = []
            if self.audit_log_path.exists():
                with open(self.audit_log_path, 'r', encoding='utf-8') as f:
                    existing = json.load(f)

            existing.extend(self.audit_entries)

            self.audit_log_path.parent.mkdir(exist_ok=True)
            with open(self.audit_log_path, 'w', encoding='utf-8') as f:
                json.dump(existing, f, indent=2, ensure_ascii=False)

            self.audit_entries.clear()
            logger.debug(f"Audit log saved: {len(existing)} entries")

        except Exception as e:
            logger.error(f"Failed to save audit log: {e}")
