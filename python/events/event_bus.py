"""
Event Bus Core Implementation
중앙 이벤트 버스 시스템으로 모듈 간 느슨한 결합을 실현합니다.
"""

from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import traceback
from collections import defaultdict
import weakref

# 로거 설정
logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """이벤트 우선순위"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Event:
    """기본 이벤트 클래스"""
    type: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    source: Optional[str] = None
    priority: EventPriority = EventPriority.NORMAL
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """이벤트 생성 후 처리"""
        if 'event_id' not in self.metadata:
            import uuid
            self.metadata['event_id'] = str(uuid.uuid4())


class EventBus:
    """중앙 이벤트 버스"""

    def __init__(self):
        # 핸들러 저장 (약한 참조 사용으로 메모리 누수 방지)
        self._handlers: Dict[str, List[weakref.ref]] = defaultdict(list)
        self._middleware: List[Callable] = []
        self._event_history: List[Event] = []
        self._max_history_size = 1000

    def subscribe(self, event_type: str, handler: Callable, priority: EventPriority = EventPriority.NORMAL):
        """이벤트 핸들러 등록"""
        # 핸들러를 약한 참조로 저장
        handler_ref = weakref.ref(handler)

        # 우선순위에 따라 정렬하여 저장
        self._handlers[event_type].append((priority, handler_ref))
        self._handlers[event_type].sort(key=lambda x: x[0].value, reverse=True)

        logger.debug(f"Handler {handler.__name__} subscribed to {event_type}")

    def unsubscribe(self, event_type: str, handler: Callable):
        """이벤트 핸들러 제거"""
        if event_type in self._handlers:
            # 약한 참조 중에서 해당 핸들러 찾아 제거
            self._handlers[event_type] = [
                (priority, ref) for priority, ref in self._handlers[event_type]
                if ref() is not handler
            ]

    def add_middleware(self, middleware: Callable):
        """미들웨어 추가 (모든 이벤트에 적용)"""
        self._middleware.append(middleware)

    def publish(self, event: Event) -> List[Any]:
        """이벤트 발행"""
        # 이벤트 히스토리에 추가
        self._add_to_history(event)

        # 미들웨어 처리
        for middleware in self._middleware:
            try:
                event = middleware(event)
                if event is None:
                    logger.debug(f"Event {event.type} blocked by middleware")
                    return []
            except Exception as e:
                logger.error(f"Middleware error: {e}")

        # 핸들러 실행
        results = []
        if event.type in self._handlers:
            # 죽은 참조 정리
            self._cleanup_dead_handlers(event.type)

            for priority, handler_ref in self._handlers[event.type]:
                handler = handler_ref()
                if handler:
                    try:
                        result = handler(event)
                        results.append(result)
                    except Exception as e:
                        logger.error(f"Handler {handler.__name__} error: {e}")
                        logger.error(traceback.format_exc())

        return results

    def _cleanup_dead_handlers(self, event_type: str):
        """죽은 핸들러 참조 정리"""
        self._handlers[event_type] = [
            (priority, ref) for priority, ref in self._handlers[event_type]
            if ref() is not None
        ]

    def _add_to_history(self, event: Event):
        """이벤트 히스토리에 추가"""
        self._event_history.append(event)

        # 최대 크기 유지
        if len(self._event_history) > self._max_history_size:
            self._event_history = self._event_history[-self._max_history_size:]

    def get_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[Event]:
        """이벤트 히스토리 조회"""
        history = self._event_history

        if event_type:
            history = [e for e in history if e.type == event_type]

        return history[-limit:]

    def clear_handlers(self, event_type: Optional[str] = None):
        """핸들러 초기화"""
        if event_type:
            self._handlers[event_type] = []
        else:
            self._handlers.clear()


# 싱글톤 인스턴스
_event_bus_instance = None


def get_event_bus() -> EventBus:
    """이벤트 버스 싱글톤 인스턴스 반환"""
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus()
    return _event_bus_instance


# 데코레이터 패턴으로 쉬운 구독
def subscribe_to(event_type: str, priority: EventPriority = EventPriority.NORMAL):
    """이벤트 구독 데코레이터"""
    def decorator(func):
        get_event_bus().subscribe(event_type, func, priority)
        return func
    return decorator
