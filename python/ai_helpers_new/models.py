"""
Flow Project v2 데이터 모델
Plan-Task 계층 구조를 위한 dataclass 정의
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from datetime import datetime
import uuid
import json


@dataclass
class Task:
    """태스크 모델"""
    id: str = field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    title: str = ""
    description: str = ""
    status: str = "todo"  # todo, in_progress, completed, cancelled
    plan_id: str = ""
    dependencies: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    assigned_to: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'Task':
        """딕셔너리에서 생성"""
        # None 값 처리
        if data.get('completed_at') == 'None':
            data['completed_at'] = None
        if data.get('assigned_to') == 'None':
            data['assigned_to'] = None
        return cls(**data)

    def update(self, **kwargs):
        """필드 업데이트"""
        allowed_fields = ['title', 'description', 'status', 'assigned_to', 'tags']
        for field_name, value in kwargs.items():
            if field_name in allowed_fields and hasattr(self, field_name):
                setattr(self, field_name, value)
        self.updated_at = datetime.now().isoformat()

        # 완료 시간 기록
        if kwargs.get('status') == 'completed' and not self.completed_at:
            self.completed_at = datetime.now().isoformat()


@dataclass
class Plan:
    """플랜 모델"""
    id: str = field(default_factory=lambda: f"plan_{uuid.uuid4().hex[:8]}")
    title: str = ""
    objective: str = ""
    status: str = "active"  # draft, active, completed, archived
    tasks: List[Task] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    priority: int = 0  # 0=normal, 1=high, 2=urgent
    progress: float = 0.0  # 0-100%
    milestones: List[Dict] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        data = asdict(self)
        # Task 객체들을 딕셔너리로 변환
        data['tasks'] = [task.to_dict() if isinstance(task, Task) else task 
                        for task in self.tasks]
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'Plan':
        """딕셔너리에서 생성"""
        # Task 객체 재생성
        tasks = []
        for task_data in data.get('tasks', []):
            if isinstance(task_data, dict):
                tasks.append(Task.from_dict(task_data))
            else:
                tasks.append(task_data)

        data['tasks'] = tasks

        # None 값 처리
        if data.get('completed_at') == 'None':
            data['completed_at'] = None

        return cls(**data)

    def add_task(self, task: Task):
        """태스크 추가"""
        task.plan_id = self.id
        self.tasks.append(task)
        self.updated_at = datetime.now().isoformat()
        self.update_progress()

    def remove_task(self, task_id: str) -> bool:
        """태스크 제거"""
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                self.tasks.pop(i)
                self.updated_at = datetime.now().isoformat()
                self.update_progress()
                return True
        return False

    def update_progress(self):
        """진행률 계산"""
        if not self.tasks:
            self.progress = 0.0
        else:
            completed = sum(1 for t in self.tasks if t.status == 'completed')
            self.progress = round((completed / len(self.tasks)) * 100, 2)

    def get_task(self, task_id: str) -> Optional[Task]:
        """ID로 태스크 찾기"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
