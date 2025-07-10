"""
EventBus와 EventTypes 최종 통합 테스트
"""

import time

# 독립적으로 실행
exec(open("python/workflow/v3/event_bus.py").read())
exec(open("python/workflow/v3/event_types.py").read())

print("="*50)
print("EventBus + EventTypes 통합 테스트")
print("="*50)

# 1. EventBus 인스턴스
bus = EventBus()
print(f"\n1. EventBus 준비: {bus._running}")

# 2. 이벤트 생성 (기존 EventType 활용)
print("\n2. 이벤트 생성 (기존 타입 활용)")

events = [
    create_plan_event(EventType.PLAN_CREATED, plan_id="p1", plan_name="테스트 플랜"),
    create_task_event(EventType.TASK_ADDED, task_id="t1", task_title="태스크 1"),
    create_task_event(EventType.TASK_COMPLETED, task_id="t1", task_title="태스크 1"),
    create_context_event(EventType.CONTEXT_UPDATED, context_type="workflow"),
    create_command_event("/start", args=["플랜명"], success=True),
    create_system_event("info", "시스템 시작됨")
]

for event in events:
    print(f"   ✅ {event.__class__.__name__}: {event.type}")

# 3. 발행/구독 테스트
print("\n3. 발행/구독 테스트")

received_count = {"count": 0}

def universal_handler(event):
    received_count["count"] += 1
    info = f"{event.type}"
    if hasattr(event, 'plan_name'):
        info += f" - {event.plan_name}"
    elif hasattr(event, 'task_title'):
        info += f" - {event.task_title}"
    elif hasattr(event, 'command'):
        info += f" - {event.command}"
    print(f"   📨 수신: {info}")

# 모든 이벤트 타입 구독
for event in events:
    bus.subscribe(event.type, universal_handler)

# 이벤트 발행
for event in events:
    bus.publish(event)

# 처리 대기
time.sleep(1)

print(f"\n4. 결과")
print(f"   발행된 이벤트: {len(events)}개")
print(f"   수신된 이벤트: {received_count['count']}개")
print(f"   EventBus 통계: {bus.get_stats()}")

bus.stop()
print("\n✅ 통합 테스트 완료!")
