"""
워크플로우 메시지 컨트롤러 - AI 친화적 메시지 출력
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import contextmanager

class MessageController:
    """
    통합 메시지 컨트롤러
    - stdout으로 메시지 출력 (AI가 볼 수 있도록)
    - 로깅 시스템 연동
    - 메시지 버퍼링 및 배치 처리
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.suppressed = False
        self.logger = logging.getLogger("workflow.messages")
        self.error_count = 0
        self.message_buffer: List[str] = []
        self.batch_mode = False
        
    def emit(self, msg_type: str, entity_id: str, data: Dict[str, Any]):
        """AI가 인식하기 쉬운 형식으로 메시지 출력"""
        if self.suppressed:
            return
            
        # AI가 인식하기 쉬운 확장 형식
        action = self._get_ai_action(msg_type, entity_id, data)
        
        # 확장된 메시지 형식 (AI용)
        print(f"\n{'='*60}")
        print(f"[WORKFLOW-MESSAGE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Type: {msg_type}")
        print(f"Entity: {entity_id}")
        print(f"AI Action: {action}")
        print(f"Data: {json.dumps(data, indent=2, ensure_ascii=False)}")
        print(f"{'='*60}\n")
        
        # 1. 항상 stdout으로 출력 (AI가 볼 수 있도록)
        print(f"st:{msg_type}:{entity_id}:{json.dumps(data)}")
        
        # 2. 로깅 (설정되어 있으면)
        if self.logger.isEnabledFor(logging.INFO):
            self.logger.info(f"{msg_type}:{entity_id} - {data}")
            
        # 3. 배치 모드일 때는 버퍼에 저장
        if self.batch_mode:
            self.message_buffer.append(f"{msg_type}:{entity_id}:{json.dumps(data)}")
            
    def _get_ai_action(self, msg_type: str, entity_id: str, data: Dict) -> str:
        """메시지 타입과 데이터에 따른 AI 액션 결정"""
        if msg_type == "state_changed":
            from_state = data.get("from")
            to_state = data.get("to")
            
            if "task" in entity_id:
                if to_state == "completed":
                    return "Generate task completion report with results and next steps"
                elif to_state == "in_progress":
                    return "Create detailed design document with impact analysis"
                elif to_state == "error":
                    return "Analyze error logs and provide fix suggestions"
            elif "plan" in entity_id and to_state == "completed":
                return "Generate comprehensive phase completion report"
                
        elif msg_type == "error_occurred":
            return "Analyze error cause and provide immediate fix"
        elif msg_type == "task_summary":
            status = data.get("status")
            if status == "completed":
                return "Document success factors and lessons learned"
            elif status == "failed":
                return "Analyze failure reasons and suggest alternatives"
        elif msg_type == "progress_update":
            return "Update project dashboard and timeline"
            
        return "Monitor and log event"
            
    def emit_transition(self, entity_id: str, old_state: str, new_state: str,
                       metadata: Optional[Dict] = None):
        """상태 전이 메시지"""
        data = {
            "from": old_state,
            "to": new_state,
            **(metadata or {})
        }
        self.emit("state_changed", entity_id, data)
        
    def emit_error(self, entity_id: str, error_type: str, message: str, 
                  context: Optional[Dict] = None):
        """에러 메시지"""
        self.error_count += 1
        data = {
            "error": error_type,
            "message": message,
            "context": context or {},
            "timestamp": datetime.now().isoformat()
        }
        self.emit("error_occurred", entity_id, data)
        
        # 에러 통계
        self.emit("error_stats", "system", {"total_errors": self.error_count})
        
    def emit_summary(self, entity_id: str, status: str, stats: Dict):
        """요약 메시지"""
        data = {
            "status": status,
            **stats
        }
        self.emit("task_summary", entity_id, data)
        
    def emit_progress(self, plan_id: str, completed: int, total: int):
        """진행률 메시지"""
        percent = int((completed / total * 100)) if total > 0 else 0
        data = {
            "completed": completed,
            "total": total,
            "percent": percent
        }
        self.emit("progress_update", plan_id, data)
        
    @contextmanager
    def suppress(self):
        """메시지 출력 임시 중단"""
        old_state = self.suppressed
        self.suppressed = True
        try:
            yield
        finally:
            self.suppressed = old_state
            
    @contextmanager
    def batch(self):
        """배치 모드 - 메시지를 버퍼에 모았다가 한번에 처리"""
        old_batch = self.batch_mode
        self.batch_mode = True
        self.message_buffer.clear()
        try:
            yield self.message_buffer
        finally:
            self.batch_mode = old_batch
            # 배치 메시지 처리
            if self.message_buffer and not self.suppressed:
                print(f"\n[BATCH] {len(self.message_buffer)} messages")
                
    def get_error_count(self) -> int:
        """에러 카운트 반환"""
        return self.error_count
        
    def reset_error_count(self):
        """에러 카운트 초기화"""
        self.error_count = 0


# 싱글톤 인스턴스 (하위 호환성)
message_controller = MessageController()
