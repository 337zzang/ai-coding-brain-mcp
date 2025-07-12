"""
ContextUpdateListener - 컨텍스트 업데이트 리스너
"""
import logging
from typing import List
from pathlib import Path
import json
from datetime import datetime

from ..models import EventType, WorkflowEvent
from .base import BaseEventListener

logger = logging.getLogger(__name__)


class ContextUpdateListener(BaseEventListener):
    """워크플로우 이벤트에 따른 컨텍스트 자동 업데이트"""

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self.context_file = Path("memory/context.json")

    def get_subscribed_events(self) -> List[EventType]:
        """구독할 이벤트 타입"""
        return [
            EventType.PLAN_CREATED,
            EventType.PLAN_STARTED,
            EventType.PLAN_COMPLETED,
            EventType.TASK_STARTED,
            EventType.TASK_COMPLETED
        ]

    def handle_event(self, event: WorkflowEvent) -> None:
        """이벤트 처리"""
        if not self.enabled:
            return

        try:
            # 컨텍스트 파일 읽기
            context = {}
            if self.context_file.exists():
                with open(self.context_file, 'r', encoding='utf-8') as f:
                    context = json.load(f)

            # 이벤트에 따른 업데이트
            if event.type == EventType.PLAN_CREATED:
                context['current_plan'] = {
                    'id': event.plan_id,
                    'name': event.details.get('name', '') if event.details else '',
                    'created_at': event.timestamp.isoformat() if hasattr(event.timestamp, 'isoformat') else str(event.timestamp)
                }
            
            elif event.type == EventType.TASK_STARTED:
                context['current_task'] = {
                    'id': event.task_id,
                    'title': event.details.get('title', '') if event.details else '',
                    'started_at': event.timestamp.isoformat() if hasattr(event.timestamp, 'isoformat') else str(event.timestamp)
                }
                
            elif event.type == EventType.TASK_COMPLETED:
                if 'completed_tasks' not in context:
                    context['completed_tasks'] = []
                    
                context['completed_tasks'].append({
                    'id': event.task_id,
                    'title': event.details.get('title', '') if event.details else '',
                    'completed_at': event.timestamp.isoformat() if hasattr(event.timestamp, 'isoformat') else str(event.timestamp)
                })

            # 컨텍스트 저장
            context['last_updated'] = datetime.now().isoformat()
            self.context_file.parent.mkdir(exist_ok=True)
            
            with open(self.context_file, 'w', encoding='utf-8') as f:
                json.dump(context, f, indent=2, ensure_ascii=False)
                
            logger.debug(f"Context updated for event: {event.type}")
            
        except Exception as e:
            logger.error(f"ContextUpdateListener error: {e}")
