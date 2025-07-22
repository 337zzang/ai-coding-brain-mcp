"""
Flow 시스템의 도메인 모델 정의
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum


class TaskStatus(Enum):
    """Task 상태 정의"""
    TODO = "todo"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    SKIP = "skip"
    ERROR = "error"


@dataclass
class Task:
    """Task 도메인 모델"""
    id: str
    name: str
    status: TaskStatus = TaskStatus.TODO
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (레거시 호환성)"""
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'context': self.context
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """딕셔너리에서 생성 (레거시 호환성)"""
        status = data.get('status', 'todo')
        if isinstance(status, str):
            status = TaskStatus(status)

        return cls(
            id=data['id'],
            name=data['name'],
            status=status,
            created_at=datetime.fromisoformat(data['created_at']) if isinstance(data.get('created_at'), str) else data.get('created_at', datetime.now()),
            updated_at=datetime.fromisoformat(data['updated_at']) if isinstance(data.get('updated_at'), str) else data.get('updated_at', datetime.now()),
            started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else None,
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            context=data.get('context', {})
        )


@dataclass
class Plan:
    """Plan 도메인 모델"""
    id: str
    name: str
    tasks: Dict[str, Task] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    completed: bool = False
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'name': self.name,
            'tasks': {tid: task.to_dict() for tid, task in self.tasks.items()},
            'created_at': self.created_at.isoformat(),
            'completed': self.completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Plan':
        """딕셔너리에서 생성"""
        tasks = {}
        tasks_data = data.get('tasks', {})
        if isinstance(tasks_data, dict):
            for tid, tdata in tasks_data.items():
                if isinstance(tdata, dict):
                    tasks[tid] = Task.from_dict(tdata)

        return cls(
            id=data['id'],
            name=data['name'],
            tasks=tasks,
            created_at=datetime.fromisoformat(data['created_at']) if isinstance(data.get('created_at'), str) else data.get('created_at', datetime.now()),
            completed=data.get('completed', False),
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None
        )


@dataclass
class Flow:
    """Flow 도메인 모델"""
    id: str
    name: str
    plans: Dict[str, Plan] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'name': self.name,
            'plans': {pid: plan.to_dict() for pid, plan in self.plans.items()},
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Flow':
        """딕셔너리에서 생성"""
        plans = {}
        plans_data = data.get('plans', {})
        if isinstance(plans_data, dict):
            for pid, pdata in plans_data.items():
                if isinstance(pdata, dict):
                    plans[pid] = Plan.from_dict(pdata)

        return cls(
            id=data['id'],
            name=data['name'],
            plans=plans,
            created_at=datetime.fromisoformat(data['created_at']) if isinstance(data.get('created_at'), str) else data.get('created_at', datetime.now()),
            updated_at=datetime.fromisoformat(data['updated_at']) if isinstance(data.get('updated_at'), str) else data.get('updated_at', datetime.now()),
            metadata=data.get('metadata', {})
        )
