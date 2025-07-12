"""
이벤트 리스너 시스템 초기화 및 통합
"""
import logging
from typing import Optional

from python.workflow.v3.event_bus import EventBus
from python.workflow.v3.listener_manager import ListenerManager
from python.workflow.v3.listeners import ErrorHandlerListener
from python.workflow.v3.events import GitAutoCommitListener

logger = logging.getLogger(__name__)


def initialize_event_listeners(workflow_manager, helpers=None) -> Optional[ListenerManager]:
    """이벤트 리스너 시스템 초기화

    Args:
        workflow_manager: WorkflowManager 인스턴스
        helpers: helpers 객체 (Git 작업 등에 사용)

    Returns:
        ListenerManager 인스턴스 또는 None
    """
    try:
        # EventBus 인스턴스 가져오기
        event_bus = EventBus()

        # 리스너 매니저 생성
        listener_manager = ListenerManager(event_bus)

        # 1. ErrorHandlerListener 등록 (TASK_FAILED, TASK_BLOCKED 처리)
        error_listener = ErrorHandlerListener(
            workflow_manager,
            retry_limit=3,
            enabled=True
        )
        listener_manager.register_listener("error_handler", error_listener)
        logger.info("Registered ErrorHandlerListener for TASK_FAILED, TASK_BLOCKED events")

        # 2. GitAutoCommitListener 등록 (기존)
        if helpers:
            git_listener = GitAutoCommitListener(helpers)
            listener_manager.register_listener("git_auto_commit", git_listener)
            logger.info("Registered GitAutoCommitListener")

        # 3. 추가 리스너들은 추후 구현 예정
        # - ContextListener
        # - UIProgressListener
        # - AutoProgressListener

        logger.info(
            f"Event listener system initialized with "
            f"{len(listener_manager.listeners)} listeners"
        )

        # WorkflowManager에 연결
        if hasattr(workflow_manager, 'listener_manager'):
            workflow_manager.listener_manager = listener_manager

        return listener_manager

    except Exception as e:
        logger.error(f"Failed to initialize event listeners: {e}", exc_info=True)
        return None


def test_event_handling():
    """이벤트 처리 테스트"""
    from python.workflow.v3.models import WorkflowEvent, Task, TaskStatus
    from python.events.unified_event_types import EventType
    from datetime import datetime
    import uuid

    # 테스트용 WorkflowManager 모의 객체
    class MockWorkflowManager:
        def retry_task(self, task_id):
            print(f"[Mock] Retrying task: {task_id}")

        def pause_plan(self, reason):
            print(f"[Mock] Pausing plan: {reason}")

    # 초기화
    mock_manager = MockWorkflowManager()
    listener_manager = initialize_event_listeners(mock_manager)

    if not listener_manager:
        print("Failed to initialize listeners")
        return

    # 테스트 이벤트 생성
    test_events = [
        # TASK_FAILED 이벤트
        WorkflowEvent(
            id=str(uuid.uuid4()),
            type=EventType.TASK_FAILED,
            timestamp=datetime.now(),
            plan_id="test-plan-123",
            task_id="test-task-456",
            user="system",
            details={
                "task_title": "데이터베이스 연결 테스트",
                "error": "Connection timeout: Database server not responding"
            }
        ),
        # TASK_BLOCKED 이벤트
        WorkflowEvent(
            id=str(uuid.uuid4()),
            type=EventType.TASK_BLOCKED,
            timestamp=datetime.now(),
            plan_id="test-plan-123",
            task_id="test-task-789",
            user="system",
            details={
                "task_title": "API 배포",
                "blocker": "의존성 태스크 '데이터베이스 마이그레이션' 미완료"
            }
        )
    ]

    # 이벤트 발행
    event_bus = EventBus()

    print("\n=== 이벤트 처리 테스트 ===")
    for event in test_events:
        print(f"\n발행: {event.type} - {event.details.get('task_title')}")

        # Event 형식으로 변환하여 발행
        event_bus.emit(event.type.value, {
            "id": event.id,
            "type": event.type.value,
            "timestamp": event.timestamp,
            "payload": {
                "plan_id": event.plan_id,
                "task_id": event.task_id,
                "user": event.user,
                **event.details
            }
        })

    # 메트릭 확인
    import time
    time.sleep(0.5)  # 비동기 처리 대기

    print("\n=== 리스너 메트릭 ===")
    metrics = listener_manager.get_metrics()
    for name, metric in metrics.items():
        if name != "_summary":
            print(f"\n{name}:")
            print(f"  - 총 이벤트: {metric.get('total_events', 0)}")
            print(f"  - 성공: {metric.get('successful', 0)}")
            print(f"  - 실패: {metric.get('failed', 0)}")

    return listener_manager


# 테스트 실행
if __name__ == "__main__":
    test_event_handling()
