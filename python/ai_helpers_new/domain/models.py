# models.py
'''
Flow 시스템 도메인 모델
o3 분석 결과를 반영한 개선 버전
'''

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional, List, Any
from enum import Enum
import json


class TaskStatus(str, Enum):
    """Task 상태"""
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
    status: str = TaskStatus.TODO.value
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'context': self.context
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Task:
        """딕셔너리에서 생성"""
        return cls(
            id=data['id'],
            name=data['name'],
            status=data.get('status', TaskStatus.TODO.value),
            created_at=data.get('created_at', datetime.now(timezone.utc).isoformat()),
            updated_at=data.get('updated_at', datetime.now(timezone.utc).isoformat()),
            started_at=data.get('started_at'),
            completed_at=data.get('completed_at'),
            context=data.get('context', {})
        )


@dataclass
class Plan:
    """Plan 도메인 모델"""
    id: str
    name: str
    tasks: Dict[str, Task] = field(default_factory=dict)
    completed: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'name': self.name,
            'tasks': {tid: task.to_dict() for tid, task in self.tasks.items()},
            'completed': self.completed,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Plan:
        """딕셔너리에서 생성"""
        tasks = {}
        for tid, tdata in data.get('tasks', {}).items():
            if isinstance(tdata, dict):
                tasks[tid] = Task.from_dict(tdata)

        return cls(
            id=data['id'],
            name=data['name'],
            tasks=tasks,
            completed=data.get('completed', False),
            created_at=data.get('created_at', datetime.now(timezone.utc).isoformat()),
            updated_at=data.get('updated_at', datetime.now(timezone.utc).isoformat()),
            metadata=data.get('metadata', {})
        )


@dataclass
class Flow:
    """Flow 도메인 모델"""
    id: str
    name: str
    plans: Dict[str, Plan] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    project: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'name': self.name,
            'plans': {pid: plan.to_dict() for pid, plan in self.plans.items()},
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'metadata': self.metadata,
            'project': self.project
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Flow:
        """딕셔너리에서 생성"""
        plans = {}
        for pid, pdata in data.get('plans', {}).items():
            if isinstance(pdata, dict):
                plans[pid] = Plan.from_dict(pdata)

        return cls(
            id=data['id'],
            name=data['name'],
            plans=plans,
            created_at=data.get('created_at', datetime.now(timezone.utc).isoformat()),
            updated_at=data.get('updated_at', datetime.now(timezone.utc).isoformat()),
            metadata=data.get('metadata', {}),
            project=data.get('project')
        )


# 헬퍼 함수들
def validate_status(status: str) -> bool:
    """상태 값 검증"""
    return status in [s.value for s in TaskStatus]


def create_flow_id() -> str:
    """Flow ID 생성"""
    from datetime import datetime
    import random
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    random_hex = f"{random.randint(0, 0xFFFFFF):06x}"
    return f"flow_{timestamp}_{random_hex}"


def create_plan_id() -> str:
    """Plan ID 생성"""
    from datetime import datetime
    import random
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    random_hex = f"{random.randint(0, 0xFFFFFF):06x}"
    return f"plan_{timestamp}_{random_hex}"


def create_task_id() -> str:
    """Task ID 생성"""
    from datetime import datetime
    import random
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    random_hex = f"{random.randint(0, 0xFFFFFF):06x}"
    return f"task_{timestamp}_{random_hex}"
