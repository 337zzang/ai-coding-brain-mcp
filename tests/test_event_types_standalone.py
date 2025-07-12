"""
Event Types 독립 테스트
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid
import time

# EventType enum 정의 (unified_event_types.py에서)
class EventType(str, Enum):
    # 플랜 관련 이벤트
    PLAN_CREATED = "plan_created"
    PLAN_STARTED = "plan_started"
    PLAN_COMPLETED = "plan_completed"
    PLAN_ARCHIVED = "plan_archived"
    PLAN_UPDATED = "plan_updated"

    # 태스크 관련 이벤트
    TASK_ADDED = "task_added"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_UPDATED = "task_updated"

    # 컨텍스트 관련 이벤트
    CONTEXT_UPDATED = "context_updated"
    CONTEXT_SAVED = "context_saved"

    # 프로젝트 관련 이벤트
    PROJECT_SWITCHED = "project_switched"
    PROJECT_LOADED = "project_loaded"

    # 시스템 이벤트
    SYSTEM_ERROR = "system_error"
    SYSTEM_WARNING = "system_warning"
    SYSTEM_INFO = "system_info"

# event_bus.py와 event_types.py 내용 실행
exec(open("python/workflow/v3/event_bus.py").read())

# Event 클래스가 정의된 후 event_types.py 실행
# (EventType은 위에서 정의했으므로 import 부분 제외)
event_types_content = open("python/workflow/v3/event_types.py").read()
# import 문 제거
lines = event_types_content.split('\n')
filtered_lines = []
for line in lines:
    if not line.strip().startswith('from python.events.unified_event_types'):
        filtered_lines.append(line)
exec('\n'.join(filtered_lines))

def test():
    print("="*50)
    print("Event Types 통합 테스트")
    print("="*50)

    # 1. 기존 EventType 활용
    print("\n1. EventType 열거형 확인")
    print(f"   총 {len(EventType)} 개의 이벤트 타입 정의됨")
    print(f"   예시: {EventType.PLAN_CREATED.value}, {EventType.TASK_COMPLETED.value}")

    # 2. 이벤트 생성
    print("\n2. 다양한 이벤트 생성")

    # PlanEvent
    plan_event = PlanEvent(
        type=EventType.PLAN_CREATED.value,
        plan_id="plan-001",
        plan_name="이벤트 시스템 개편",
        project_name="ai-coding-brain-mcp"
    )
    print(f"   ✅ PlanEvent: {plan_event.type}")

    # TaskEvent
    task_event = TaskEvent(
        type=EventType.TASK_COMPLETED.value,
        task_id="task-001",
        task_title="EventBus 구현",
        task_status="completed"
    )
    print(f"   ✅ TaskEvent: {task_event.type}")

    # CommandEvent
    cmd_event = CommandEvent(
        type="command_executed",
        command="/next",
        success=True
    )
    print(f"   ✅ CommandEvent: {cmd_event.command}")

    # 3. EventBus 통합
    print("\n3. EventBus와 통합 테스트")
    bus = EventBus()

    received = []
    def handler(event):
        received.append(event)
        event_info = f"{event.type}"
        if hasattr(event, 'plan_name'):
            event_info += f" - {event.plan_name}"
        elif hasattr(event, 'task_title'):
            event_info += f" - {event.task_title}"
        print(f"   📨 이벤트 수신: {event_info}")

    # 구독
    bus.subscribe(EventType.PLAN_CREATED.value, handler)
    bus.subscribe(EventType.TASK_COMPLETED.value, handler)

    # 발행
    bus.publish(plan_event)
    bus.publish(task_event)

    time.sleep(0.5)

    print(f"\n   수신된 이벤트: {len(received)}개")
    print(f"   통계: {bus.get_stats()}")

    # 4. 헬퍼 함수 테스트
    print("\n4. 헬퍼 함수 테스트")

    plan = create_plan_event(
        EventType.PLAN_CREATED,
        plan_id="plan-002",
        plan_name="테스트 플랜"
    )
    print(f"   create_plan_event: {plan.type} - {plan.plan_name}")

    task = create_task_event(
        EventType.TASK_ADDED,
        task_id="task-002",
        task_title="새 태스크"
    )
    print(f"   create_task_event: {task.type} - {task.task_title}")

    sys_event = create_system_event(
        "info",
        "시스템 메시지",
        component="test"
    )
    print(f"   create_system_event: {sys_event.type} - {sys_event.message}")

    bus.stop()
    print("\n✅ 모든 테스트 완료!")

if __name__ == "__main__":
    test()
