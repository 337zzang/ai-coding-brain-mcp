"""
워크플로우 관리자 - 작업 계획, 승인, 실행 관리
"""
import json
from pathlib import Path
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from workflow.models import Plan, Task, TaskStatus, ApprovalStatus, ExecutionPlan
import uuid

from utils.io_helpers import write_json
from utils.git_utils import get_git_status_info

class WorkflowManager:
    """워크플로우 관리 클래스"""
    
    def __init__(self, data_file: str = "memory/workflow.json"):
        self.data_file = data_file
        self.plans: List[Plan] = []
        self.current_plan: Optional[Plan] = None
        self.load_data()
    
    def load_data(self):
        """데이터 파일에서 계획 로드"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # 디버깅을 위한 타입 확인
                    if not isinstance(data, dict):
                        print(f"⚠️ 데이터가 dict가 아닙니다: {type(data)}")
                        self.plans = []
                        return
                    
                    # plans 로드
                    plans_data = data.get('plans', [])
                    if not isinstance(plans_data, list):
                        print(f"⚠️ plans가 list가 아닙니다: {type(plans_data)}")
                        self.plans = []
                        return
                    
                    self.plans = []
                    for i, p in enumerate(plans_data):
                        try:
                            if not isinstance(p, dict):
                                print(f"⚠️ plan[{i}]이 dict가 아닙니다: {type(p)}")
                                continue
                            self.plans.append(Plan.from_dict(p))
                        except Exception as e:
                            print(f"⚠️ plan[{i}] 로드 실패: {e}")
                            continue
                    
                    # current_plan 설정
                    if data.get('current_plan_id'):
                        self.current_plan = self._find_plan(data['current_plan_id'])
            except Exception as e:
                print(f"⚠️ 데이터 로드 실패: {e}")
                self.plans = []
    
    def save_data(self):
        """데이터를 파일에 저장"""
        data = {
            'plans': [plan.to_dict() for plan in self.plans],
            'current_plan_id': self.current_plan.id if self.current_plan else None,
            'last_updated': datetime.now().isoformat()
        }
        write_json(data, Path(self.data_file))
    
    def _find_plan(self, plan_id: str) -> Optional[Plan]:
        """ID로 계획 찾기"""
        for plan in self.plans:
            if plan.id == plan_id:
                return plan
        return None
    
    def create_plan(self, name: str, description: str, reset: bool = False) -> Plan:
        """새 계획 생성"""
        if reset:
            self.plans = []
            self.current_plan = None
        
        plan = Plan(
            id=str(uuid.uuid4()),
            name=name,
            description=description
        )
        self.plans.append(plan)
        self.current_plan = plan
        self.save_data()
        return plan
    
    def add_task(self, title: str, description: str) -> Task:
        """현재 계획에 작업 추가"""
        if not self.current_plan:
            raise ValueError("현재 활성 계획이 없습니다. 먼저 /plan으로 계획을 생성하세요.")
        
        task = Task(
            id=str(uuid.uuid4()),
            title=title,
            description=description
        )
        self.current_plan.tasks.append(task)
        self.save_data()
        return task
    
    def create_task_plan(self, task_id: str, plan: ExecutionPlan) -> Task:
        """작업에 상세 계획 추가"""
        if not self.current_plan:
            raise ValueError("현재 활성 계획이 없습니다.")
        
        for task in self.current_plan.tasks:
            if task.id == task_id:
                task.execution_plan = plan
                task.status = TaskStatus.PENDING
                self.save_data()
                return task
        
        raise ValueError(f"작업 ID {task_id}를 찾을 수 없습니다.")
    
    def approve_task(self, task_id: str, approved: bool, notes: str = "") -> Task:
        """작업 계획 승인/거부"""
        if not self.current_plan:
            raise ValueError("현재 활성 계획이 없습니다.")
        
        for task in self.current_plan.tasks:
            if task.id == task_id:
                task.approval_status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
                task.approval_notes = notes
                if approved:
                    task.status = TaskStatus.APPROVED
                self.save_data()
                return task
        
        raise ValueError(f"작업 ID {task_id}를 찾을 수 없습니다.")
    
    def start_task(self, task_id: str) -> Task:
        """작업 시작"""
        if not self.current_plan:
            raise ValueError("현재 활성 계획이 없습니다.")
        
        for task in self.current_plan.tasks:
            if task.id == task_id:
                if task.approval_status != ApprovalStatus.APPROVED:
                    raise ValueError("승인되지 않은 작업은 시작할 수 없습니다.")
                task.status = TaskStatus.IN_PROGRESS
                task.started_at = datetime.now().isoformat()
                self.save_data()
                return task
        
        raise ValueError(f"작업 ID {task_id}를 찾을 수 없습니다.")
    
    def complete_task(self, task_id: str, result: Dict[str, Any]) -> Task:
        """작업 완료 및 결과 저장"""
        if not self.current_plan:
            raise ValueError("현재 활성 계획이 없습니다.")
        
        for i, task in enumerate(self.current_plan.tasks):
            if task.id == task_id:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now().isoformat()
                task.result = result
                
                # 다음 작업으로 인덱스 이동
                if i == self.current_plan.current_task_index:
                    self.current_plan.current_task_index += 1
                
                self.save_data()
                return task
        
        raise ValueError(f"작업 ID {task_id}를 찾을 수 없습니다.")
    
    def get_current_task(self) -> Optional[Task]:
        """현재 작업 반환"""
        if self.current_plan:
            return self.current_plan.get_current_task()
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """현재 상태 반환 (Git 정보 포함)"""
        # Git 상태 정보 수집
        git_info = get_git_status_info()
        
        if not self.current_plan:
            return {
                'status': 'no_active_plan',
                'message': '활성 계획이 없습니다. /plan으로 새 계획을 시작하세요.',
                'git': git_info
            }
        
        current_task = self.get_current_task()
        completed_tasks = [t for t in self.current_plan.tasks if t.status == TaskStatus.COMPLETED]
        remaining_tasks = [t for t in self.current_plan.tasks if t.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]]
        
        # 작업 목록 생성 (상태 아이콘 포함)
        all_tasks = []
        for i, task in enumerate(self.current_plan.tasks):
            if task.status == TaskStatus.COMPLETED:
                status_icon = "✅"
            elif task.status == TaskStatus.IN_PROGRESS:
                status_icon = "🔄"
            elif task.status == TaskStatus.BLOCKED:
                status_icon = "🚫"
            elif task.status == TaskStatus.CANCELLED:
                status_icon = "❌"
            else:
                status_icon = "⬜"
            
            task_line = f"{status_icon} {task.title}"
            if task == current_task:
                task_line = f"👉 {task_line}"
            all_tasks.append(task_line)
        
        return {
            'plan': {
                'name': self.current_plan.name,
                'description': self.current_plan.description,
                'total_tasks': len(self.current_plan.tasks),
                'completed_tasks': len(completed_tasks),
                'progress': f"{len(completed_tasks)}/{len(self.current_plan.tasks)}",
                'progress_percent': (len(completed_tasks) / len(self.current_plan.tasks) * 100) if self.current_plan.tasks else 0
            },
            'current_task': {
                'title': current_task.title,
                'description': current_task.description,
                'status': current_task.status.value,
                'approval': current_task.approval_status.value if current_task.approval_status else 'none'
            } if current_task else None,
            'next_tasks': [
                {'title': t.title, 'status': t.status.value}
                for t in self.current_plan.tasks[self.current_plan.current_task_index+1:self.current_plan.current_task_index+3]
            ],
            'all_tasks': all_tasks,
            'remaining_tasks': len(remaining_tasks),
            'git': git_info
        }
    
    def get_history(self, plan_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """작업 이력 조회"""
        if plan_id:
            plan = self._find_plan(plan_id)
            if not plan:
                return []
            plans = [plan]
        else:
            plans = self.plans
        
        history = []
        for plan in plans:
            for task in plan.tasks:
                if task.status == TaskStatus.COMPLETED and task.result:
                    history.append({
                        'plan': plan.name,
                        'task': task.title,
                        'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                        'summary': task.result.summary,
                        'details': task.result.details
                    })
        
        return history