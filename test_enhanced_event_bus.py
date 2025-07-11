"""
Enhanced EventBus 테스트
"""
import asyncio
import time
from python.events.enhanced_event_bus import EnhancedEventBus, EventPriority


async def test_enhanced_event_bus():
    """개선된 EventBus 테스트"""
    print("🧪 Enhanced EventBus 테스트 시작...")

    # EventBus 생성
    bus = EnhancedEventBus(max_workers=3, max_retries=2)

    # 테스트 핸들러
    processed_events = []

    def test_handler(data):
        processed_events.append(data)
        print(f"   처리됨: {data.get('message')} (우선순위: {data.get('priority')})")

        # 일부러 에러 발생
        if data.get('fail'):
            raise Exception("의도적 실패")

    # 구독
    bus.subscribe("test_event", test_handler)

    # EventBus 시작
    await bus.start()

    # 다양한 우선순위로 이벤트 발행
    print("\n📤 이벤트 발행:")
    bus.publish("test_event", {"message": "일반 이벤트", "priority": "normal"}, EventPriority.NORMAL)
    bus.publish("test_event", {"message": "중요 이벤트", "priority": "critical"}, EventPriority.CRITICAL)
    bus.publish("test_event", {"message": "낮은 우선순위", "priority": "low"}, EventPriority.LOW)
    bus.publish("test_event", {"message": "실패할 이벤트", "priority": "high", "fail": True}, EventPriority.HIGH)

    # 처리 대기
    await asyncio.sleep(2)

    # 메트릭 확인
    print("\n📊 메트릭:")
    metrics = bus.get_metrics()
    print(f"   처리된 이벤트: {metrics['stats']['processed']}")
    print(f"   실패한 이벤트: {metrics['stats']['failed']}")
    print(f"   데드레터 큐: {metrics['dead_letter_count']}개")

    # 데드레터 확인
    if metrics['dead_letter_count'] > 0:
        print("\n💀 데드레터 큐:")
        for dl in bus.get_dead_letters():
            print(f"   - {dl['event'].event_type}: {dl['error']}")

    # 종료
    await bus.stop()

    print("\n✅ 테스트 완료!")
    print(f"   처리된 이벤트 수: {len(processed_events)}")

    # 우선순위 순서 확인
    if len(processed_events) >= 2:
        first = processed_events[0].get('priority')
        print(f"   첫 번째 처리된 이벤트: {first} (critical이어야 함)")


if __name__ == "__main__":
    asyncio.run(test_enhanced_event_bus())
