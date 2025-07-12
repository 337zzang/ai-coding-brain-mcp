"""
에러 및 실패 이벤트 처리 리스너
"""
from typing import Set, Optional, Dict, Any
import logging
from datetime import datetime

from .base import BaseEventListener
from python.workflow.v3.models import WorkflowEvent, TaskStatus
from python.events.unified_event_types import EventType

logger = logging.getLogger(__name__)


class ErrorHandlerListener(BaseEventListener):
    """에러 및 실패 이벤트 자동 처리 리스너

    TASK_FAILED, TASK_BLOCKED, SYSTEM_ERROR 등의 이벤트를 처리하여
    자동 복구, 재시도, 알림 등의 작업을 수행합니다.
    """

    def __init__(self, workflow_manager, retry_limit: int = 3, enabled: bool = True):
        """
        Args:
            workflow_manager: WorkflowManager 인스턴스
            retry_limit: 자동 재시도 최대 횟수
            enabled: 리스너 활성화 여부
        """
        super().__init__(enabled)
        self.workflow_manager = workflow_manager
        self.retry_limit = retry_limit
        self.retry_counts: Dict[str, int] = {}  # task_id -> retry count
        self.error_history: Dict[str, list] = {}  # task_id -> error list

    def get_subscribed_events(self) -> Set[EventType]:
        """구독할 이벤트 타입"""
        return {
            EventType.TASK_FAILED,
            EventType.TASK_BLOCKED,
            EventType.SYSTEM_ERROR
        }

    def handle_event(self, event: WorkflowEvent) -> Optional[Dict[str, Any]]:
        """이벤트 처리"""
        logger.info(f"ErrorHandlerListener processing {event.type} event")

        if event.type == EventType.TASK_FAILED:
            return self._handle_task_failed(event)
        elif event.type == EventType.TASK_BLOCKED:
            return self._handle_task_blocked(event)
        elif event.type == EventType.SYSTEM_ERROR:
            return self._handle_system_error(event)

        return None

    def _handle_task_failed(self, event: WorkflowEvent) -> Dict[str, Any]:
        """태스크 실패 처리"""
        task_id = event.task_id
        error = event.details.get("error", "Unknown error")
        task_title = event.details.get("task_title", "Unknown task")

        # 에러 기록
        if task_id not in self.error_history:
            self.error_history[task_id] = []
        self.error_history[task_id].append({
            "timestamp": event.timestamp.isoformat(),
            "error": error
        })

        # 재시도 횟수 확인
        retry_count = self.retry_counts.get(task_id, 0)

        if retry_count < self.retry_limit:
            # 자동 재시도
            logger.info(f"Retrying task {task_id} ({retry_count + 1}/{self.retry_limit})")
            self.retry_counts[task_id] = retry_count + 1

            # 태스크 상태를 다시 진행중으로 변경
            self._retry_task(task_id)

            return {
                "action": "retry",
                "task_id": task_id,
                "retry_count": retry_count + 1,
                "max_retries": self.retry_limit
            }
        else:
            # 재시도 한계 초과 - 플랜 일시정지
            logger.error(
                f"Task {task_id} failed after {self.retry_limit} retries. "
                f"Pausing plan."
            )

            # 플랜을 일시정지 상태로 변경 (구현 필요)
            self._pause_current_plan(f"Task '{task_title}' failed after {self.retry_limit} retries")

            return {
                "action": "plan_paused",
                "task_id": task_id,
                "reason": "max_retries_exceeded",
                "error_history": self.error_history[task_id]
            }

    def _handle_task_blocked(self, event: WorkflowEvent) -> Dict[str, Any]:
        """태스크 차단 처리"""
        task_id = event.task_id
        blocker = event.details.get("blocker", "Unknown blocker")
        task_title = event.details.get("task_title", "Unknown task")

        logger.warning(f"Task {task_id} blocked: {blocker}")

        # 차단 정보 기록
        blocked_info = {
            "task_id": task_id,
            "task_title": task_title,
            "blocker": blocker,
            "blocked_at": event.timestamp.isoformat()
        }

        # 컨텍스트에 차단 정보 저장 (다른 태스크가 해결할 수 있도록)
        self._record_blocked_task(blocked_info)

        # 다른 실행 가능한 태스크 찾기
        alternative_task = self._find_alternative_task()

        if alternative_task:
            logger.info(f"Found alternative task: {alternative_task.title}")
            return {
                "action": "switch_task",
                "blocked_task_id": task_id,
                "alternative_task_id": alternative_task.id,
                "blocker": blocker
            }
        else:
            logger.warning("No alternative tasks available")
            return {
                "action": "wait_for_unblock",
                "task_id": task_id,
                "blocker": blocker
            }

    def _handle_system_error(self, event: WorkflowEvent) -> Dict[str, Any]:
        """시스템 에러 처리"""
        error = event.details.get("error", "Unknown system error")
        severity = event.details.get("severity", "error")

        logger.error(f"System error: {error}")

        if severity == "critical":
            # 심각한 에러 - 모든 작업 중단
            self._emergency_stop("Critical system error detected")
            return {
                "action": "emergency_stop",
                "error": error,
                "severity": severity
            }
        else:
            # 일반 에러 - 로깅하고 계속
            return {
                "action": "logged",
                "error": error,
                "severity": severity
            }

    def _retry_task(self, task_id: str):
        """태스크 재시도"""
        # WorkflowManager의 태스크 상태 변경 메서드 호출
        if hasattr(self.workflow_manager, 'retry_task'):
            self.workflow_manager.retry_task(task_id)
        else:
            logger.warning("WorkflowManager doesn't support retry_task method")

    def _pause_current_plan(self, reason: str):
        """현재 플랜 일시정지"""
        if hasattr(self.workflow_manager, 'pause_plan'):
            self.workflow_manager.pause_plan(reason)
        else:
            logger.warning("WorkflowManager doesn't support pause_plan method")

    def _record_blocked_task(self, blocked_info: dict):
        """차단된 태스크 정보 기록"""
        # 컨텍스트에 차단 정보 저장
        if hasattr(self.workflow_manager, 'context_integration'):
            self.workflow_manager.context_integration.add_blocked_task(blocked_info)

    def _find_alternative_task(self):
        """대체 가능한 태스크 찾기"""
        # 현재 플랜에서 실행 가능한 다른 태스크 찾기
        if hasattr(self.workflow_manager, 'get_executable_tasks'):
            tasks = self.workflow_manager.get_executable_tasks()
            return tasks[0] if tasks else None
        return None

    def _emergency_stop(self, reason: str):
        """긴급 중단"""
        logger.critical(f"Emergency stop: {reason}")
        # 모든 활동 중단 로직 (구현 필요)

    def get_error_report(self, task_id: Optional[str] = None) -> Dict[str, Any]:
        """에러 리포트 생성

        Args:
            task_id: 특정 태스크 ID (None이면 전체)

        Returns:
            에러 리포트
        """
        if task_id:
            return {
                "task_id": task_id,
                "retry_count": self.retry_counts.get(task_id, 0),
                "error_history": self.error_history.get(task_id, [])
            }
        else:
            return {
                "total_errors": sum(len(errors) for errors in self.error_history.values()),
                "tasks_with_errors": len(self.error_history),
                "retry_counts": self.retry_counts,
                "error_history": self.error_history
            }
