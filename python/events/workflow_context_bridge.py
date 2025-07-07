"""
Workflow-Context Bridge Implementation
워크플로우와 컨텍스트 매니저를 연결하는 브릿지
"""

from typing import Optional, Dict, Any
import logging
from events.event_bus import get_event_bus, Event, subscribe_to
from events.event_types import EventTypes, TaskEvent, FileEvent, ContextEvent

logger = logging.getLogger(__name__)


class WorkflowContextBridge:
    """워크플로우와 컨텍스트 매니저를 연결하는 브릿지"""

    def __init__(self):
        self.event_bus = get_event_bus()
        self.current_task_id: Optional[str] = None
        self.current_plan_id: Optional[str] = None
        self._setup_handlers()
        logger.info("WorkflowContextBridge initialized")

    def _setup_handlers(self):
        """이벤트 핸들러 설정"""
        # 워크플로우 이벤트 구독
        self.event_bus.subscribe(EventTypes.WORKFLOW_TASK_STARTED, self._on_task_started)
        self.event_bus.subscribe(EventTypes.WORKFLOW_TASK_COMPLETED, self._on_task_completed)
        self.event_bus.subscribe(EventTypes.WORKFLOW_PLAN_CREATED, self._on_plan_created)

        # 파일 시스템 이벤트 구독
        self.event_bus.subscribe(EventTypes.FILE_CREATED, self._on_file_created)
        self.event_bus.subscribe(EventTypes.FILE_ACCESSED, self._on_file_accessed)
        self.event_bus.subscribe(EventTypes.FILE_MODIFIED, self._on_file_modified)

        # 프로젝트 전환 이벤트 구독
        self.event_bus.subscribe(EventTypes.CONTEXT_PROJECT_SWITCHED, self._on_project_switched)

    def _on_task_started(self, event: Event):
        """태스크 시작 시 처리"""
        self.current_task_id = event.data.get('task_id')
        logger.info(f"Task started: {self.current_task_id}")

        # 컨텍스트 업데이트 이벤트 발행
        context_update = ContextEvent(
            EventTypes.CONTEXT_UPDATED,
            update_type='task_started',
            task_id=self.current_task_id,
            task_title=event.data.get('task_title')
        )
        self.event_bus.publish(context_update)

    def _on_task_completed(self, event: Event):
        """태스크 완료 시 처리"""
        task_id = event.data.get('task_id')
        logger.info(f"Task completed: {task_id}")

        # 컨텍스트 업데이트 이벤트 발행
        context_update = ContextEvent(
            EventTypes.CONTEXT_UPDATED,
            update_type='task_completed',
            task_id=task_id,
            completion_notes=event.data.get('completion_notes', '')
        )
        self.event_bus.publish(context_update)

        # 현재 태스크 ID 초기화
        if self.current_task_id == task_id:
            self.current_task_id = None

    def _on_plan_created(self, event: Event):
        """계획 생성 시 처리"""
        self.current_plan_id = event.data.get('plan_id')
        logger.info(f"Plan created: {self.current_plan_id}")

        # 컨텍스트 업데이트 이벤트 발행
        context_update = ContextEvent(
            EventTypes.CONTEXT_UPDATED,
            update_type='plan_created',
            plan_id=self.current_plan_id,
            plan_name=event.data.get('plan_name')
        )
        self.event_bus.publish(context_update)

    def _on_file_created(self, event: Event):
        """파일 생성 시 처리"""
        self._handle_file_event(event, 'created')

    def _on_file_accessed(self, event: Event):
        """파일 접근 시 처리"""
        self._handle_file_event(event, 'accessed')

    def _on_file_modified(self, event: Event):
        """파일 수정 시 처리"""
        self._handle_file_event(event, 'modified')

    def _handle_file_event(self, event: Event, operation: str):
        """파일 이벤트 공통 처리"""
        # 현재 태스크 ID를 파일 이벤트에 추가
        file_path = event.data.get('file_path')

        # 이미 task_id가 있으면 그대로 사용, 없으면 현재 task_id 추가
        task_id = event.data.get('task_id') or self.current_task_id

        logger.debug(f"File {operation}: {file_path} (task: {task_id})")

        # 컨텍스트 업데이트 이벤트 발행
        context_update = ContextEvent(
            EventTypes.CONTEXT_UPDATED,
            update_type=f'file_{operation}',
            file_path=file_path,
            task_id=task_id,
            operation=operation
        )
        self.event_bus.publish(context_update)

    def _on_project_switched(self, event: Event):
        """프로젝트 전환 시 처리"""
        # 현재 태스크와 계획 초기화
        self.current_task_id = None
        self.current_plan_id = None

        logger.info(f"Project switched to: {event.data.get('project_name')}")

    def get_current_context(self) -> Dict[str, Any]:
        """현재 브릿지 컨텍스트 반환"""
        return {
            'current_task_id': self.current_task_id,
            'current_plan_id': self.current_plan_id
        }


# 싱글톤 인스턴스
_bridge_instance = None


def get_workflow_context_bridge() -> WorkflowContextBridge:
    """브릿지 싱글톤 인스턴스 반환"""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = WorkflowContextBridge()
    return _bridge_instance


# 편의 함수들
def set_current_task(task_id: str):
    """현재 작업 중인 태스크 설정"""
    bridge = get_workflow_context_bridge()
    bridge.current_task_id = task_id


def get_current_task_id() -> Optional[str]:
    """현재 작업 중인 태스크 ID 반환"""
    bridge = get_workflow_context_bridge()
    return bridge.current_task_id
