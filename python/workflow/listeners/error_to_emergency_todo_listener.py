"""
ErrorToEmergencyTodoListener - 에러 발생 시 긴급 Todo 생성
"""
import logging
from typing import List, Dict, Any
from datetime import datetime
import json
import os

from .base import BaseEventListener
from ..models import WorkflowEvent
from python.events.unified_event_types import EventType
from ..events import EventBuilder

logger = logging.getLogger(__name__)


class ErrorToEmergencyTodoListener(BaseEventListener):
    """에러 발생 시 긴급 Todo를 생성하여 즉시 해결하도록 유도"""
    
    def __init__(self):
        super().__init__()
        self.emergency_todo_file = "emergency_todo.json"
        self.error_history = []
        self.active_emergency = None
        
    def get_subscribed_events(self) -> List[EventType]:
        """구독할 이벤트 타입"""
        return [
            EventType.TASK_FAILED,
            EventType.ERROR_OCCURRED
        ]
    
    def handle_event(self, event: WorkflowEvent) -> None:
        """이벤트 처리"""
        if event.type == EventType.TASK_FAILED:
            self._on_task_failed(event)
        elif event.type == EventType.ERROR_OCCURRED:
            self._on_error_occurred(event)
            
    def _on_task_failed(self, event: WorkflowEvent):
        """태스크 실패 시 긴급 Todo 생성"""
        task_title = event.details.get('task_title', '')
        error_msg = event.details.get('error', '')
        task_id = event.task_id
        
        # 에러 정보 저장
        error_info = {
            'type': 'task_failed',
            'task_id': task_id,
            'task_title': task_title,
            'error': error_msg,
            'timestamp': datetime.now().isoformat()
        }
        
        self.error_history.append(error_info)
        
        # 긴급 Todo 생성
        emergency_todo = self._create_emergency_todo(error_info)
        
        # 파일로 저장
        self._save_emergency_todo(emergency_todo)
        
        # 사용자에게 알림
        print(f"\n🚨 태스크 실패 감지!")
        print(f"❌ 실패한 태스크: {task_title}")
        print(f"💡 에러 내용: {error_msg}")
        print(f"\n🆘 긴급 Todo가 생성되었습니다:")
        for i, todo in enumerate(emergency_todo['todos'], 1):
            print(f"  {i}. {todo['content']}")
        print("\n⚡ 현재 작업을 중단하고 에러를 먼저 해결해주세요!")
        
    def _on_error_occurred(self, event: WorkflowEvent):
        """일반 에러 발생 시 처리"""
        error_type = event.details.get('error_type', 'Unknown')
        error_msg = event.details.get('message', '')
        
        error_info = {
            'type': 'general_error',
            'error_type': error_type,
            'message': error_msg,
            'timestamp': datetime.now().isoformat()
        }
        
        self.error_history.append(error_info)
        
        # 경미한 에러는 로깅만
        if self._is_minor_error(error_type):
            logger.warning(f"Minor error occurred: {error_type} - {error_msg}")
            return
            
        # 중요한 에러는 긴급 Todo 생성
        emergency_todo = self._create_emergency_todo(error_info)
        self._save_emergency_todo(emergency_todo)
        
        print(f"\n⚠️ 에러 발생: {error_type}")
        print(f"📋 긴급 대응이 필요합니다.")
        
    def _create_emergency_todo(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """에러 정보를 기반으로 긴급 Todo 생성"""
        error_type = error_info.get('type')
        
        todos = []
        
        if error_type == 'task_failed':
            # 태스크 실패 관련 Todo
            todos.extend([
                {
                    "content": f"에러 로그 분석 - {error_info.get('error', '')}",
                    "status": "pending",
                    "priority": "high"
                },
                {
                    "content": "에러 원인 파악 및 디버깅",
                    "status": "pending",
                    "priority": "high"
                },
                {
                    "content": "수정 사항 구현 및 테스트",
                    "status": "pending",
                    "priority": "high"
                },
                {
                    "content": "태스크 재실행 및 검증",
                    "status": "pending",
                    "priority": "medium"
                }
            ])
        else:
            # 일반 에러 관련 Todo
            todos.extend([
                {
                    "content": f"에러 상세 분석 - {error_info.get('error_type', '')}",
                    "status": "pending",
                    "priority": "high"
                },
                {
                    "content": "영향 범위 파악",
                    "status": "pending",
                    "priority": "high"
                },
                {
                    "content": "해결 방안 구현",
                    "status": "pending",
                    "priority": "high"
                }
            ])
            
        emergency_todo = {
            'id': f"emergency_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'error_info': error_info,
            'todos': todos,
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        self.active_emergency = emergency_todo
        return emergency_todo
        
    def _save_emergency_todo(self, emergency_todo: Dict[str, Any]):
        """긴급 Todo를 파일로 저장"""
        try:
            with open(self.emergency_todo_file, 'w', encoding='utf-8') as f:
                json.dump(emergency_todo, f, ensure_ascii=False, indent=2)
            logger.info(f"긴급 Todo 저장: {self.emergency_todo_file}")
        except Exception as e:
            logger.error(f"긴급 Todo 저장 실패: {e}")
            
    def _is_minor_error(self, error_type: str) -> bool:
        """경미한 에러인지 판단"""
        minor_errors = [
            'warning',
            'deprecation',
            'info',
            'notice'
        ]
        return error_type.lower() in minor_errors
        
    def resolve_emergency(self):
        """긴급 상황 해결 완료"""
        if self.active_emergency:
            self.active_emergency['status'] = 'resolved'
            self.active_emergency['resolved_at'] = datetime.now().isoformat()
            
            # 파일 삭제 또는 아카이브
            if os.path.exists(self.emergency_todo_file):
                # 아카이브로 이동
                archive_name = f"resolved_{self.active_emergency['id']}.json"
                os.rename(self.emergency_todo_file, archive_name)
                
            print("✅ 긴급 상황이 해결되었습니다.")
            self.active_emergency = None
            
    def get_active_emergency(self) -> Dict[str, Any]:
        """현재 활성화된 긴급 상황 반환"""
        return self.active_emergency