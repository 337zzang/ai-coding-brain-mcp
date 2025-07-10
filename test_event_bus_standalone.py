"""
EventBus 독립 테스트 (의존성 없음)
"""

import sys
import os
import time
import threading

# event_bus.py 내용을 직접 실행
exec(open("python/workflow/v3/event_bus.py").read())

def test_basic_functionality():
    """기본 기능 테스트"""
    print("="*50)
    print("EventBus 독립 테스트")
    print("="*50)

    # 1. 인스턴스 생성
    print("\n1. EventBus 인스턴스 테스트")
    bus = EventBus()
    print(f"   EventBus 생성: {bus}")
    print(f"   실행 중: {bus._running}")

    # 2. 이벤트 생성
    print("\n2. Event 객체 생성 테스트")
    event = Event(
        type="test_event",
        payload={"message": "Hello World"}
    )
    print(f"   Event ID: {event.id}")
    print(f"   Event Type: {event.type}")
    print(f"   Event Payload: {event.payload}")

    # 3. 핸들러 등록 및 이벤트 발행
    print("\n3. 발행/구독 테스트")
    received = []

    def handler(e):
        received.append(e)
        print(f"   ✅ 이벤트 수신: {e.type} - {e.payload}")

    bus.subscribe("test_event", handler)
    print(f"   핸들러 등록 완료")

    # 이벤트 발행
    bus.publish(event)
    print(f"   이벤트 발행 완료")

    # 비동기 처리 대기
    time.sleep(1)

    # 결과 확인
    print(f"\n4. 결과 확인")
    print(f"   수신된 이벤트 수: {len(received)}")
    print(f"   통계: {bus.get_stats()}")

    if len(received) > 0:
        print("\n✅ EventBus 기본 기능 정상 작동!")
    else:
        print("\n❌ EventBus 테스트 실패")

    # 정리
    bus.stop()
    print("\nEventBus 종료")

if __name__ == "__main__":
    test_basic_functionality()
