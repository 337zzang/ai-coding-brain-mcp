"""
핵심 도메인 모델 정의
외부 의존성 없음
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

@dataclass
class Task:
    id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    priority: int = 0

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'priority': self.priority
        }

@dataclass
class Plan:
    id: str
    name: str
    description: str = ""
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tasks: Dict[str, Task] = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'task_count': len(self.tasks),
            'metadata': self.metadata
        }

    def add_task(self, task: Task) -> None:
        """Task 추가"""
        self.tasks[task.id] = task
        self.updated_at = datetime.now()

    def get_task(self, task_id: str) -> Optional[Task]:
        """Task 조회"""
        return self.tasks.get(task_id)

    def remove_task(self, task_id: str) -> bool:
        """Task 제거"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.updated_at = datetime.now()
            return True
        return False
