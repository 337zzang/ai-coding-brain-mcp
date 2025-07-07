"""
Performance Tests
이벤트 시스템 성능 테스트
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'python'))

import time
import statistics
from events.event_bus import get_event_bus, Event, EventPriority
from events.event_types import EventTypes, create_task_started_event
import threading


def test_event_throughput():
    """이벤트 처리량 테스트"""
    print("\n=== 이벤트 처리량 테스트 ===")

    bus = get_event_bus()

    # 처리된 이벤트 카운터
    processed_count = {'count': 0}

    def counter_handler(event):
        processed_count['count'] += 1

    # 핸들러 등록
    bus.subscribe("performance.test", counter_handler)

    # 테스트 실행
    num_events = 10000
    start_time = time.time()

    print(f"발행할 이벤트: {num_events:,}개")

    for i in range(num_events):
        event = Event(type="performance.test", data={'index': i})
        bus.publish(event)

    end_time = time.time()
    duration = end_time - start_time

    # 결과 계산
    events_per_second = num_events / duration

    print(f"\n📊 결과:")
    print(f"  - 처리 시간: {duration:.3f}초")
    print(f"  - 처리된 이벤트: {processed_count['count']:,}개")
    print(f"  - 처리량: {events_per_second:,.0f} events/sec")

    return events_per_second


def test_handler_latency():
    """핸들러 지연 시간 테스트"""
    print("\n=== 핸들러 지연 시간 테스트 ===")

    bus = get_event_bus()
    latencies = []

    def latency_handler(event):
        # 이벤트 생성 시간과 현재 시간 차이 계산
        created_time = event.data.get('created_time')
        if created_time:
            latency = (time.time() - created_time) * 1000  # ms
            latencies.append(latency)

    # 핸들러 등록
    bus.subscribe("latency.test", latency_handler)

    # 테스트 실행
    num_tests = 1000

    for i in range(num_tests):
        event = Event(
            type="latency.test",
            data={'created_time': time.time()}
        )
        bus.publish(event)

    # 통계 계산
    if latencies:
        avg_latency = statistics.mean(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]

        print(f"\n📊 지연 시간 통계 ({num_tests}개 이벤트):")
        print(f"  - 평균: {avg_latency:.3f}ms")
        print(f"  - 최소: {min_latency:.3f}ms")
        print(f"  - 최대: {max_latency:.3f}ms")
        print(f"  - P95: {p95_latency:.3f}ms")

    return avg_latency


def test_priority_performance():
    """우선순위별 처리 성능 테스트"""
    print("\n=== 우선순위별 처리 성능 테스트 ===")

    bus = get_event_bus()
    priority_times = {
        EventPriority.CRITICAL: [],
        EventPriority.HIGH: [],
        EventPriority.NORMAL: [],
        EventPriority.LOW: []
    }

    def priority_handler(event):
        process_time = time.time() - event.data['start_time']
        priority = event.priority
        priority_times[priority].append(process_time * 1000)

    # 각 우선순위별로 핸들러 등록
    for priority in EventPriority:
        bus.subscribe("priority.perf", priority_handler, priority)

    # 다양한 우선순위로 이벤트 발행
    for priority in EventPriority:
        for i in range(100):
            event = Event(
                type="priority.perf",
                data={'start_time': time.time()},
                priority=priority
            )
            bus.publish(event)

    # 결과 분석
    print("\n📊 우선순위별 평균 처리 시간:")
    for priority, times in priority_times.items():
        if times:
            avg_time = statistics.mean(times)
            print(f"  - {priority.name}: {avg_time:.3f}ms")

    return True


def test_memory_usage():
    """메모리 사용량 테스트"""
    print("\n=== 메모리 사용량 테스트 ===")

    import psutil
    import gc

    process = psutil.Process()

    # 초기 메모리 사용량
    gc.collect()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    bus = get_event_bus()

    # 많은 수의 핸들러 등록
    handlers = []
    for i in range(1000):
        def make_handler(index):
            def handler(event):
                pass
            return handler

        handler = make_handler(i)
        handlers.append(handler)
        bus.subscribe(f"memory.test.{i}", handler)

    # 많은 이벤트 발행
    for i in range(10000):
        event = Event(
            type=f"memory.test.{i % 1000}",
            data={'large_data': 'x' * 1000}
        )
        bus.publish(event)

    # 최종 메모리 사용량
    gc.collect()
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory

    print(f"\n📊 메모리 사용량:")
    print(f"  - 초기: {initial_memory:.1f} MB")
    print(f"  - 최종: {final_memory:.1f} MB")
    print(f"  - 증가: {memory_increase:.1f} MB")

    # 정리
    bus.clear_handlers()
    handlers.clear()
    gc.collect()

    return memory_increase


if __name__ == "__main__":
    print("⚡ 이벤트 시스템 성능 테스트\n")

    try:
        # 각 성능 테스트 실행
        throughput = test_event_throughput()
        latency = test_handler_latency()
        test_priority_performance()
        memory = test_memory_usage()

        # 성능 요약
        print("\n\n📊 성능 테스트 요약:")
        print(f"  - 처리량: {throughput:,.0f} events/sec")
        print(f"  - 평균 지연: {latency:.3f}ms")
        print(f"  - 메모리 증가: {memory:.1f} MB")

        # 성능 평가
        if throughput > 50000 and latency < 1.0:
            print("\n✅ 우수한 성능!")
        elif throughput > 10000 and latency < 5.0:
            print("\n✅ 양호한 성능")
        else:
            print("\n⚠️ 성능 개선 필요")

    except Exception as e:
        print(f"\n❌ 성능 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
