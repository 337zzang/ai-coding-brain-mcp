"""
워크플로우 데이터 모델
- Plan: 작업 계획
- Task: 개별 작업 (execution_plan 포함)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid

class TaskStatus(Enum):
    """작업 상태"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    APPROVED = "approved"  # 실행 계획 승인됨
    PENDING = "pending"    # 실행 계획 대기 중

class ApprovalStatus(Enum):
    """승인 상태"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"

@dataclass
class ExecutionPlan:
    """작업 실행 계획"""
    steps: List[str] = field(default_factory=list)
    estimated_time: str = ""
    tools: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    ai_provider: str = "gemini"  # 또는 "gpt"
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'steps': self.steps,
            'estimated_time': self.estimated_time,
            'tools': self.tools,
            'risks': self.risks,
            'success_criteria': self.success_criteria,
            'created_at': self.created_at,
            'ai_provider': self.ai_provider
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionPlan':
        """딕셔너리에서 생성"""
        return cls(
            steps=data.get('steps', []),
            estimated_time=data.get('estimated_time', ''),
            tools=data.get('tools', []),
            risks=data.get('risks', []),
            success_criteria=data.get('success_criteria', []),
            created_at=data.get('created_at', datetime.now().isoformat()),
            ai_provider=data.get('ai_provider', 'gemini')
        )

@dataclass
class Task:
    """개별 작업"""
    id: str = field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    title: str = ""
    description: str = ""
    status: TaskStatus = TaskStatus.TODO
    approval_status: Optional[ApprovalStatus] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    started_at: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    assignee: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    completion_notes: str = ""
    approval_notes: str = ""
    execution_plan: Optional[ExecutionPlan] = None
    result: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status.value if isinstance(self.status, TaskStatus) else self.status,
            'approval_status': self.approval_status.value if self.approval_status else None,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'completed_at': self.completed_at,
            'started_at': self.started_at,
            'dependencies': self.dependencies,
            'assignee': self.assignee,
            'tags': self.tags,
            'completion_notes': self.completion_notes,
            'approval_notes': self.approval_notes,
            'execution_plan': self.execution_plan.to_dict() if self.execution_plan else None,
            'result': self.result
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """딕셔너리에서 생성"""
        task = cls(
            id=data.get('id', f"task_{uuid.uuid4().hex[:8]}"),
            title=data.get('title', ''),
            description=data.get('description', ''),
            created_at=data.get('created_at', datetime.now().isoformat()),
            updated_at=data.get('updated_at', datetime.now().isoformat()),
            completed_at=data.get('completed_at'),
            started_at=data.get('started_at'),
            dependencies=data.get('dependencies', []),
            assignee=data.get('assignee'),
            tags=data.get('tags', []),
            completion_notes=data.get('completion_notes', ''),
            approval_notes=data.get('approval_notes', ''),
            result=data.get('result')
        )
        
        # status 처리
        status_value = data.get('status', 'todo')
        try:
            task.status = TaskStatus(status_value)
        except ValueError:
            # 이전 버전 호환성
            status_map = {
                'pending': TaskStatus.PENDING,
                'approved': TaskStatus.APPROVED,
                'todo': TaskStatus.TODO,
                'in_progress': TaskStatus.IN_PROGRESS,
                'completed': TaskStatus.COMPLETED
            }
            task.status = status_map.get(status_value, TaskStatus.TODO)
        
        # approval_status 처리
        if data.get('approval_status'):
            try:
                task.approval_status = ApprovalStatus(data['approval_status'])
            except ValueError:
                task.approval_status = None
        
        # execution_plan 처리
        if data.get('execution_plan'):
            task.execution_plan = ExecutionPlan.from_dict(data['execution_plan'])
            
        return task

@dataclass
class Plan:
    """작업 계획"""
    id: str = field(default_factory=lambda: f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    name: str = ""
    description: str = ""
    tasks: List[Task] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "active"  # active, completed, archived
    tags: List[str] = field(default_factory=list)
    current_task_index: int = 0  # 현재 작업 인덱스
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'tasks': [task.to_dict() for task in self.tasks],
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'status': self.status,
            'tags': self.tags,
            'current_task_index': self.current_task_index
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Plan':
        """딕셔너리에서 생성"""
        plan = cls(
            id=data.get('id', f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            name=data.get('name', ''),
            description=data.get('description', ''),
            created_at=data.get('created_at', datetime.now().isoformat()),
            updated_at=data.get('updated_at', datetime.now().isoformat()),
            status=data.get('status', 'active'),
            tags=data.get('tags', []),
            current_task_index=data.get('current_task_index', 0)
        )
        
        # tasks 처리
        tasks_data = data.get('tasks', [])
        for task_data in tasks_data:
            if isinstance(task_data, dict):
                plan.tasks.append(Task.from_dict(task_data))
                
        return plan
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """ID로 작업 찾기"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def get_current_task(self) -> Optional[Task]:
        """현재 진행 중인 작업 반환"""
        for task in self.tasks:
            if task.status == TaskStatus.IN_PROGRESS:
                return task
        
        # 진행 중인 작업이 없으면 첫 번째 미완료 작업
        for task in self.tasks:
            if task.status in [TaskStatus.TODO, TaskStatus.PENDING, TaskStatus.APPROVED]:
                return task
                
        return None
    
    def get_next_task(self) -> Optional[Task]:
        """다음 작업 반환"""
        if self.current_task_index + 1 < len(self.tasks):
            return self.tasks[self.current_task_index + 1]
        return None
    
    def get_progress(self) -> Dict[str, Any]:
        """진행 상황 계산"""
        total = len(self.tasks)
        completed = len([t for t in self.tasks if t.status == TaskStatus.COMPLETED])
        
        return {
            'total': total,
            'completed': completed,
            'percentage': round((completed / total * 100) if total > 0 else 0, 1),
            'remaining': total - completed
        }

    def add_task(self, title: str, description: str = "") -> 'Task':
        """태스크 추가"""
        task = Task(title=title, description=description)
        self.tasks.append(task)
        return task

    def complete_task(self, task_id: str, notes: str = "") -> bool:
        """태스크 완료 처리"""
        for task in self.tasks:
            if task.id == task_id:
                task.status = 'completed'
                task.completed_at = datetime.now().isoformat()
                task.completion_notes = notes
                return True
        return False

    def get_task_by_index(self, index: int) -> Optional['Task']:
        """인덱스로 태스크 가져오기"""
        if 0 <= index < len(self.tasks):
            return self.tasks[index]
        return None

    def move_to_next_task(self) -> bool:
        """다음 태스크로 이동"""
        if self.current_task_index < len(self.tasks) - 1:
            self.current_task_index += 1
            return True
        return False
