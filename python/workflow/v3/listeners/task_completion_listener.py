"""
Enhanced Task Completion Listener for MCP Communication
태스크 완료 시 상세 정보를 MCP가 읽기 쉬운 형태로 기록
"""
from python.workflow.v3.listeners.base import BaseEventListener
from python.workflow.v3.events import EventType, WorkflowEvent
from typing import List, Dict, Any
import json
import os
from datetime import datetime

class TaskCompletionListener(BaseEventListener):
    """태스크 완료 시 MCP 통신을 위한 상세 정보 기록"""
    
    def __init__(self):
        super().__init__()
        self.completion_log_path = "logs/task_completions.json"
        self.ensure_log_file()
    
    def get_subscribed_events(self) -> List[EventType]:
        return [EventType.TASK_COMPLETED]
    
    def ensure_log_file(self):
        """로그 파일 초기화"""
        os.makedirs("logs", exist_ok=True)
        if not os.path.exists(self.completion_log_path):
            with open(self.completion_log_path, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    def handle_event(self, event: WorkflowEvent) -> bool:
        """태스크 완료 이벤트 처리"""
        try:
            # 기존 로그 읽기
            with open(self.completion_log_path, 'r', encoding='utf-8') as f:
                completions = json.load(f)
            
            # 완료 정보 구성
            completion_info = {
                "task_id": event.task_id,
                "task_title": event.details.get('title', 'Unknown'),
                "completed_at": datetime.now().isoformat(),
                "duration": event.details.get('duration'),
                "completion_note": event.details.get('note', ''),
                "plan_id": event.plan_id,
                "user": event.user,
                "success": True,
                "next_task": event.details.get('next_task'),
                "mcp_readable": True  # MCP가 읽기 위한 플래그
            }
            
            # 로그에 추가
            completions.append(completion_info)
            
            # 최근 10개만 유지 (MCP 성능 고려)
            if len(completions) > 10:
                completions = completions[-10:]
            
            # 저장
            with open(self.completion_log_path, 'w', encoding='utf-8') as f:
                json.dump(completions, f, indent=2, ensure_ascii=False)
            
            print(f"✅ TaskCompletionListener: {event.details.get('title')} 완료 기록")
            return True
            
        except Exception as e:
            print(f"❌ TaskCompletionListener 오류: {e}")
            return False
