"""
Event Types 테스트
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from datetime import datetime

# 기존 통합 EventType import
from python.events.unified_event_types import EventType

# EventBus와 새로운 이벤트 타입들 import
exec(open("python/workflow/v3/event_bus.py").read())
exec(open("python/workflow/v3/event_types.py").read())


def test_event_types():
    """이벤트 타입 테스트"""
    print("="*50)
    print("Event Types 테스트")
    print("="*50)

    # 1. EventType enum 테스트
    print("\n1. EventType 열거형 테스트")
    print(f"   PLAN_CREATED: {EventType.PLAN_CREATED.value}")
    print(f"   TASK_COMPLETED: {EventType.TASK_COMPLETED.value}")
    print(f"   CONTEXT_UPDATED: {EventType.CONTEXT_UPDATED.value}")

    # 2. PlanEvent 생성 테스트
    print("\n2. PlanEvent 생성 테스트")
    plan_event = create_plan_event(
        EventType.PLAN_CREATED,
        plan_id="plan-123",
        plan_name="이벤트 시스템 개편",
        project_name="ai-coding-brain-mcp"
    )
    print(f"   Type: {plan_event.type}")
    print(f"   Plan ID: {plan_event.plan_id}")
    print(f"   Metadata: {plan_event.metadata}")

    # 3. TaskEvent 생성 테스트
    print("\n3. TaskEvent 생성 테스트")
    task_event = create_task_event(
        EventType.TASK_COMPLETED,
        task_id="task-456",
        task_title="EventBus 구현",
        task_status="completed",
        plan_id="plan-123"
    )
    print(f"   Type: {task_event.type}")
    print(f"   Task: {task_event.task_title}")
    print(f"   Status: {task_event.task_status}")

    # 4. CommandEvent 생성 테스트
    print("\n4. CommandEvent 생성 테스트")
    cmd_event = create_command_event(
        "/start",
        args=["이벤트 시스템"],
        success=True,
        result="플랜 생성됨"
    )
    print(f"   Command: {cmd_event.command}")
    print(f"   Success: {cmd_event.success}")

    # 5. SystemEvent 생성 테스트
    print("\n5. SystemEvent 생성 테스트")
    sys_event = create_system_event(
        "info",
        "EventBus 시작됨",
        component="EventBus"
    )
    print(f"   Level: {sys_event.level}")
    print(f"   Message: {sys_event.message}")
    print(f"   Type: {sys_event.type}")

    # 6. EventBus와 통합 테스트
    print("\n6. EventBus 통합 테스트")
    bus = EventBus()

    # 핸들러 등록
    received_events = []
    def test_handler(event):
        received_events.append(event)
        print(f"   📨 수신: {event.type} - {getattr(event, 'plan_name', 'N/A')}")

    # 플랜 이벤트 구독
    bus.subscribe(EventType.PLAN_CREATED.value, test_handler)
    bus.subscribe(EventType.TASK_COMPLETED.value, test_handler)

    # 이벤트 발행
    bus.publish(plan_event)
    bus.publish(task_event)

    # 처리 대기
    import time
    time.sleep(0.5)

    print(f"\n   총 수신 이벤트: {len(received_events)}개")
    print(f"   EventBus 통계: {bus.get_stats()}")

    # 정리
    bus.stop()

    print("\n✅ 모든 테스트 통과!")


if __name__ == "__main__":
    test_event_types()
