"""
이벤트 리스너 중앙 관리자 (수정됨)
"""
from typing import Dict, List, Callable, Any
import logging
import time
from collections import defaultdict

from python.workflow.v3.event_bus import EventBus, Event
from python.workflow.v3.listeners.base import BaseEventListener
from python.workflow.v3.models import WorkflowEvent
from python.events.unified_event_types import EventType

logger = logging.getLogger(__name__)


class ListenerManager:
    """이벤트 리스너 중앙 관리자

    모든 이벤트 리스너를 등록하고 관리하며,
    메트릭을 수집하고 모니터링합니다.
    """

    def __init__(self, event_bus: EventBus):
        """
        Args:
            event_bus: EventBus 인스턴스
        """
        self.event_bus = event_bus
        self.listeners: Dict[str, BaseEventListener] = {}
        self._listener_metrics: Dict[str, dict] = defaultdict(lambda: {
            "total_events": 0,
            "successful": 0,
            "failed": 0,
            "total_time": 0.0,
            "last_event": None
        })
        self._handler_refs: Dict[str, List[tuple]] = defaultdict(list)

    def register_listener(self, name: str, listener: BaseEventListener):
        """리스너 등록

        Args:
            name: 리스너 이름
            listener: BaseEventListener 인스턴스
        """
        if name in self.listeners:
            logger.warning(f"Listener {name} already registered, replacing")
            self.unregister_listener(name)

        self.listeners[name] = listener

        # EventBus에 각 이벤트 타입별로 구독
        for event_type in listener.get_subscribed_events():
            handler = self._create_handler_wrapper(name, listener)
            self.event_bus.subscribe(event_type.value, handler)
            self._handler_refs[name].append((event_type.value, handler))

        logger.info(
            f"Registered listener: {name} "
            f"(subscribing to {len(listener.get_subscribed_events())} events)"
        )

    def unregister_listener(self, name: str):
        """리스너 등록 해제

        Args:
            name: 리스너 이름
        """
        if name not in self.listeners:
            logger.warning(f"Listener {name} not found")
            return

        # EventBus에서 구독 해제
        for event_type, handler in self._handler_refs[name]:
            self.event_bus.unsubscribe(event_type, handler)

        del self.listeners[name]
        del self._handler_refs[name]

        logger.info(f"Unregistered listener: {name}")

    def _create_handler_wrapper(self, name: str, listener: BaseEventListener):
        """메트릭 수집을 포함한 핸들러 래퍼 생성

        Args:
            name: 리스너 이름
            listener: 리스너 인스턴스

        Returns:
            래핑된 핸들러 함수
        """
        def wrapper(event: Event):
            metrics = self._listener_metrics[name]
            metrics["total_events"] += 1
            metrics["last_event"] = time.time()

            start_time = time.time()
            try:
                # Event를 WorkflowEvent로 변환
                workflow_event = self._convert_to_workflow_event(event)

                # 리스너 처리
                result = listener.process(workflow_event)

                metrics["successful"] += 1
                elapsed = time.time() - start_time
                metrics["total_time"] += elapsed

                logger.debug(
                    f"Listener {name} processed {workflow_event.type} "
                    f"in {elapsed:.3f}s"
                )
                return result

            except Exception as e:
                metrics["failed"] += 1
                elapsed = time.time() - start_time
                metrics["total_time"] += elapsed

                logger.error(
                    f"Listener {name} failed processing event: {e}",
                    exc_info=True
                )

        return wrapper

    def _convert_to_workflow_event(self, event: Event) -> WorkflowEvent:
        """Event를 WorkflowEvent로 변환

        Args:
            event: EventBus의 Event 객체

        Returns:
            WorkflowEvent 객체
        """
        # 이미 WorkflowEvent인 경우
        if isinstance(event, WorkflowEvent):
            return event

        # EventType enum으로 변환
        try:
            event_type = EventType(event.type)
        except ValueError:
            # enum에 없는 타입인 경우 문자열 그대로 사용
            event_type = event.type

        # WorkflowEvent 생성
        return WorkflowEvent(
            id=getattr(event, 'id', ''),
            type=event_type,
            timestamp=getattr(event, 'timestamp', None),
            plan_id=event.payload.get('plan_id', '') if hasattr(event, 'payload') else '',
            task_id=event.payload.get('task_id', '') if hasattr(event, 'payload') else '',
            user=event.payload.get('user', 'system') if hasattr(event, 'payload') else 'system',
            details={
                k: v for k, v in event.payload.items() 
                if k not in ['plan_id', 'task_id', 'user']
            } if hasattr(event, 'payload') else {}
        )

    def get_metrics(self, name: str = None) -> Dict[str, Any]:
        """리스너 메트릭 조회

        Args:
            name: 특정 리스너 이름 (None이면 전체)

        Returns:
            메트릭 정보
        """
        if name:
            if name not in self.listeners:
                return {}

            metrics = self._listener_metrics[name].copy()
            listener_metrics = self.listeners[name].get_metrics()
            metrics.update(listener_metrics)

            # 평균 처리 시간 계산
            if metrics["total_events"] > 0:
                metrics["avg_processing_time"] = (
                    metrics["total_time"] / metrics["total_events"]
                )
            else:
                metrics["avg_processing_time"] = 0

            return metrics
        else:
            # 전체 메트릭
            all_metrics = {}
            for listener_name in self.listeners:
                all_metrics[listener_name] = self.get_metrics(listener_name)

            # 요약 정보
            total_events = sum(
                m["total_events"] for m in all_metrics.values()
            )
            total_successful = sum(
                m["successful"] for m in all_metrics.values()
            )
            total_failed = sum(
                m["failed"] for m in all_metrics.values()
            )

            all_metrics["_summary"] = {
                "total_listeners": len(self.listeners),
                "total_events": total_events,
                "total_successful": total_successful,
                "total_failed": total_failed,
                "success_rate": (
                    total_successful / total_events if total_events > 0 else 0
                )
            }

            return all_metrics

    def enable_listener(self, name: str):
        """리스너 활성화"""
        if name in self.listeners:
            self.listeners[name].enabled = True
            logger.info(f"Enabled listener: {name}")

    def disable_listener(self, name: str):
        """리스너 비활성화"""
        if name in self.listeners:
            self.listeners[name].enabled = False
            logger.info(f"Disabled listener: {name}")

    def get_listener_status(self) -> Dict[str, bool]:
        """모든 리스너의 활성화 상태 반환"""
        return {
            name: listener.enabled 
            for name, listener in self.listeners.items()
        }
