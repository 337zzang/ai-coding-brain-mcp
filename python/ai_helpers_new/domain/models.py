"""
Domain Models - Ultra Simple Flow System
Flow 개념이 제거되고 Plan과 Task만 남은 모델
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid


class TaskStatus(Enum):
    """Task 상태"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Task 모델"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    status: TaskStatus = TaskStatus.TODO
    priority: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    assignee: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "assignee": self.assignee,
            "tags": self.tags,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """딕셔너리에서 생성"""
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = TaskStatus(data['status'])
        return cls(**data)


@dataclass
class Plan:
    """Plan 모델 (Flow 개념 제거)"""
    id: str = field(default_factory=lambda: f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}")
    name: str = ""
    description: str = ""
    status: str = "active"
    priority: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    start_date: Optional[str] = None
    due_date: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    tasks: Dict[str, Task] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # AI가 사용할 수 있는 추가 필드들
    context: Dict[str, Any] = field(default_factory=dict)  # AI 컨텍스트 정보

    def add_task(self, task: Task) -> None:
        """Task 추가"""
        self.tasks[task.id] = task
        self.updated_at = datetime.now().isoformat()

    def get_task(self, task_id: str) -> Optional[Task]:
        """Task 조회"""
        return self.tasks.get(task_id)

    def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """Task 상태 업데이트"""
        if task_id in self.tasks:
            self.tasks[task_id].status = status
            self.tasks[task_id].updated_at = datetime.now().isoformat()
            if status == TaskStatus.DONE:
                self.tasks[task_id].completed_at = datetime.now().isoformat()
            self.updated_at = datetime.now().isoformat()
            return True
        return False

    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """상태별 Task 목록"""
        return [task for task in self.tasks.values() if task.status == status]

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "start_date": self.start_date,
            "due_date": self.due_date,
            "tags": self.tags,
            "tasks": {tid: task.to_dict() for tid, task in self.tasks.items()},
            "metadata": self.metadata,
            "context": self.context
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Plan':
        """딕셔너리에서 생성"""
        tasks_data = data.pop('tasks', {})
        plan = cls(**data)

        # Task 복원
        for task_id, task_data in tasks_data.items():
            if isinstance(task_data, dict):
                task = Task.from_dict(task_data)
                plan.tasks[task_id] = task

        return plan
