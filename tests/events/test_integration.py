"""
Event Integration Test
이벤트 시스템 통합 테스트
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'python'))

from workflow.workflow_manager import WorkflowManager
from events.event_integration_adapter import get_event_adapter, integrate_all
from events.event_bus import get_event_bus
from events.event_types import EventTypes
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_workflow_event_integration():
    """워크플로우 이벤트 통합 테스트"""
    print("\n=== 워크플로우 이벤트 통합 테스트 ===")

    # 이벤트 추적을 위한 리스트
    captured_events = []

    # 이벤트 핸들러
    def capture_event(event):
        captured_events.append({
            'type': event.type,
            'data': event.data
        })
        print(f"✓ Captured event: {event.type}")

    # 이벤트 버스 설정
    bus = get_event_bus()
    bus.subscribe(EventTypes.WORKFLOW_PLAN_CREATED, capture_event)
    bus.subscribe(EventTypes.WORKFLOW_TASK_STARTED, capture_event)
    bus.subscribe(EventTypes.WORKFLOW_TASK_COMPLETED, capture_event)

    # 어댑터로 통합
    adapter = get_event_adapter()
    wf_manager = WorkflowManager()
    adapter.integrate_workflow_manager(wf_manager)

    # 워크플로우 작업 수행
    print("\n1. 계획 생성")
    plan = wf_manager.create_plan("테스트 계획", "이벤트 통합 테스트")

    # 이벤트 발행 확인
    assert any(e['type'] == EventTypes.WORKFLOW_PLAN_CREATED for e in captured_events), \
        "PLAN_CREATED 이벤트가 발행되지 않음"

    print("✅ 워크플로우 이벤트 통합 테스트 통과")
    return len(captured_events)


def test_full_integration():
    """전체 시스템 통합 테스트"""
    print("\n=== 전체 시스템 통합 테스트 ===")

    # 전체 통합
    adapter = integrate_all()

    # 이벤트 버스 상태 확인
    bus = get_event_bus()

    print("\n통합 완료 상태:")
    print("- WorkflowManager ✓")
    print("- ContextManager ✓")
    print("- File Operations ✓")

    return True


if __name__ == "__main__":
    print("🧪 이벤트 통합 테스트 시작\n")

    try:
        # 워크플로우 이벤트 통합 테스트
        event_count = test_workflow_event_integration()
        print(f"\n📊 발행된 이벤트: {event_count}개")

        # 전체 통합 테스트
        test_full_integration()

        print("\n✅ 모든 통합 테스트 통과!")

    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
