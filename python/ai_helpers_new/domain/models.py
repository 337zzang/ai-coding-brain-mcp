"""
Flow 시스템 도메인 모델
Phase 2 구조 개선 - 단순화된 모델
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional
import uuid


class TaskStatus(str, Enum):
    """Task 상태 - 3단계로 단순화"""
    TODO = 'todo'
    DOING = 'doing'  # in_progress, planning, reviewing 통합
    DONE = 'done'
    ARCHIVED = 'archived'

    @classmethod
    def from_legacy(cls, status: str) -> 'TaskStatus':
        """레거시 5단계 상태를 3단계로 변환"""
        mapping = {
            'todo': cls.TODO,
            'planning': cls.DOING,
            'in_progress': cls.DOING,
            'reviewing': cls.DOING,
            'completed': cls.DONE,
            'done': cls.DONE,
            'archived': cls.ARCHIVED
        }
        return mapping.get(status, cls.TODO)


def create_flow_id(name: str = None) -> str:
    """Flow ID 생성"""
    if name and not name.startswith('flow_'):
        return name  # 프로젝트명 그대로 사용
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    short_id = str(uuid.uuid4())[:6]
    return f"flow_{timestamp}_{short_id}"


def create_plan_id(flow_id: str = None) -> str:
    """Plan ID 생성"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    short_id = str(uuid.uuid4())[:6]
    return f"plan_{timestamp}_{short_id}"


def create_task_id(plan_id: str = None) -> str:
    """Task ID 생성"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    short_id = str(uuid.uuid4())[:6]
    return f"task_{timestamp}_{short_id}"


@dataclass
class Task:
    """Task 모델 - Context 통합"""
    id: str
    name: str
    description: str = ""
    status: TaskStatus = TaskStatus.TODO
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)  # Context 통합

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status.value,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'context': self.context
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """딕셔너리에서 생성"""
        data = data.copy()
        if 'status' in data:
            # 레거시 상태 변환
            data['status'] = TaskStatus.from_legacy(data['status'])
        return cls(**data)

    def start(self):
        """Task 시작"""
        self.status = TaskStatus.DOING
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def complete(self):
        """Task 완료"""
        self.status = TaskStatus.DONE
        self.completed_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def add_action(self, action: str, data: Any = None):
        """Context에 액션 추가"""
        if 'actions' not in self.context:
            self.context['actions'] = []
        self.context['actions'].append({
            'action': action,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': data
        })
        self.updated_at = datetime.now(timezone.utc).isoformat()


@dataclass
class Plan:
    """Plan 모델"""
    id: str
    name: str
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    tasks: Dict[str, Task] = field(default_factory=dict)
    status: str = 'active'  # active, completed
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'completed_at': self.completed_at,
            'tasks': {tid: task.to_dict() for tid, task in self.tasks.items()},
            'status': self.status,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Plan':
        """딕셔너리에서 생성"""
        data = data.copy()
        # tasks 변환
        if 'tasks' in data:
            tasks = {}
            for tid, tdata in data['tasks'].items():
                if isinstance(tdata, dict):
                    tasks[tid] = Task.from_dict(tdata)
                else:
                    tasks[tid] = tdata
            data['tasks'] = tasks
        return cls(**data)

    def add_task(self, name: str, description: str = "") -> Task:
        """Task 추가"""
        task_id = create_task_id(self.id)
        task = Task(id=task_id, name=name, description=description)
        self.tasks[task_id] = task
        self.updated_at = datetime.now(timezone.utc).isoformat()
        return task

    def is_completed(self) -> bool:
        """모든 Task가 완료되었는지 확인"""
        if not self.tasks:
            return False
        return all(task.status == TaskStatus.DONE for task in self.tasks.values())

    def complete(self):
        """Plan 완료"""
        self.status = 'completed'
        self.completed_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = datetime.now(timezone.utc).isoformat()


@dataclass
class Flow:
    """Flow 모델"""
    id: str
    name: str
    project: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    plans: Dict[str, Plan] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    archived: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'name': self.name,
            'project': self.project,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'plans': {pid: plan.to_dict() for pid, plan in self.plans.items()},
            'metadata': self.metadata,
            'archived': self.archived
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Flow':
        """딕셔너리에서 생성"""
        data = data.copy()
        # plans 변환
        if 'plans' in data:
            plans = {}
            for pid, pdata in data['plans'].items():
                if isinstance(pdata, dict):
                    plans[pid] = Plan.from_dict(pdata)
                else:
                    plans[pid] = pdata
            data['plans'] = plans
        return cls(**data)

    def add_plan(self, name: str, description: str = "") -> Plan:
        """Plan 추가"""
        plan_id = create_plan_id(self.id)
        plan = Plan(id=plan_id, name=name, description=description)
        self.plans[plan_id] = plan
        self.updated_at = datetime.now(timezone.utc).isoformat()
        return plan

    def get_all_tasks(self) -> List[Task]:
        """모든 Task 목록"""
        tasks = []
        for plan in self.plans.values():
            tasks.extend(plan.tasks.values())
        return tasks

    def archive(self):
        """Flow 아카이브"""
        self.archived = True
        self.updated_at = datetime.now(timezone.utc).isoformat()
