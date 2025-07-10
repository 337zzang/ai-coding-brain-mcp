"""
EventBus 단위 테스트
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import time
import threading
from python.workflow.v3.event_bus import EventBus, Event, event_bus


def test_singleton_pattern():
    """싱글톤 패턴 테스트"""
    print("1. 싱글톤 패턴 테스트")
    bus1 = EventBus()
    bus2 = EventBus()

    assert bus1 is bus2, "EventBus should be singleton"
    assert bus1 is event_bus, "Global instance should be the same"
    print("   ✅ 싱글톤 패턴 정상 작동")


def test_pub_sub():
    """발행/구독 메커니즘 테스트"""
    print("\n2. 발행/구독 메커니즘 테스트")

    # 테스트용 이벤트 수신 기록
    received_events = []

    def test_handler(event: Event):
        received_events.append(event)
        print(f"   📨 이벤트 수신: {event.type} - {event.payload}")

    # 핸들러 등록
    event_bus.subscribe("test_event", test_handler)

    # 이벤트 발행
    test_event = Event(
        type="test_event",
        payload={"message": "Hello EventBus!"}
    )
    event_bus.publish(test_event)

    # 비동기 처리를 위해 잠시 대기
    time.sleep(0.5)

    # 검증
    assert len(received_events) == 1, "Should receive one event"
    assert received_events[0].type == "test_event"
    print("   ✅ 발행/구독 정상 작동")

    # 핸들러 제거
    event_bus.unsubscribe("test_event", test_handler)


def test_multiple_handlers():
    """다중 핸들러 테스트"""
    print("\n3. 다중 핸들러 테스트")

    counter = {"value": 0}
    lock = threading.Lock()

    def handler1(event: Event):
        with lock:
            counter["value"] += 1
        print(f"   Handler1 처리: {event.type}")

    def handler2(event: Event):
        with lock:
            counter["value"] += 10
        print(f"   Handler2 처리: {event.type}")

    # 여러 핸들러 등록
    event_bus.subscribe("multi_test", handler1)
    event_bus.subscribe("multi_test", handler2)

    # 이벤트 발행
    event = Event(type="multi_test", payload={"test": True})
    event_bus.publish(event)

    time.sleep(0.5)

    # 검증
    assert counter["value"] == 11, f"Expected 11, got {counter['value']}"
    print("   ✅ 다중 핸들러 정상 작동")

    # 정리
    event_bus.clear_handlers("multi_test")


def test_error_handling():
    """에러 처리 및 재시도 테스트"""
    print("\n4. 에러 처리 테스트")

    attempt_count = {"value": 0}

    def failing_handler(event: Event):
        attempt_count["value"] += 1
        print(f"   시도 #{attempt_count['value']}")

        if attempt_count["value"] < 3:
            raise Exception("Simulated error")

        print("   성공!")

    # 실패하는 핸들러 등록
    event_bus.subscribe("error_test", failing_handler)

    # 이벤트 발행
    event = Event(type="error_test", payload={"will_fail": True})
    event_bus.publish(event)

    # 재시도를 위한 충분한 시간 대기
    time.sleep(5)

    # 검증 (재시도 포함)
    assert attempt_count["value"] >= 3, "Should retry multiple times"
    print("   ✅ 에러 처리 및 재시도 정상 작동")

    # 정리
    event_bus.clear_handlers("error_test")


def test_stats():
    """통계 기능 테스트"""
    print("\n5. 통계 기능 테스트")

    stats = event_bus.get_stats()
    print(f"   현재 통계: {stats}")

    assert "published" in stats
    assert "processed" in stats
    assert "failed" in stats
    print("   ✅ 통계 기능 정상 작동")


def run_all_tests():
    """모든 테스트 실행"""
    print("="*50)
    print("EventBus 단위 테스트 시작")
    print("="*50)

    try:
        test_singleton_pattern()
        test_pub_sub()
        test_multiple_handlers()
        test_error_handling()
        test_stats()

        print("\n" + "="*50)
        print("✅ 모든 테스트 통과!")
        print("="*50)

        # 최종 통계
        final_stats = event_bus.get_stats()
        print(f"\n최종 통계: {final_stats}")

    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
