"""
WorkflowManager - 중앙 상태 관리자
모든 워크플로우 관련 로직을 중앙에서 관리
"""
import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from .models import Plan, Phase, Task, WorkflowState, TaskStatus, PhaseStatus
from .decorators import autosave


class WorkflowManager:
    """워크플로우 중앙 관리자"""
    
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.state_file = Path(f"memory/states/{project_name}_workflow.json")
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 상태 로드 또는 초기화
        self.state = self._load_state()
        
    def _load_state(self) -> WorkflowState:
        """상태 로드"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return WorkflowState(**data)
            except Exception as e:
                print(f"⚠️ 상태 로드 실패: {e}")
        
        # 새 상태 생성
        return WorkflowState(project_name=self.project_name)
    
    def _save_state(self) -> None:
        """상태 저장"""
        self.state.update()
        data = self.state.model_dump()
        
        # datetime 객체를 문자열로 변환
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: convert_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_datetime(item) for item in obj]
            return obj
        
        data = convert_datetime(data)
        
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    # ============= Plan 관련 메서드 =============
    
    @autosave
    def create_plan(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """새 계획 생성"""
        if self.state.plan:
            return {
                'success': False,
                'message': '이미 활성화된 계획이 있습니다',
                'data': None
            }
        
        plan = Plan(name=name, description=description)
        self.state.plan = plan
        
        return {
            'success': True,
            'message': f'계획 "{name}" 생성 완료',
            'data': {
                'id': plan.id,
                'name': plan.name,
                'description': plan.description
            }
        }
    
    @autosave
    def update_plan(self, name: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        """계획 정보 수정"""
        if not self.state.plan:
            return {
                'success': False,
                'message': '활성화된 계획이 없습니다',
                'data': None
            }
        
        if name:
            self.state.plan.name = name
        if description:
            self.state.plan.description = description
        
        return {
            'success': True,
            'message': '계획 정보 수정 완료',
            'data': {
                'id': self.state.plan.id,
                'name': self.state.plan.name,
                'description': self.state.plan.description
            }
        }
    
    def get_plan(self) -> Optional[Plan]:
        """현재 계획 조회"""
        return self.state.plan
    
    # ============= Phase 관련 메서드 =============
    
    @autosave
    def add_phase(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Phase 추가"""
        if not self.state.plan:
            return {
                'success': False,
                'message': '계획을 먼저 생성해주세요',
                'data': None
            }
        
        phase = Phase(name=name, description=description)
        self.state.plan.add_phase(phase)
        
        return {
            'success': True,
            'message': f'Phase "{name}" 추가 완료',
            'data': {
                'id': phase.id,
                'name': phase.name,
                'description': phase.description
            }
        }
    
    def get_current_phase(self) -> Optional[Phase]:
        """현재 Phase 조회"""
        if not self.state.plan:
            return None
        return self.state.plan.get_current_phase()
    
    # ============= Task 관련 메서드 =============
    
    @autosave
    def add_task(self, phase_name: str, title: str, description: Optional[str] = None,
                 estimated_hours: float = 1.0) -> Dict[str, Any]:
        """작업 추가"""
        if not self.state.plan:
            return {
                'success': False,
                'message': '계획을 먼저 생성해주세요',
                'data': None
            }
        
        # Phase 찾기
        phase = None
        for p in self.state.plan.phases:
            if p.name == phase_name:
                phase = p
                break
        
        if not phase:
            return {
                'success': False,
                'message': f'Phase "{phase_name}"을 찾을 수 없습니다',
                'data': None
            }
        
        task = Task(
            phase_id=phase.id,
            title=title,
            description=description,
            estimated_hours=estimated_hours
        )
        phase.add_task(task)
        
        return {
            'success': True,
            'message': f'작업 "{title}" 추가 완료',
            'data': {
                'id': task.id,
                'phase_name': phase_name,
                'title': task.title,
                'description': task.description,
                'status': task.status.value
            }
        }
    
    def get_current_task(self) -> Optional[Task]:
        """현재 작업 조회"""
        if not self.state.plan:
            return None
        return self.state.plan.get_current_task()
    
    @autosave
    def start_task(self, task_id: str) -> Dict[str, Any]:
        """작업 시작"""
        if not self.state.plan:
            return {
                'success': False,
                'message': '활성화된 계획이 없습니다',
                'data': None
            }
        
        # 작업 찾기
        task = None
        for phase in self.state.plan.phases:
            for t in phase.tasks:
                if t.id == task_id:
                    task = t
                    break
        
        if not task:
            return {
                'success': False,
                'message': '작업을 찾을 수 없습니다',
                'data': None
            }
        
        if not task.start():
            return {
                'success': False,
                'message': f'작업을 시작할 수 없습니다 (현재 상태: {task.status.value})',
                'data': None
            }
        
        self.state.plan.current_task_id = task.id
        
        # Phase 상태 업데이트
        for phase in self.state.plan.phases:
            if phase.id == task.phase_id:
                phase.update_status()
                self.state.plan.current_phase_id = phase.id
                break
        
        return {
            'success': True,
            'message': f'작업 "{task.title}" 시작',
            'data': {
                'id': task.id,
                'title': task.title,
                'status': task.status.value
            }
        }
    
    @autosave
    def complete_task(self, task_id: Optional[str] = None, content: Optional[str] = None) -> Dict[str, Any]:
        """작업 완료"""
        if not self.state.plan:
            return {
                'success': False,
                'message': '활성화된 계획이 없습니다',
                'data': None
            }
        
        # 현재 작업 사용
        if not task_id:
            task_id = self.state.plan.current_task_id
        
        if not task_id:
            return {
                'success': False,
                'message': '완료할 작업이 없습니다',
                'data': None
            }
        
        # 작업 찾기
        task = None
        phase = None
        for p in self.state.plan.phases:
            for t in p.tasks:
                if t.id == task_id:
                    task = t
                    phase = p
                    break
        
        if not task:
            return {
                'success': False,
                'message': '작업을 찾을 수 없습니다',
                'data': None
            }
        
        if not task.complete(content):
            return {
                'success': False,
                'message': f'작업을 완료할 수 없습니다 (현재 상태: {task.status.value})',
                'data': None
            }
        
        # 현재 작업 해제
        if self.state.plan.current_task_id == task_id:
            self.state.plan.current_task_id = None
        
        # Phase 상태 업데이트
        phase.update_status()
        
        return {
            'success': True,
            'message': f'작업 "{task.title}" 완료',
            'data': {
                'id': task.id,
                'title': task.title,
                'content': task.content,
                'status': task.status.value
            }
        }
    
    # ============= 워크플로우 관련 메서드 =============
    
    def get_next_task(self) -> Optional[Task]:
        """다음 작업 찾기"""
        if not self.state.plan:
            return None
        return self.state.plan.get_next_task()
    
    @autosave
    def start_next_task(self) -> Dict[str, Any]:
        """다음 작업 시작"""
        next_task = self.get_next_task()
        if not next_task:
            return {
                'success': False,
                'message': '모든 작업이 완료되었습니다',
                'data': None
            }
        
        return self.start_task(next_task.id)
    
    @autosave
    def advance_to_next_step(self, content: Optional[str] = None) -> Dict[str, Any]:
        """현재 작업 완료 후 다음 작업 시작"""
        result = {
            'success': False,
            'message': '',
            'completed_task': None,
            'next_task': None
        }
        
        # 현재 작업 완료
        if self.state.plan and self.state.plan.current_task_id:
            complete_result = self.complete_task(content=content)
            if complete_result['success']:
                result['completed_task'] = complete_result['data']
            else:
                result['message'] = complete_result['message'] + '. '
        
        # 다음 작업 시작
        next_result = self.start_next_task()
        if next_result['success']:
            result['success'] = True
            result['next_task'] = next_result['data']
            result['message'] += next_result['message']
        else:
            result['success'] = True  # 작업이 모두 완료된 것도 성공
            result['message'] += next_result['message']
        
        return result
    
    # ============= 통계 및 조회 메서드 =============
    
    def get_statistics(self) -> Dict[str, Any]:
        """통계 정보"""
        if not self.state.plan:
            return {
                'total_tasks': 0,
                'completed_tasks': 0,
                'pending_tasks': 0,
                'in_progress_tasks': 0,
                'progress': 0.0
            }
        
        all_tasks = self.state.plan.get_all_tasks()
        
        return {
            'total_tasks': len(all_tasks),
            'completed_tasks': sum(1 for t in all_tasks if t.status == TaskStatus.COMPLETED),
            'pending_tasks': sum(1 for t in all_tasks if t.status == TaskStatus.PENDING),
            'in_progress_tasks': sum(1 for t in all_tasks if t.status == TaskStatus.IN_PROGRESS),
            'progress': self.state.plan.get_progress(),
            'total_phases': len(self.state.plan.phases),
            'completed_phases': sum(1 for p in self.state.plan.phases if p.status == PhaseStatus.COMPLETED)
        }
    
    def get_task_list(self) -> List[Dict[str, Any]]:
        """전체 작업 목록"""
        if not self.state.plan:
            return []
        
        tasks = []
        for phase in self.state.plan.phases:
            for task in phase.tasks:
                tasks.append({
                    'id': task.id,
                    'phase_name': phase.name,
                    'title': task.title,
                    'description': task.description,
                    'status': task.status.value,
                    'is_current': task.id == self.state.plan.current_task_id
                })
        
        return tasks


# 싱글톤 인스턴스
_workflow_manager: Optional[WorkflowManager] = None


def get_workflow_manager(project_name: Optional[str] = None) -> WorkflowManager:
    """WorkflowManager 인스턴스 조회"""
    global _workflow_manager
    
    if project_name:
        _workflow_manager = WorkflowManager(project_name)
    
    if not _workflow_manager:
        # 기본 프로젝트명 사용
        _workflow_manager = WorkflowManager("ai-coding-brain-mcp")
    
    return _workflow_manager
