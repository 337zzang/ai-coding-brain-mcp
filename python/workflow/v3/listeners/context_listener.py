"""
컨텍스트 자동 업데이트 리스너
"""
from typing import Set, Optional, Dict, Any
import logging
from datetime import datetime

from .base import BaseEventListener
from python.workflow.v3.models import WorkflowEvent
from python.events.unified_event_types import EventType

logger = logging.getLogger(__name__)


class ContextUpdateListener(BaseEventListener):
    """컨텍스트 자동 업데이트 리스너

    워크플로우 이벤트를 받아 자동으로 컨텍스트를 업데이트합니다.
    기존의 수동 ContextIntegration.record_event 호출을 대체합니다.
    """

    def __init__(self, context_integration, enabled: bool = True):
        """
        Args:
            context_integration: ContextIntegration 인스턴스
            enabled: 리스너 활성화 여부
        """
        super().__init__(enabled)
        self.context = context_integration
        self._update_buffer = []  # 배치 업데이트를 위한 버퍼

    def get_subscribed_events(self) -> Set[EventType]:
        """구독할 이벤트 타입"""
        return {
            # 플랜 관련
            EventType.PLAN_CREATED,
            EventType.PLAN_STARTED,
            EventType.PLAN_COMPLETED,
            EventType.PLAN_ARCHIVED,

            # 태스크 관련
            EventType.TASK_ADDED,
            EventType.TASK_STARTED,
            EventType.TASK_COMPLETED,
            EventType.TASK_FAILED,
            EventType.TASK_BLOCKED,
            EventType.TASK_UNBLOCKED,

            # 프로젝트 관련
            EventType.PROJECT_SWITCHED,
            EventType.PROJECT_LOADED,
        }

    def handle_event(self, event: WorkflowEvent) -> Optional[Dict[str, Any]]:
        """이벤트 처리"""
        logger.debug(f"ContextUpdateListener processing {event.type}")

        # 이벤트 타입별 처리
        if event.type == EventType.PLAN_CREATED:
            return self._handle_plan_created(event)
        elif event.type == EventType.PLAN_STARTED:
            return self._handle_plan_started(event)
        elif event.type == EventType.PLAN_COMPLETED:
            return self._handle_plan_completed(event)
        elif event.type == EventType.TASK_STARTED:
            return self._handle_task_started(event)
        elif event.type == EventType.TASK_COMPLETED:
            return self._handle_task_completed(event)
        elif event.type == EventType.TASK_FAILED:
            return self._handle_task_failed(event)
        elif event.type == EventType.TASK_BLOCKED:
            return self._handle_task_blocked(event)
        elif event.type == EventType.PROJECT_SWITCHED:
            return self._handle_project_switched(event)

        return None

    def _handle_plan_created(self, event: WorkflowEvent) -> Dict[str, Any]:
        """플랜 생성 처리"""
        plan_info = {
            "event_type": "plan_created",
            "plan_id": event.plan_id,
            "plan_name": event.details.get("plan_name", "Unknown"),
            "description": event.details.get("description", ""),
            "created_at": event.timestamp.isoformat(),
            "created_by": event.user
        }

        # 컨텍스트에 플랜 정보 추가
        self.context.add_workflow_event(plan_info)

        return {"context_updated": True, "type": "plan_created"}

    def _handle_plan_completed(self, event: WorkflowEvent) -> Dict[str, Any]:
        """플랜 완료 처리"""
        plan_summary = {
            "event_type": "plan_completed",
            "plan_id": event.plan_id,
            "plan_name": event.details.get("plan_name", "Unknown"),
            "completed_at": event.timestamp.isoformat(),
            "total_tasks": event.details.get("total_tasks", 0),
            "completed_tasks": event.details.get("completed_tasks", 0),
            "duration": event.details.get("duration", "Unknown"),
            "summary": f"플랜 '{event.details.get('plan_name', 'Unknown')}' 완료"
        }

        # 플랜 완료 요약 생성
        self.context.add_workflow_summary(plan_summary)

        return {"context_updated": True, "type": "plan_completed"}

    def _handle_task_started(self, event: WorkflowEvent) -> Dict[str, Any]:
        """태스크 시작 처리"""
        task_info = {
            "event_type": "task_started",
            "task_id": event.task_id,
            "task_title": event.details.get("task_title", "Unknown"),
            "started_at": event.timestamp.isoformat(),
            "plan_id": event.plan_id
        }

        # 현재 작업 상태 업데이트
        self.context.update_current_task(task_info)

        return {"context_updated": True, "type": "task_started"}

    def _handle_task_completed(self, event: WorkflowEvent) -> Dict[str, Any]:
        """태스크 완료 처리"""
        task_result = {
            "event_type": "task_completed",
            "task_id": event.task_id,
            "task_title": event.details.get("task_title", "Unknown"),
            "completed_at": event.timestamp.isoformat(),
            "duration": event.details.get("duration", "Unknown"),
            "notes": event.details.get("notes", []),
            "outputs": event.details.get("outputs", {}),
            "success": True
        }

        # 태스크 결과 기록
        self.context.add_task_result(task_result)

        # 진행률 업데이트
        progress = event.details.get("progress", {})
        if progress:
            self.context.update_progress(progress)

        return {"context_updated": True, "type": "task_completed"}

    def _handle_task_failed(self, event: WorkflowEvent) -> Dict[str, Any]:
        """태스크 실패 처리"""
        failure_info = {
            "event_type": "task_failed",
            "task_id": event.task_id,
            "task_title": event.details.get("task_title", "Unknown"),
            "failed_at": event.timestamp.isoformat(),
            "error": event.details.get("error", "Unknown error"),
            "retry_count": event.details.get("retry_count", 0),
            "success": False
        }

        # 실패 정보 기록
        self.context.add_task_result(failure_info)
        self.context.add_error(failure_info)

        return {"context_updated": True, "type": "task_failed"}

    def _handle_task_blocked(self, event: WorkflowEvent) -> Dict[str, Any]:
        """태스크 차단 처리"""
        blocked_info = {
            "event_type": "task_blocked",
            "task_id": event.task_id,
            "task_title": event.details.get("task_title", "Unknown"),
            "blocked_at": event.timestamp.isoformat(),
            "blocker": event.details.get("blocker", "Unknown"),
            "status": "blocked"
        }

        # 차단 정보 기록
        self.context.add_blocked_task(blocked_info)

        return {"context_updated": True, "type": "task_blocked"}

    def _handle_project_switched(self, event: WorkflowEvent) -> Dict[str, Any]:
        """프로젝트 전환 처리"""
        # 컨텍스트 저장 및 새 프로젝트 로드
        project_name = event.details.get("project_name")
        if project_name:
            self.context.switch_project(project_name)

        return {"context_updated": True, "type": "project_switched"}

    def flush_updates(self):
        """버퍼에 있는 업데이트 즉시 처리"""
        if self._update_buffer:
            # 배치 업데이트 로직 (필요시 구현)
            self._update_buffer.clear()
