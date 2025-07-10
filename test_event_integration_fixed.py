"""
Event-Based Architecture Integration Test (Fixed)
"""

import time
from datetime import datetime

# 필요한 모듈들 로드
exec(open("python/workflow/v3/event_bus.py").read())
exec(open("python/workflow/v3/event_types.py").read())

# 테스트용 Mock 클래스들
class MockContextManager:
    def __init__(self):
        self.current_project = None
        self.events_received = []
        self._register_handlers()

    def _register_handlers(self):
        event_bus.subscribe(EventType.PLAN_CREATED.value, self._on_event)
        event_bus.subscribe(EventType.TASK_COMPLETED.value, self._on_event)
        event_bus.subscribe(EventType.PROJECT_LOADED.value, self._on_event)

    def _on_event(self, event):
        self.events_received.append({
            'type': event.type,
            'timestamp': event.timestamp,
            'data': getattr(event, 'payload', {})
        })
        print(f"   ContextManager received: {event.type}")

    def switch_project(self, project_name):
        previous = self.current_project
        self.current_project = project_name

        # PROJECT_SWITCHED 이벤트 발행
        event = create_project_event(
            EventType.PROJECT_SWITCHED,
            project_name=project_name,
            previous_project=previous
        )
        event_bus.publish(event)
        print(f"   ContextManager: Switched {previous} -> {project_name}")


class MockWorkflowManager:
    def __init__(self, project_name):
        self.project_name = project_name
        self.events_received = []
        self.current_plan = None
        self._register_handlers()

    def _register_handlers(self):
        event_bus.subscribe(EventType.PROJECT_SWITCHED.value, self._on_project_switched)

    def _on_project_switched(self, event):
        self.events_received.append(event)
        print(f"   WorkflowManager received: PROJECT_SWITCHED -> {event.project_name}")

        # PROJECT_LOADED 이벤트 발행 (수정됨)
        loaded_event = ProjectEvent(
            type=EventType.PROJECT_LOADED.value,
            project_name=event.project_name,
            payload={'workflow_info': {'status': 'loaded'}}
        )
        event_bus.publish(loaded_event)

    def create_plan(self, name):
        self.current_plan = {'id': 'plan-1', 'name': name}

        # PLAN_CREATED 이벤트 발행
        event = create_plan_event(
            EventType.PLAN_CREATED,
            plan_id='plan-1',
            plan_name=name,
            project_name=self.project_name
        )
        event_bus.publish(event)
        print(f"   WorkflowManager: Created plan '{name}'")

    def complete_task(self, task_id, task_title):
        # TASK_COMPLETED 이벤트 발행
        event = create_task_event(
            EventType.TASK_COMPLETED,
            task_id=task_id,
            task_title=task_title,
            plan_id='plan-1',
            project_name=self.project_name
        )
        event_bus.publish(event)
        print(f"   WorkflowManager: Completed task '{task_title}'")


def test_event_based_communication():
    """이벤트 기반 통신 테스트"""
    print("="*60)
    print("Event-Based Communication Test")
    print("="*60)

    # EventBus 초기화
    event_bus.clear_handlers()

    # 1. 컴포넌트 생성
    print("\n1. 컴포넌트 초기화")
    context_mgr = MockContextManager()
    workflow_mgr = MockWorkflowManager("test-project")
    print("   ✅ ContextManager & WorkflowManager 생성")

    # 2. 프로젝트 전환 테스트
    print("\n2. 프로젝트 전환 (ContextManager -> WorkflowManager)")
    context_mgr.switch_project("new-project")

    # 이벤트 처리 대기
    time.sleep(0.5)

    # 검증
    assert len(workflow_mgr.events_received) > 0, "WorkflowManager should receive event"
    assert len(context_mgr.events_received) > 0, "ContextManager should receive PROJECT_LOADED"
    print("   ✅ 양방향 이벤트 통신 성공")

    # 3. 워크플로우 이벤트 테스트
    print("\n3. 워크플로우 작업 (WorkflowManager -> ContextManager)")
    workflow_mgr.create_plan("테스트 플랜")
    workflow_mgr.complete_task("task-1", "첫 번째 태스크")

    time.sleep(0.5)

    # 검증
    context_events = [e['type'] for e in context_mgr.events_received]
    assert EventType.PLAN_CREATED.value in context_events
    assert EventType.TASK_COMPLETED.value in context_events
    print("   ✅ 워크플로우 이벤트 전달 성공")

    # 4. 결과 요약
    print("\n4. 테스트 결과 요약")
    print(f"   ContextManager 수신 이벤트: {len(context_mgr.events_received)}개")
    print(f"   WorkflowManager 수신 이벤트: {len(workflow_mgr.events_received)}개")

    # EventBus 통계
    stats = event_bus.get_stats()
    print(f"\n   EventBus 통계:")
    print(f"   - 발행: {stats['published']}개")
    print(f"   - 처리: {stats['processed']}개")
    print(f"   - 실패: {stats['failed']}개")

    print("\n✅ 모든 테스트 통과! 이벤트 기반 아키텍처 정상 작동")


if __name__ == "__main__":
    test_event_based_communication()
