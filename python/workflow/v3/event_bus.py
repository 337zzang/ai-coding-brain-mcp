"""
Event Bus System for MCP Workflow V3
====================================

이벤트 기반 아키텍처의 핵심 컴포넌트로, 모듈 간 느슨한 결합을 제공합니다.

주요 기능:
- 싱글톤 패턴으로 전역 이벤트 버스 제공
- 발행/구독(Pub/Sub) 메커니즘
- 비동기 이벤트 처리
- 실패 시 재시도 로직
- 이벤트 로깅 및 추적
"""

import threading
import logging
from typing import Dict, List, Callable, Any, Optional
from collections import defaultdict
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor, Future
from datetime import datetime
import traceback
import time
from dataclasses import dataclass, field
import uuid

# 로거 설정
logger = logging.getLogger(__name__)


@dataclass
class Event:
    """기본 이벤트 클래스"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """이벤트 생성 후 처리"""
        if not self.type:
            raise ValueError("Event type is required")

        # 메타데이터에 기본 정보 추가
        self.metadata.update({
            'created_at': self.timestamp.isoformat(),
            'event_id': self.id,
            'event_type': self.type
        })


class EventBus:
    """
    중앙 이벤트 버스 (싱글톤 패턴)

    모든 모듈이 이벤트를 발행하고 구독할 수 있는 중앙 허브입니다.
    비동기 처리를 통해 발행자를 블로킹하지 않습니다.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """싱글톤 패턴 구현"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """EventBus 초기화"""
        # 이미 초기화되었으면 스킵
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._event_queue: Queue = Queue()
        self._executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=5)
        self._running = False
        self._processor_thread: Optional[threading.Thread] = None
        self._retry_config = {
            'max_retries': 3,
            'retry_delay': 1.0,  # seconds
            'backoff_factor': 2.0
        }

        # 이벤트 통계
        self._stats = {
            'published': 0,
            'processed': 0,
            'failed': 0,
            'retried': 0
        }

        logger.info("EventBus initialized")

    def start(self):
        """이벤트 처리 시작"""
        if self._running:
            logger.warning("EventBus is already running")
            return

        self._running = True
        self._processor_thread = threading.Thread(
            target=self._process_events,
            daemon=True
        )
        self._processor_thread.start()
        logger.info("EventBus started")

    def stop(self):
        """이벤트 처리 중지"""
        if not self._running:
            return

        self._running = False
        self._event_queue.put(None)  # 종료 신호

        if self._processor_thread:
            self._processor_thread.join(timeout=5)

        self._executor.shutdown(wait=True, cancel_futures=True)
        logger.info("EventBus stopped")

    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """
        이벤트 핸들러 등록

        Args:
            event_type: 구독할 이벤트 타입
            handler: 이벤트 처리 함수 (Event 객체를 받음)
        """
        if not callable(handler):
            raise ValueError(f"Handler must be callable, got {type(handler)}")

        self._handlers[event_type].append(handler)
        logger.debug(f"Handler {handler.__name__} subscribed to {event_type}")

    def unsubscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """
        이벤트 핸들러 제거

        Args:
            event_type: 구독 해제할 이벤트 타입
            handler: 제거할 핸들러 함수
        """
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

            # 빈 리스트는 제거
            if not self._handlers[event_type]:
                del self._handlers[event_type]

            logger.debug(f"Handler {handler.__name__} unsubscribed from {event_type}")

    def publish(self, event: Event) -> None:
        """
        이벤트 발행 (비동기)

        Args:
            event: 발행할 이벤트 객체
        """
        # 더 유연한 타입 체크 - duck typing 방식
        if not hasattr(event, 'type') or not hasattr(event, 'id'):
            raise ValueError(f"Event must have 'type' and 'id' attributes, got {type(event)}")

        self._stats['published'] += 1
        self._event_queue.put(event)
        logger.debug(f"Event published: {event.type} (id: {event.id})")

    def publish_sync(self, event: Event) -> List[Future]:
        """
        이벤트 동기 발행 (테스트용)

        Args:
            event: 발행할 이벤트 객체

        Returns:
            핸들러 실행 Future 리스트
        """
        futures = []
        handlers = self._handlers.get(event.type, [])

        for handler in handlers:
            future = self._executor.submit(self._execute_handler, handler, event)
            futures.append(future)

        return futures

    def _process_events(self):
        """백그라운드 이벤트 처리 루프"""
        logger.info("Event processing loop started")

        while self._running:
            try:
                # 타임아웃을 두어 주기적으로 종료 상태 체크
                event = self._event_queue.get(timeout=1.0)

                if event is None:  # 종료 신호
                    break

                self._process_single_event(event)

            except Empty:
                continue
            except Exception as e:
                logger.error(f"Error in event processing loop: {e}")
                logger.debug(traceback.format_exc())

        logger.info("Event processing loop stopped")

    def _process_single_event(self, event: Event):
        """단일 이벤트 처리"""
        handlers = self._handlers.get(event.type, [])

        if not handlers:
            logger.debug(f"No handlers for event type: {event.type}")
            return

        logger.debug(f"Processing event {event.type} with {len(handlers)} handlers")

        # 각 핸들러를 비동기로 실행
        for handler in handlers:
            self._executor.submit(self._execute_handler, handler, event)

    def _execute_handler(self, handler: Callable, event: Event):
        """
        핸들러 실행 (재시도 로직 포함)

        Args:
            handler: 실행할 핸들러 함수
            event: 처리할 이벤트
        """
        retries = 0
        delay = self._retry_config['retry_delay']

        while retries <= self._retry_config['max_retries']:
            try:
                handler(event)
                self._stats['processed'] += 1
                logger.debug(f"Handler {handler.__name__} processed event {event.type}")
                return

            except Exception as e:
                retries += 1
                self._stats['retried'] += 1

                if retries > self._retry_config['max_retries']:
                    self._stats['failed'] += 1
                    logger.error(
                        f"Handler {handler.__name__} failed after {retries-1} retries: {e}"
                    )
                    logger.debug(traceback.format_exc())

                    # Dead Letter Queue에 추가 (향후 구현)
                    self._handle_failed_event(event, handler, e)
                    return

                logger.warning(
                    f"Handler {handler.__name__} failed (retry {retries}/{self._retry_config['max_retries']}): {e}"
                )

                # Exponential backoff
                time.sleep(delay)
                delay *= self._retry_config['backoff_factor']

    def _handle_failed_event(self, event: Event, handler: Callable, error: Exception):
        """
        실패한 이벤트 처리

        향후 Dead Letter Queue 구현 시 여기에 추가
        """
        failed_event_data = {
            'event': event,
            'handler': handler.__name__,
            'error': str(error),
            'traceback': traceback.format_exc(),
            'timestamp': datetime.now().isoformat()
        }

        # TODO: Dead Letter Queue에 저장
        logger.error(f"Failed event logged: {failed_event_data}")

    def get_stats(self) -> Dict[str, int]:
        """이벤트 처리 통계 반환"""
        return self._stats.copy()

    def get_handlers_count(self) -> Dict[str, int]:
        """이벤트 타입별 핸들러 수 반환"""
        return {event_type: len(handlers) for event_type, handlers in self._handlers.items()}

    def clear_handlers(self, event_type: Optional[str] = None):
        """
        핸들러 초기화

        Args:
            event_type: 특정 이벤트 타입만 초기화 (None이면 전체)
        """
        if event_type:
            self._handlers[event_type].clear()
        else:
            self._handlers.clear()

    def __repr__(self):
        return (
            f"EventBus(running={self._running}, "
            f"handlers={len(self._handlers)}, "
            f"stats={self._stats})"
        )


# 전역 이벤트 버스 인스턴스
event_bus = EventBus()

# 자동 시작 (import 시)
if not event_bus._running:
    event_bus.start()
