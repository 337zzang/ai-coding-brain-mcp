"""
AI Instruction Base for MCP Communication
모든 리스너가 AI에게 지시를 내리기 위한 기본 구조
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import json
import os

class ActionType(Enum):
    """AI가 수행할 작업 타입"""
    GIT_COMMIT = "git_commit"
    GIT_PUSH = "git_push"
    CREATE_FILE = "create_file"
    UPDATE_FILE = "update_file"
    REPORT_USER = "report_user"
    FIX_ERROR = "fix_error"
    RUN_TEST = "run_test"
    UPDATE_DOCS = "update_docs"
    WORKFLOW_COMMAND = "workflow_command"
    ANALYZE_CODE = "analyze_code"
    SEND_NOTIFICATION = "send_notification"

class Priority(Enum):
    """작업 우선순위"""
    CRITICAL = "critical"  # 즉시 처리 필요 (에러 등)
    HIGH = "high"         # 높은 우선순위
    NORMAL = "normal"     # 일반 작업
    LOW = "low"          # 나중에 처리 가능
class AIInstruction:
    """AI에게 전달할 지시서 구조"""
    
    def __init__(self, event_type: str, context: Dict[str, Any]):
        self.instruction_id = f"INS_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:17]}"
        self.created_at = datetime.now().isoformat()
        self.event_type = event_type
        self.context = context
        self.actions: List[Dict[str, Any]] = []
        self.priority = Priority.NORMAL
        self.status = "pending"
        
    def add_action(self, action_type: ActionType, params: Dict[str, Any], 
                   order: int = None, depends_on: List[str] = None):
        """AI가 수행할 작업 추가"""
        action = {
            "action_id": f"ACT_{len(self.actions) + 1}",
            "type": action_type.value,
            "params": params,
            "order": order or len(self.actions) + 1,
            "depends_on": depends_on or [],
            "status": "pending"
        }
        self.actions.append(action)
        
    def set_priority(self, priority: Priority):
        """우선순위 설정"""
        self.priority = priority        
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "instruction_id": self.instruction_id,
            "created_at": self.created_at,
            "event_type": self.event_type,
            "context": self.context,
            "ai_actions_required": self.actions,
            "priority": self.priority.value,
            "status": self.status,
            "mcp_executable": True
        }
    
    def save(self, filepath: str = "logs/ai_instructions.json"):
        """지시서 저장"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # 기존 지시서 읽기
        instructions = []
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                try:
                    instructions = json.load(f)
                except:
                    instructions = []
        
        # 새 지시서 추가
        instructions.append(self.to_dict())
        
        # 최근 20개만 유지
        if len(instructions) > 20:
            instructions = instructions[-20:]
        
        # 저장
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(instructions, f, indent=2, ensure_ascii=False)
            
        # 활성 지시서도 별도 저장 (AI가 바로 읽을 수 있도록)
        active_path = "logs/active_ai_instruction.json"
        with open(active_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)