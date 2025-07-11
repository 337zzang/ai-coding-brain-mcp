# WorkflowContextBridge 구현 예제
# python/integration/workflow_context_bridge.py

from typing import Optional
from events.event_bus import EventBus, Event, EventType, get_event_bus

class WorkflowContextBridge:
    """워크플로우와 컨텍스트 매니저를 연결하는 브릿지"""

    def __init__(self):
        self.event_bus = get_event_bus()
        self.current_task_id: Optional[str] = None
        self._setup_handlers()

    def _setup_handlers(self):
        """이벤트 핸들러 설정"""
        # 워크플로우 이벤트 구독
        self.event_bus.subscribe(EventType.TASK_STARTED, self._on_task_started)
        self.event_bus.subscribe(EventType.TASK_COMPLETED, self._on_task_completed)
        self.event_bus.subscribe(EventType.PLAN_CREATED, self._on_plan_created)

        # 파일 시스템 이벤트 구독
        self.event_bus.subscribe(EventType.FILE_ACCESSED, self._on_file_accessed)
        self.event_bus.subscribe(EventType.FILE_CREATED, self._on_file_created)

    def _on_task_started(self, event: Event):
        """태스크 시작 시 처리"""
        self.current_task_id = event.data.get('task_id')

        # 컨텍스트에 태스크 시작 기록
        context_event = Event(
            type=EventType.CONTEXT_UPDATED,
            data={
                'update_type': 'task_started',
                'task_id': self.current_task_id,
                'task_title': event.data.get('title'),
                'timestamp': event.timestamp
            },
            source='WorkflowContextBridge'
        )
        self.event_bus.publish(context_event)

    def _on_task_completed(self, event: Event):
        """태스크 완료 시 처리"""
        task_id = event.data.get('task_id')

        # 컨텍스트에 태스크 완료 기록
        context_event = Event(
            type=EventType.CONTEXT_UPDATED,
            data={
                'update_type': 'task_completed',
                'task_id': task_id,
                'completion_notes': event.data.get('notes'),
                'timestamp': event.timestamp
            },
            source='WorkflowContextBridge'
        )
        self.event_bus.publish(context_event)

        # 현재 태스크 ID 초기화
        if self.current_task_id == task_id:
            self.current_task_id = None

    def _on_plan_created(self, event: Event):
        """계획 생성 시 처리"""
        # 컨텍스트에 새 계획 기록
        context_event = Event(
            type=EventType.CONTEXT_UPDATED,
            data={
                'update_type': 'plan_created',
                'plan_id': event.data.get('plan_id'),
                'plan_name': event.data.get('name'),
                'timestamp': event.timestamp
            },
            source='WorkflowContextBridge'
        )
        self.event_bus.publish(context_event)

    def _on_file_accessed(self, event: Event):
        """파일 접근 시 처리"""
        # 현재 태스크 ID와 연결하여 기록
        file_data = event.data.copy()
        file_data['task_id'] = self.current_task_id

        # 컨텍스트에 파일 접근 기록
        context_event = Event(
            type=EventType.CONTEXT_UPDATED,
            data={
                'update_type': 'file_access',
                'file_path': file_data.get('file_path'),
                'operation': file_data.get('operation'),
                'task_id': self.current_task_id,
                'timestamp': event.timestamp
            },
            source='WorkflowContextBridge'
        )
        self.event_bus.publish(context_event)

    def _on_file_created(self, event: Event):
        """파일 생성 시 처리"""
        # 현재 태스크 ID와 연결하여 기록
        file_data = event.data.copy()
        file_data['task_id'] = self.current_task_id

        # 컨텍스트에 파일 생성 기록
        context_event = Event(
            type=EventType.CONTEXT_UPDATED,
            data={
                'update_type': 'file_created',
                'file_path': file_data.get('file_path'),
                'task_id': self.current_task_id,
                'timestamp': event.timestamp
            },
            source='WorkflowContextBridge'
        )
        self.event_bus.publish(context_event)

# 싱글톤 인스턴스
_bridge_instance = None

def get_workflow_context_bridge() -> WorkflowContextBridge:
    """브릿지 싱글톤 인스턴스 반환"""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = WorkflowContextBridge()
    return _bridge_instance

# 사용 예제
if __name__ == "__main__":
    # 브릿지 초기화
    bridge = get_workflow_context_bridge()

    # 이벤트 버스 가져오기
    bus = get_event_bus()

    # 태스크 시작 이벤트 발행
    bus.publish(Event(
        type=EventType.TASK_STARTED,
        data={
            'task_id': 'task_456',
            'title': '순환 의존성 분석'
        },
        source='WorkflowManager'
    ))

    # 파일 접근 이벤트 발행 (현재 태스크와 자동 연결됨)
    bus.publish(Event(
        type=EventType.FILE_ACCESSED,
        data={
            'file_path': 'python/workflow/models.py',
            'operation': 'read'
        },
        source='FileManager'
    ))
