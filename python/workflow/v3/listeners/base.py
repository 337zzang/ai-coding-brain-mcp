"""
이벤트 리스너 기본 인터페이스
"""
from abc import ABC, abstractmethod
from typing import Set, Optional, Dict, Any
import logging

from python.workflow.v3.models import WorkflowEvent
from python.events.unified_event_types import EventType

logger = logging.getLogger(__name__)


class BaseEventListener(ABC):
    """이벤트 리스너 기본 인터페이스

    모든 이벤트 리스너가 상속해야 하는 추상 클래스입니다.
    """

    def __init__(self, enabled: bool = True):
        """
        Args:
            enabled: 리스너 활성화 여부
        """
        self.enabled = enabled
        self._subscribed_events: Set[EventType] = self.get_subscribed_events()
        self._event_count = 0
        self._error_count = 0

    @abstractmethod
    def get_subscribed_events(self) -> Set[EventType]:
        """구독할 이벤트 타입 반환

        Returns:
            구독할 EventType의 집합
        """
        pass

    @abstractmethod
    def handle_event(self, event: WorkflowEvent) -> Optional[Dict[str, Any]]:
        """이벤트 처리 로직

        Args:
            event: 처리할 워크플로우 이벤트

        Returns:
            처리 결과 딕셔너리 (선택적)
        """
        pass

    def should_handle(self, event: WorkflowEvent) -> bool:
        """이벤트 처리 여부 결정

        Args:
            event: 확인할 이벤트

        Returns:
            처리해야 하면 True
        """
        return (
            self.enabled and 
            event.type in self._subscribed_events
        )

    def on_error(self, event: WorkflowEvent, error: Exception):
        """에러 처리

        Args:
            event: 에러가 발생한 이벤트
            error: 발생한 예외
        """
        self._error_count += 1
        logger.error(
            f"Error in {self.__class__.__name__} "
            f"handling {event.type}: {error}",
            exc_info=True
        )

    def process(self, event: WorkflowEvent) -> Optional[Dict[str, Any]]:
        """이벤트 처리 래퍼 (메트릭 포함)

        Args:
            event: 처리할 이벤트

        Returns:
            처리 결과
        """
        if not self.should_handle(event):
            return None

        self._event_count += 1

        try:
            return self.handle_event(event)
        except Exception as e:
            self.on_error(event, e)
            return None

    def get_metrics(self) -> Dict[str, Any]:
        """리스너 메트릭 반환

        Returns:
            처리 통계 정보
        """
        return {
            "enabled": self.enabled,
            "subscribed_events": len(self._subscribed_events),
            "event_count": self._event_count,
            "error_count": self._error_count,
            "error_rate": self._error_count / max(self._event_count, 1)
        }
