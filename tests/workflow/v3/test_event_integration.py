"""
WorkflowEventAdapter 통합 테스트 (핵심 문제 해결 후)
"""
import pytest
import sys
import time
from pathlib import Path
from unittest.mock import Mock
from datetime import datetime

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from python.workflow.v3.workflow_event_adapter import WorkflowEventAdapter
from python.workflow.v3.models import WorkflowEvent, WorkflowPlan, Task
from python.workflow.v3.event_types import EventType
from python.workflow.v3.event_bus import Event
from python.workflow.v3.listeners.base import BaseEventListener


class TestEventListener(BaseEventListener):
    """테스트용 이벤트 리스너"""
    def __init__(self):
        self.events_received = []

    def get_subscribed_events(self):
        """모든 이벤트 타입 구독"""
        return {
            EventType.TASK_STARTED,
            EventType.TASK_COMPLETED,
            EventType.PLAN_CREATED,
            EventType.TASK_ADDED
        }

    def handle_event(self, event: WorkflowEvent):
        """이벤트 처리"""
        self.events_received.append(event)
        return None


class TestWorkflowEventAdapter:
    """WorkflowEventAdapter 통합 테스트"""

    @pytest.fixture
    def mock_manager(self):
        """Mock WorkflowManager"""
        manager = Mock()
        manager.project_name = "test_project"
        return manager

    @pytest.fixture
    def adapter(self, mock_manager):
        """테스트용 어댑터"""
        adapter = WorkflowEventAdapter(mock_manager)
        yield adapter
        # 테스트 후 정리
        if hasattr(adapter, 'event_bus'):
            adapter.event_bus.reset()
            adapter.cleanup()

    def test_adapter_initialization(self, adapter, mock_manager):
        """어댑터 초기화 테스트"""
        assert adapter.workflow_manager == mock_manager
        assert hasattr(adapter, 'event_bus')
        assert adapter.event_bus is not None

    def test_add_listener_api(self, adapter):
        """add_listener API 테스트"""
        received_events = []

        def handler(event):
            received_events.append(event)

        # 새로운 API 사용
        adapter.add_listener("task_started", handler)

        # 이벤트 발행
        mock_task = Mock(id="task-1", title="테스트", status="in_progress")
        mock_plan = Mock(id="plan-1", name="플랜")

        adapter.publish_task_started(mock_task, mock_plan)

        time.sleep(0.1)

        assert len(received_events) > 0

    def test_workflow_listener(self, adapter):
        """add_workflow_listener API 테스트"""
        # BaseEventListener를 구현한 리스너
        listener = TestEventListener()

        # 리스너 추가
        adapter.add_workflow_listener(listener)

        # 다양한 이벤트 발행
        mock_plan = Mock(id="plan-1", name="테스트 플랜")
        mock_task = Mock(id="task-1", title="테스트 작업", status="todo")

        adapter.publish_plan_created(mock_plan)
        adapter.publish_task_added(mock_task, mock_plan)
        adapter.publish_task_started(mock_task, mock_plan)

        time.sleep(0.2)

        # 검증
        assert len(listener.events_received) >= 3

        # 받은 이벤트가 WorkflowEvent 타입인지 확인
        for event in listener.events_received:
            assert isinstance(event, WorkflowEvent)
            assert hasattr(event, 'type')
            assert hasattr(event, 'plan_id')

    def test_publish_workflow_event(self, adapter):
        """WorkflowEvent 직접 발행 테스트"""
        received_events = []

        def handler(event):
            received_events.append(event)

        adapter.add_listener("task_completed", handler)

        # WorkflowEvent 생성
        workflow_event = WorkflowEvent(
            type=EventType.TASK_COMPLETED,
            plan_id="plan-123",
            task_id="task-456",
            user="test-user",
            details={"notes": "작업 완료!"}
        )

        # 발행
        adapter.publish_workflow_event(workflow_event)

        time.sleep(0.1)

        assert len(received_events) > 0
        # Event 타입으로 변환되어 전달
        assert hasattr(received_events[0], 'data')
        assert received_events[0].data.get('task_id') == "task-456"

    def test_event_bus_reset(self, adapter):
        """EventBus reset 테스트"""
        # 핸들러 추가
        def handler(event):
            pass

        adapter.add_listener("test_event", handler)

        # reset
        adapter.event_bus.reset()

        # reset 후에도 정상 작동하는지 확인
        adapter.event_bus.start()

        received = []
        adapter.add_listener("test_event2", lambda e: received.append(e))

        # 이벤트 발행
        test_event = Event()
        test_event.type = "test_event2"
        adapter.event_bus.publish(test_event)

        time.sleep(0.1)

        assert len(received) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
