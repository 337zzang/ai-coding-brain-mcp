"""
Event System Integration Example
이벤트 시스템을 실제로 사용하는 예제
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from events.event_bus import get_event_bus, subscribe_to
from events.event_types import EventTypes, TaskEvent, FileEvent, create_task_started_event
from events.workflow_context_bridge import get_workflow_context_bridge
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 이벤트 핸들러 예제
@subscribe_to(EventTypes.WORKFLOW_TASK_STARTED)
def on_task_started(event):
    """태스크 시작 시 로깅"""
    logger.info(f"📋 Task started: {event.data.get('task_title')}")


@subscribe_to(EventTypes.FILE_ACCESSED)
def on_file_accessed(event):
    """파일 접근 시 로깅"""
    task_id = event.data.get('task_id')
    file_path = event.data.get('file_path')
    if task_id:
        logger.info(f"📁 File accessed during task {task_id}: {file_path}")
    else:
        logger.info(f"📁 File accessed: {file_path}")


@subscribe_to(EventTypes.CONTEXT_UPDATED)
def on_context_updated(event):
    """컨텍스트 업데이트 시 처리"""
    update_type = event.data.get('update_type')
    logger.info(f"🔄 Context updated: {update_type}")


def simulate_workflow_execution():
    """워크플로우 실행 시뮬레이션"""
    print("\n=== 워크플로우 실행 시뮬레이션 ===\n")

    # 이벤트 버스와 브릿지 초기화
    bus = get_event_bus()
    bridge = get_workflow_context_bridge()

    # 1. 태스크 시작
    task_event = create_task_started_event("task_001", "데이터 분석 태스크")
    bus.publish(task_event)

    # 2. 파일 작업들 (현재 태스크와 자동 연결)
    files = ["data.csv", "analysis.py", "results.json"]
    for file_path in files:
        file_event = FileEvent(
            EventTypes.FILE_ACCESSED,
            file_path=file_path,
            operation="read"
        )
        bus.publish(file_event)

    # 3. 새 파일 생성
    create_event = FileEvent(
        EventTypes.FILE_CREATED,
        file_path="report.md",
        operation="create"
    )
    bus.publish(create_event)

    # 4. 태스크 완료
    complete_event = TaskEvent(
        EventTypes.WORKFLOW_TASK_COMPLETED,
        task_id="task_001",
        task_title="데이터 분석 태스크",
        status="COMPLETED",
        completion_notes="분석 완료, 보고서 생성됨"
    )
    bus.publish(complete_event)

    # 5. 이벤트 히스토리 확인
    print("\n=== 이벤트 히스토리 ===")
    history = bus.get_history(limit=10)
    print(f"총 {len(history)}개 이벤트 발생")

    for event in history[-5:]:  # 최근 5개
        print(f"  - {event.type} at {event.timestamp}")


def demonstrate_decoupled_modules():
    """모듈 간 느슨한 결합 데모"""
    print("\n=== 느슨한 결합 데모 ===\n")

    bus = get_event_bus()

    # WorkflowManager 역할 (실제로는 별도 모듈)
    class MockWorkflowManager:
        def start_task(self, task_id, title):
            # 직접 ContextManager를 호출하지 않고 이벤트만 발행
            event = create_task_started_event(task_id, title)
            bus.publish(event)
            print(f"WorkflowManager: Published task start event")

    # ContextManager 역할 (실제로는 별도 모듈)
    class MockContextManager:
        def __init__(self):
            # WorkflowManager를 import하지 않고 이벤트만 구독
            bus.subscribe(EventTypes.WORKFLOW_TASK_STARTED, self.on_task_started)

        def on_task_started(self, event):
            print(f"ContextManager: Received task start - {event.data.get('task_title')}")
            # 컨텍스트 업데이트 로직...

    # 사용 예
    wf_manager = MockWorkflowManager()
    ctx_manager = MockContextManager()

    # WorkflowManager가 태스크 시작 (ContextManager를 직접 호출하지 않음)
    wf_manager.start_task("task_002", "리팩토링 태스크")

    print("\n✅ 모듈들이 이벤트를 통해 통신 - 직접적인 의존성 없음!")


if __name__ == "__main__":
    # 워크플로우 시뮬레이션
    simulate_workflow_execution()

    # 느슨한 결합 데모
    demonstrate_decoupled_modules()

    print("\n🎉 이벤트 시스템 통합 예제 완료!")
