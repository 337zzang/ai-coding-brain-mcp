"""
Enhanced Event Bus with Priority Queue and Metrics
"""
import asyncio
import time
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from queue import PriorityQueue
from threading import Lock
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import logging

logger = logging.getLogger(__name__)


class EventPriority(IntEnum):
    """이벤트 우선순위"""
    CRITICAL = 1  # 시스템 중요 이벤트
    HIGH = 2      # 사용자 액션
    NORMAL = 3    # 일반 이벤트
    LOW = 4       # 백그라운드 작업


@dataclass(order=True)
class PrioritizedEvent:
    """우선순위가 있는 이벤트"""
    priority: int
    timestamp: float = field(default_factory=time.time)
    event_type: str = field(compare=False)
    data: Dict[str, Any] = field(default_factory=dict, compare=False)
    retry_count: int = field(default=0, compare=False)


class EventMetrics:
    """이벤트 처리 메트릭"""
    def __init__(self):
        self.processed_count = defaultdict(int)
        self.failed_count = defaultdict(int)
        self.processing_time = defaultdict(list)
        self.queue_size_history = deque(maxlen=1000)
        self._lock = Lock()

    def record_processed(self, event_type: str, duration: float):
        with self._lock:
            self.processed_count[event_type] += 1
            self.processing_time[event_type].append(duration)

    def record_failed(self, event_type: str):
        with self._lock:
            self.failed_count[event_type] += 1

    def record_queue_size(self, size: int):
        with self._lock:
            self.queue_size_history.append((time.time(), size))

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            stats = {
                "processed": dict(self.processed_count),
                "failed": dict(self.failed_count),
                "average_processing_time": {}
            }

            for event_type, times in self.processing_time.items():
                if times:
                    stats["average_processing_time"][event_type] = sum(times) / len(times)

            return stats


class EnhancedEventBus:
    """개선된 이벤트 버스"""

    def __init__(self, max_workers: int = 5, max_retries: int = 3):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._priority_queue = PriorityQueue()
        self._dead_letter_queue = deque(maxlen=1000)
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._metrics = EventMetrics()
        self._max_retries = max_retries
        self._running = False
        self._worker_task = None

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """이벤트 구독"""
        self._subscribers[event_type].append(handler)
        logger.info(f"Subscribed {handler.__name__} to {event_type}")

    def publish(self, event_type: str, data: Dict[str, Any], 
                priority: EventPriority = EventPriority.NORMAL) -> None:
        """이벤트 발행"""
        event = PrioritizedEvent(
            priority=priority.value,
            event_type=event_type,
            data=data
        )
        self._priority_queue.put(event)
        self._metrics.record_queue_size(self._priority_queue.qsize())

    async def start(self):
        """이벤트 처리 시작"""
        self._running = True
        self._worker_task = asyncio.create_task(self._process_events())
        logger.info("EventBus started")

    async def stop(self):
        """이벤트 처리 중지"""
        self._running = False
        if self._worker_task:
            await self._worker_task
        self._executor.shutdown(wait=True)
        logger.info("EventBus stopped")

    async def _process_events(self):
        """이벤트 처리 워커"""
        while self._running:
            try:
                # 우선순위 큐에서 이벤트 가져오기
                event = self._priority_queue.get(timeout=0.1)
                await self._handle_event(event)
            except:
                await asyncio.sleep(0.01)

    async def _handle_event(self, event: PrioritizedEvent):
        """개별 이벤트 처리"""
        start_time = time.time()
        handlers = self._subscribers.get(event.event_type, [])

        for handler in handlers:
            try:
                # 비동기 실행
                future = self._executor.submit(handler, event.data)
                future.result(timeout=30)  # 30초 타임아웃

                # 메트릭 기록
                duration = time.time() - start_time
                self._metrics.record_processed(event.event_type, duration)

            except Exception as e:
                logger.error(f"Error handling {event.event_type}: {e}")
                self._metrics.record_failed(event.event_type)

                # 재시도 로직
                if event.retry_count < self._max_retries:
                    event.retry_count += 1
                    event.priority = EventPriority.HIGH.value  # 우선순위 상승
                    self._priority_queue.put(event)
                else:
                    # 데드레터 큐로 이동
                    self._dead_letter_queue.append({
                        "event": event,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })

    def get_metrics(self) -> Dict[str, Any]:
        """메트릭 조회"""
        return {
            "stats": self._metrics.get_stats(),
            "queue_size": self._priority_queue.qsize(),
            "dead_letter_count": len(self._dead_letter_queue)
        }

    def get_dead_letters(self) -> List[Dict[str, Any]]:
        """데드레터 큐 조회"""
        return list(self._dead_letter_queue)
