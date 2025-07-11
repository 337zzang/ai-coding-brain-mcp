# 이벤트 버스 구현 예제
# python/events/event_bus.py

from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from datetime import datetime
import asyncio
from enum import Enum

class EventType(Enum):
    """이벤트 타입 정의"""
    # 워크플로우 이벤트
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    PLAN_CREATED = "plan.created"
    PLAN_COMPLETED = "plan.completed"

    # 파일 시스템 이벤트
    FILE_ACCESSED = "file.accessed"
    FILE_CREATED = "file.created"
    FILE_MODIFIED = "file.modified"

    # 컨텍스트 이벤트
    CONTEXT_UPDATED = "context.updated"
    PROJECT_SWITCHED = "project.switched"

@dataclass
class Event:
    """기본 이벤트 클래스"""
    type: EventType
    data: Dict[str, Any]
    timestamp: str = None
    source: str = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

class EventBus:
    """중앙 이벤트 버스"""

    def __init__(self):
        self._handlers: Dict[EventType, List[Callable]] = {}
        self._async_handlers: Dict[EventType, List[Callable]] = {}
        self._middleware: List[Callable] = []

    def subscribe(self, event_type: EventType, handler: Callable):
        """이벤트 핸들러 등록"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def subscribe_async(self, event_type: EventType, handler: Callable):
        """비동기 이벤트 핸들러 등록"""
        if event_type not in self._async_handlers:
            self._async_handlers[event_type] = []
        self._async_handlers[event_type].append(handler)

    def unsubscribe(self, event_type: EventType, handler: Callable):
        """이벤트 핸들러 제거"""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)

    def add_middleware(self, middleware: Callable):
        """미들웨어 추가 (모든 이벤트에 적용)"""
        self._middleware.append(middleware)

    def publish(self, event: Event):
        """이벤트 발행 (동기)"""
        # 미들웨어 실행
        for middleware in self._middleware:
            event = middleware(event)
            if event is None:
                return  # 미들웨어가 이벤트를 차단

        # 동기 핸들러 실행
        if event.type in self._handlers:
            for handler in self._handlers[event.type]:
                try:
                    handler(event)
                except Exception as e:
                    print(f"Error in handler {handler.__name__}: {e}")

    async def publish_async(self, event: Event):
        """이벤트 발행 (비동기)"""
        # 비동기 핸들러 실행
        if event.type in self._async_handlers:
            tasks = []
            for handler in self._async_handlers[event.type]:
                tasks.append(asyncio.create_task(handler(event)))
            await asyncio.gather(*tasks, return_exceptions=True)

# 싱글톤 인스턴스
_event_bus = EventBus()

def get_event_bus() -> EventBus:
    """이벤트 버스 싱글톤 인스턴스 반환"""
    return _event_bus

# 사용 예제
if __name__ == "__main__":
    bus = get_event_bus()

    # 핸들러 정의
    def on_task_started(event: Event):
        print(f"Task started: {event.data.get('task_id')}")

    def on_file_accessed(event: Event):
        print(f"File accessed: {event.data.get('file_path')}")

    # 핸들러 등록
    bus.subscribe(EventType.TASK_STARTED, on_task_started)
    bus.subscribe(EventType.FILE_ACCESSED, on_file_accessed)

    # 이벤트 발행
    bus.publish(Event(
        type=EventType.TASK_STARTED,
        data={"task_id": "task_123", "title": "Sample Task"},
        source="WorkflowManager"
    ))
