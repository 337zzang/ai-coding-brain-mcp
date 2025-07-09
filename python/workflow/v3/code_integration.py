"""
Workflow v3 Code Integration
코드 실행과 워크플로우 통합
"""
from typing import Dict, Any, Optional
import json
import os
from datetime import datetime

from .manager import WorkflowManager
from .parser import CommandParser
from .storage import FileStorage
from .models import EventType


class WorkflowCodeIntegration:
    """코드 실행과 워크플로우 통합"""
    
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.storage_path = os.path.join('memory', 'workflow_v3')
        self.storage = FileStorage(self.storage_path)
        self.manager = WorkflowManager(storage=self.storage)
        self.parser = CommandParser()
        
    def get_current_task_context(self) -> Optional[Dict[str, Any]]:
        """현재 태스크 컨텍스트 가져오기"""
        state = self.manager.get_state()
        if not state.current_plan:
            return None
            
        current_task = state.current_plan.get_current_task()
        if not current_task:
            return None
            
        return {
            'task_id': current_task.id,
            'task_title': current_task.title,
            'task_status': current_task.status.value,
            'plan_id': state.current_plan.id,
            'plan_name': state.current_plan.name
        }
        
    def record_code_execution(self, code: str, result: Dict[str, Any], 
                            execution_time: float) -> bool:
        """코드 실행 기록"""
        try:
            state = self.manager.get_state()
            if not state.current_plan:
                return False
                
            current_task = state.current_plan.get_current_task()
            if not current_task:
                return False
                
            # 태스크에 메모 추가
            current_task.add_note(
                f"코드 실행: {len(code)} bytes, "
                f"실행시간: {execution_time:.2f}초, "
                f"결과: {'성공' if result.get('success') else '실패'}"
            )
            
            # 상태 저장
            self.manager._save_state()
            return True
            
        except Exception:
            return False
            
    def auto_progress_task(self, completion_note: str = "") -> Dict[str, Any]:
        """태스크 자동 진행"""
        try:
            # /next 명령 실행
            parsed = self.parser.parse(f"/next {completion_note}")
            return self.manager.execute(parsed)
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
            
    def get_workflow_status(self) -> Dict[str, Any]:
        """워크플로우 상태 조회"""
        try:
            parsed = self.parser.parse("/status")
            return self.manager.execute(parsed)
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
