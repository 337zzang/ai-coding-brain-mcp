"""
Real-time Error Report Listener for MCP Communication
오류 발생 시 즉시 MCP가 읽고 대응할 수 있도록 정보 제공
"""
from python.workflow.v3.listeners.base import BaseEventListener
from python.workflow.v3.events import EventType, WorkflowEvent
from typing import List, Dict, Any
import json
import os
from datetime import datetime
import traceback

class ErrorReportListener(BaseEventListener):
    """오류 발생 시 MCP 통신을 위한 즉각적인 리포트"""
    
    def __init__(self):
        super().__init__()
        self.error_report_path = "logs/active_errors.json"
        self.error_history_path = "logs/error_history.json"
        self.ensure_log_files()
    
    def get_subscribed_events(self) -> List[EventType]:
        return [EventType.TASK_FAILED]
    
    def ensure_log_files(self):
        """로그 파일 초기화"""
        os.makedirs("logs", exist_ok=True)
        
        # 활성 오류 파일 (MCP가 즉시 읽을 파일)
        if not os.path.exists(self.error_report_path):
            with open(self.error_report_path, 'w', encoding='utf-8') as f:
                json.dump({"active_errors": [], "requires_attention": False}, f)        
        # 오류 이력 파일
        if not os.path.exists(self.error_history_path):
            with open(self.error_history_path, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    def handle_event(self, event: WorkflowEvent) -> bool:
        """오류 이벤트 처리"""
        try:
            # 오류 정보 구성
            error_info = {
                "error_id": f"ERR_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "occurred_at": datetime.now().isoformat(),
                "task_id": event.task_id,
                "task_title": event.details.get('title', 'Unknown Task'),
                "error_type": event.details.get('error_type', 'UnknownError'),
                "error_message": event.details.get('message', 'No error message'),
                "stack_trace": event.details.get('stack_trace', ''),
                "context": {
                    "plan_id": event.plan_id,
                    "user": event.user,
                    "workflow_stage": event.details.get('stage', 'unknown')
                },
                "suggested_actions": self._suggest_actions(event.details),
                "severity": self._determine_severity(event.details),
                "mcp_action_required": True
            }
            
            # 활성 오류로 등록
            with open(self.error_report_path, 'r', encoding='utf-8') as f:
                active_data = json.load(f)            
            active_data['active_errors'].append(error_info)
            active_data['requires_attention'] = True
            active_data['last_error_time'] = datetime.now().isoformat()
            
            # 저장
            with open(self.error_report_path, 'w', encoding='utf-8') as f:
                json.dump(active_data, f, indent=2, ensure_ascii=False)
            
            # 이력에도 저장
            with open(self.error_history_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
            history.append(error_info)
            with open(self.error_history_path, 'w', encoding='utf-8') as f:
                json.dump(history[-50:], f, indent=2, ensure_ascii=False)  # 최근 50개만
            
            print(f"🚨 ErrorReportListener: {error_info['error_type']} - MCP 대응 필요!")
            return True
            
        except Exception as e:
            print(f"❌ ErrorReportListener 자체 오류: {e}")
            return False
    
    def _suggest_actions(self, details: Dict[str, Any]) -> List[str]:
        """오류에 따른 권장 조치 제안"""
        error_type = details.get('error_type', '')
        suggestions = []
        
        if 'FileNotFound' in error_type:
            suggestions.append("파일 존재 여부 확인")
            suggestions.append("파일 경로 검증")
            suggestions.append("필요시 파일 생성")
        elif 'Permission' in error_type:
            suggestions.append("파일/디렉토리 권한 확인")
            suggestions.append("실행 권한 부여")
        elif 'Import' in error_type:
            suggestions.append("모듈 설치 확인")
            suggestions.append("import 경로 검증")
        elif 'Syntax' in error_type:
            suggestions.append("코드 문법 검사")
            suggestions.append("들여쓰기 확인")
        else:
            suggestions.append("오류 메시지 분석")
            suggestions.append("스택 트레이스 확인")
        
        return suggestions
    
    def _determine_severity(self, details: Dict[str, Any]) -> str:
        """오류 심각도 판단"""
        error_type = details.get('error_type', '')
        
        if any(critical in error_type for critical in ['System', 'Fatal', 'Critical']):
            return "CRITICAL"
        elif any(high in error_type for high in ['Permission', 'Import', 'Module']):
            return "HIGH"
        elif any(medium in error_type for medium in ['File', 'Path', 'Value']):
            return "MEDIUM"
        else:
            return "LOW"
