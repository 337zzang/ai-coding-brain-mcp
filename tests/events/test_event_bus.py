"""
Event Bus Test
이벤트 버스 기능 테스트
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'python'))

from events.event_bus import get_event_bus, Event, EventPriority, subscribe_to
from events.event_types import (
    EventTypes, TaskEvent, FileEvent, 
    create_task_started_event, create_task_completed_event
)
from events.workflow_context_bridge import get_workflow_context_bridge


def test_basic_event_bus():
    """기본 이벤트 버스 테스트"""
    print("=== 기본 이벤트 버스 테스트 ===")

    # 이벤트 버스 가져오기
    bus = get_event_bus()

    # 테스트용 핸들러
    results = []

    def test_handler(event: Event):
        results.append(f"Received: {event.type}")
        print(f"✓ Handler called: {event.type}")

    # 핸들러 구독
    bus.subscribe("test.event", test_handler)

    # 이벤트 발행
    test_event = Event(type="test.event", data={"message": "Hello"})
    bus.publish(test_event)

    assert len(results) == 1, "Handler should be called once"
    print("✅ 기본 이벤트 발행/구독 테스트 통과\n")


def test_priority_handling():
    """우선순위 처리 테스트"""
    print("=== 우선순위 처리 테스트 ===")

    bus = get_event_bus()
    results = []

    def high_priority_handler(event):
        results.append("HIGH")

    def normal_priority_handler(event):
        results.append("NORMAL")

    def low_priority_handler(event):
        results.append("LOW")

    # 다양한 우선순위로 구독
    bus.subscribe("priority.test", low_priority_handler, EventPriority.LOW)
    bus.subscribe("priority.test", high_priority_handler, EventPriority.HIGH)
    bus.subscribe("priority.test", normal_priority_handler, EventPriority.NORMAL)

    # 이벤트 발행
    bus.publish(Event(type="priority.test"))

    # 우선순위 순서 확인
    assert results == ["HIGH", "NORMAL", "LOW"], f"Expected order: HIGH, NORMAL, LOW. Got: {results}"
    print("✅ 우선순위 처리 테스트 통과\n")


def test_workflow_context_bridge():
    """워크플로우-컨텍스트 브릿지 테스트"""
    print("=== 워크플로우-컨텍스트 브릿지 테스트 ===")

    # 브릿지 초기화
    bridge = get_workflow_context_bridge()
    bus = get_event_bus()

    # 컨텍스트 업데이트 추적
    context_updates = []

    def track_context_updates(event: Event):
        context_updates.append(event.data)
        print(f"✓ Context update: {event.data.get('update_type')}")

    bus.subscribe(EventTypes.CONTEXT_UPDATED, track_context_updates)

    # 태스크 시작 이벤트
    task_start = create_task_started_event("task_123", "테스트 태스크")
    bus.publish(task_start)

    # 현재 태스크 ID 확인
    assert bridge.current_task_id == "task_123", "Current task ID should be set"

    # 파일 접근 이벤트 (현재 태스크와 자동 연결)
    file_event = FileEvent(
        EventTypes.FILE_ACCESSED,
        file_path="test.py",
        operation="read"
    )
    bus.publish(file_event)

    # 태스크 완료 이벤트
    task_complete = create_task_completed_event("task_123", "테스트 태스크", "완료됨")
    bus.publish(task_complete)

    # 컨텍스트 업데이트 확인
    assert len(context_updates) >= 3, f"Expected at least 3 context updates, got {len(context_updates)}"
    print(f"✓ Total context updates: {len(context_updates)}")
    print("✅ 워크플로우-컨텍스트 브릿지 테스트 통과\n")


def test_event_history():
    """이벤트 히스토리 테스트"""
    print("=== 이벤트 히스토리 테스트 ===")

    bus = get_event_bus()

    # 여러 이벤트 발행
    for i in range(5):
        bus.publish(Event(type="history.test", data={"index": i}))

    # 히스토리 조회
    history = bus.get_history("history.test")
    assert len(history) == 5, f"Expected 5 events in history, got {len(history)}"

    # 최신 이벤트가 마지막에 있는지 확인
    assert history[-1].data["index"] == 4, "Latest event should be last"

    print("✅ 이벤트 히스토리 테스트 통과\n")


if __name__ == "__main__":
    print("🧪 이벤트 시스템 테스트 시작\n")

    try:
        test_basic_event_bus()
        test_priority_handling()
        test_workflow_context_bridge()
        test_event_history()

        print("✅ 모든 테스트 통과!")

    except AssertionError as e:
        print(f"❌ 테스트 실패: {e}")
    except Exception as e:
        print(f"❌ 예외 발생: {e}")
        import traceback
        traceback.print_exc()
