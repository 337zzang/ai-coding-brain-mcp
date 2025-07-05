"""
워크플로우 관리자 - 중앙집중식 상태 관리
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """작업 상태"""
    TODO = "todo"
    PENDING = "pending"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class WorkflowManager:
    """워크플로우 중앙 관리자"""
    
    def __init__(self, workflow_file: str = "memory/workflow.json"):
        self.workflow_file = Path(workflow_file)
        self.data = self._load_data()
    
    def _load_data(self) -> Dict[str, Any]:
        """워크플로우 데이터 로드"""
        if not self.workflow_file.exists():
            return {"plans": [], "current_plan_id": None}
        
        try:
            with open(self.workflow_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"워크플로우 로드 실패: {e}")
            return {"plans": [], "current_plan_id": None}
    
    def save_data(self):
        """워크플로우 데이터 저장"""
        try:
            self.workflow_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.workflow_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"워크플로우 저장 실패: {e}")
    
    @property
    def current_plan(self) -> Optional[Dict[str, Any]]:
        """현재 활성 계획 가져오기"""
        current_plan_id = self.data.get('current_plan_id')
        if not current_plan_id:
            return None
        
        for plan in self.data.get('plans', []):
            if plan.get('id') == current_plan_id:
                return plan
        return None
    
    def get_current_task(self) -> Optional[Dict[str, Any]]:
        """현재 작업 가져오기 (우선순위: in_progress > approved > pending > todo)"""
        plan = self.current_plan
        if not plan:
            return None
        
        tasks = plan.get('tasks', [])
        
        # 우선순위별로 작업 찾기
        priority_statuses = ['in_progress', 'approved', 'pending', 'todo']
        for status in priority_statuses:
            for task in tasks:
                if task.get('status') == status:
                    return task
        
        return None
    
    def get_summary(self) -> Dict[str, Any]:
        """현재 계획·작업 요약 정보(프린트용) 반환"""
        if not self.current_plan:
            return {'has_active_plan': False}
        
        plan = self.current_plan
        tasks = plan.get('tasks', [])
        completed = [t for t in tasks if t.get('status') == 'completed']
        current = self.get_current_task()
        
        return {
            'has_active_plan': True,
            'plan_name': plan.get('name'),
            'description': plan.get('description'),
            'total_tasks': len(tasks),
            'completed_tasks': len(completed),
            'progress_percent': round(len(completed) / len(tasks) * 100, 1) if tasks else 0,
            'current_task': current,
        }
