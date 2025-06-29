"""
AI Coding Brain Pydantic 데이터 모델
버전: 1.0
작성일: 2025-06-24

이 모듈은 프로젝트의 모든 데이터 구조를 Pydantic 모델로 정의합니다.
타입 안정성과 자동 검증을 제공하여 런타임 오류를 방지합니다.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import json
import uuid

class TaskStatus(str, Enum):
    """작업의 상태를 정의하는 Enum"""
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    BLOCKED = 'blocked'
    CANCELED = 'canceled'

class BaseModelWithConfig(BaseModel):
    """
    JSON 직렬화와 Path 객체 처리를 위한 기본 모델
    """

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {Path: str, datetime: lambda v: v.isoformat() if v else None}

    def model_dump(self, **kwargs):
        """Path 객체를 문자열로 변환하여 반환"""
        d = super().model_dump(**kwargs)
        return self._convert_paths_to_str(d)

    def dict(self, **kwargs):
        """하위 호환성을 위한 별칭 (deprecated)"""
        return self.model_dump(**kwargs)

    def _convert_paths_to_str(self, obj):
        """재귀적으로 Path 객체를 문자열로 변환"""
        if isinstance(obj, dict):
            return {k: self._convert_paths_to_str(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_paths_to_str(item) for item in obj]
        elif isinstance(obj, Path):
            return str(obj)
        return obj

class Task(BaseModelWithConfig):
    """작업(Task) 모델"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str = ''
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    priority: str = Field(default='medium', pattern='^(high|medium|low)$')
    phase_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    completed: bool = False
    subtasks: List[str] = Field(default_factory=list)
    work_summary: Optional[Dict[str, Any]] = None
    content: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    related_files: List[str] = Field(default_factory=list)
    state_history: List[Dict[str, Any]] = Field(default_factory=list)
    blocking_reason: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    blocks: List[str] = Field(default_factory=list)
    auto_generated: bool = False
    wisdom_hints: List[str] = Field(default_factory=list)
    context_data: Dict[str, Any] = Field(default_factory=dict)

    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['pending', 'in_progress', 'completed', 'blocked']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of {valid_statuses}')
        return v

    @validator('priority')
    def validate_priority(cls, v):
        valid_priorities = ['high', 'medium', 'low']
        if v not in valid_priorities:
            raise ValueError(f'Priority must be one of {valid_priorities}')
        return v

    def mark_completed(self, content: Optional[str]=None):
        """작업을 완료 상태로 표시하고 content 기록"""
        self.completed = True
        self.status = 'completed'
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()
        if content:
            self.content = content

    def mark_started(self):
        """작업을 시작 상태로 표시"""
        self.status = 'in_progress'
        self.started_at = datetime.now()

    def get_priority_value(self) -> int:
        """우선순위를 숫자로 변환 (정렬용)"""
        priority_map = {'high': 3, 'medium': 2, 'low': 1}
        return priority_map.get(self.priority, 2)

    def transition_to(self, new_status: str) -> bool:
        """유효한 상태 전환 수행
        
        Args:
            new_status: 전환할 상태
            
        Returns:
            bool: 전환 성공 여부
        """
        valid_transitions = {'pending': ['ready', 'blocked', 'cancelled'], 'ready': ['in_progress', 'blocked', 'cancelled'], 'blocked': ['ready', 'cancelled'], 'in_progress': ['completed', 'blocked', 'cancelled'], 'completed': [], 'cancelled': []}
        current_valid = valid_transitions.get(self.status, [])
        if new_status not in current_valid:
            return False
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now()
        self.state_history.append({'from': old_status, 'to': new_status, 'timestamp': self.updated_at, 'reason': self.blocking_reason if new_status == 'blocked' else None})
        if new_status == 'in_progress':
            self.started_at = datetime.now()
        elif new_status == 'completed':
            self.completed_at = datetime.now()
            self.completed = True
            if self.started_at:
                self.actual_hours = (self.completed_at - self.started_at).total_seconds() / 3600
        elif new_status == 'blocked':
            pass
        return True

    def can_start(self) -> bool:
        """작업 시작 가능 여부 확인
        
        Returns:
            bool: 시작 가능하면 True
        """
        return self.status in ['pending', 'ready']

    def check_dependencies(self) -> List[str]:
        """충족되지 않은 의존성 목록 반환
        
        Returns:
            List[str]: 충족되지 않은 의존성 ID 목록
        """
        return self.dependencies if self.dependencies else []

    def add_dependency(self, task_id: str) -> None:
        """의존성 추가
        
        Args:
            task_id: 의존할 작업 ID
        """
        if not self.dependencies:
            self.dependencies = []
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)
            self.updated_at = datetime.now()

    def remove_dependency(self, task_id: str) -> None:
        """의존성 제거
        
        Args:
            task_id: 제거할 의존성 작업 ID
        """
        if self.dependencies and task_id in self.dependencies:
            self.dependencies.remove(task_id)
            self.updated_at = datetime.now()

    def get_time_in_state(self, state: Optional[str]=None) -> float:
        """특정 상태(또는 현재 상태)에 머문 시간 계산 (시간 단위)
        
        Args:
            state: 조회할 상태 (None이면 현재 상태)
            
        Returns:
            float: 해당 상태에 머문 시간 (시간 단위)
        """
        if state is None:
            state = self.status
        total_hours = 0.0
        for i, entry in enumerate(self.state_history):
            if entry['to'] == state:
                if i + 1 < len(self.state_history):
                    next_entry = self.state_history[i + 1]
                    duration = next_entry['timestamp'] - entry['timestamp']
                else:
                    duration = datetime.now() - entry['timestamp']
                total_hours += duration.total_seconds() / 3600
        if state == self.status and total_hours == 0:
            if state == 'in_progress' and self.started_at:
                total_hours = (datetime.now() - self.started_at).total_seconds() / 3600
            elif state == 'completed' and self.completed_at and self.started_at:
                total_hours = (self.completed_at - self.started_at).total_seconds() / 3600
        return total_hours

    def set_blocking_reason(self, reason: str) -> None:
        """차단 이유 설정
        
        Args:
            reason: 차단 이유
        """
        self.blocking_reason = reason
        self.updated_at = datetime.now()

    def estimate_completion_time(self) -> Optional[datetime]:
        """예상 완료 시간 계산
        
        Returns:
            Optional[datetime]: 예상 완료 시간
        """
        if self.status == 'completed':
            return self.completed_at
        if self.status == 'in_progress' and self.started_at and self.estimated_hours:
            return self.started_at + timedelta(hours=self.estimated_hours)
        return None

    def get_progress_percentage(self) -> float:
        """작업 진행률 계산 (0-100)
        
        Returns:
            float: 진행률 (0-100)
        """
        if self.status == 'completed':
            return 100.0
        elif self.status == 'in_progress' and self.started_at and self.estimated_hours:
            elapsed = (datetime.now() - self.started_at).total_seconds() / 3600
            return min(100.0, elapsed / self.estimated_hours * 100)
        else:
            return 0.0

class Phase(BaseModelWithConfig):
    """단계(Phase) 모델"""
    id: str
    name: str
    description: str = ''
    status: str = Field(default='pending', pattern='^(pending|in_progress|completed)$')
    task_order: List[str] = Field(default_factory=list)
    progress: float = 0.0
    completed_tasks: int = 0
    total_tasks: int = 0
    estimated_days: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    tasks: Dict[str, Task] = Field(default_factory=dict)

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """ID로 작업 찾기"""
        return self.tasks.get(task_id)

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """ID로 작업 찾기"""
        return self.tasks.get(task_id)

    def add_task(self, title: str, description: str='') -> Task:
        """새 작업 추가"""
        task = Task(title=title, description=description, phase_id=self.id)
        self.tasks[task.id] = task
        self.task_order.append(task.id)
        return task

    def progress(self) -> Dict[str, Any]:
        """진행률 계산"""
        total = len(self.tasks)
        completed = len([t for t in self.tasks.values() if t.completed])
        return {'total': total, 'completed': completed, 'percentage': completed / total * 100 if total > 0 else 0}

    def get_progress_details(self) -> Dict[str, Any]:
        """상세 진행 상황 반환
        
        Returns:
            Dict[str, Any]: 상태별 작업 수, 진행률 등 상세 정보
        """
        status_count = {'pending': 0, 'ready': 0, 'in_progress': 0, 'completed': 0, 'blocked': 0, 'cancelled': 0}
        for task in self.tasks:
            status_count[task.status] = status_count.get(task.status, 0) + 1
        return {'status_count': status_count, 'total_tasks': len(self.tasks), 'active_tasks': status_count['in_progress'], 'completion_rate': self.progress['percentage'], 'blocked_rate': status_count['blocked'] / len(self.tasks) * 100 if self.tasks else 0}

    def get_active_task(self) -> Optional[Task]:
        """현재 진행 중인 작업 반환
        
        Returns:
            Optional[Task]: 진행 중인 작업 (없으면 None)
        """
        for task in self.tasks:
            if task.status == 'in_progress':
                return task
        return None

    def can_complete(self) -> bool:
        """Phase 완료 가능 여부 확인
        
        Returns:
            bool: 모든 작업이 완료/취소되었으면 True
        """
        for task in self.tasks:
            if task.status not in ['completed', 'cancelled']:
                return False
        return True

    def estimate_remaining_time(self) -> float:
        """남은 예상 시간 계산 (시간 단위)
        
        Returns:
            float: 남은 예상 시간
        """
        remaining_hours = 0.0
        for task in self.tasks:
            if task.status in ['pending', 'ready', 'blocked']:
                if task.estimated_hours:
                    remaining_hours += task.estimated_hours
            elif task.status == 'in_progress':
                if task.estimated_hours and task.started_at:
                    elapsed = (datetime.now() - task.started_at).total_seconds() / 3600
                    remaining = max(0, task.estimated_hours - elapsed)
                    remaining_hours += remaining
        return remaining_hours

    def get_next_task(self) -> Optional[Task]:
        """Phase 내에서 다음 실행할 작업 반환
        
        Returns:
            Optional[Task]: 다음 작업 (없으면 None)
        """
        available_tasks = [t for t in self.tasks if t.status in ['pending', 'ready']]
        if not available_tasks:
            return None
        available_tasks.sort(key=lambda t: t.get_priority_value(), reverse=True)
        return available_tasks[0]

class Plan(BaseModelWithConfig):
    """계획(Plan) 모델"""
    name: str
    description: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    phases: Dict[str, Phase] = Field(default_factory=dict)
    current_phase: Optional[str] = None
    current_task: Optional[str] = None
    phase_order: List[str] = Field(default_factory=list)
    content: Optional[str] = None
    content_history: List[Dict[str, Any]] = Field(default_factory=list)
    overall_progress: float = 0.0
    project_insights: Dict[str, Any] = Field(default_factory=dict)
    wisdom_data: Dict[str, Any] = Field(default_factory=dict)

    @property
    def tasks(self) -> List[Task]:
        """모든 Phase의 Task를 하나의 리스트로 반환하는 프로퍼티"""
        return self.get_all_tasks()

    def get_all_tasks(self) -> List[Task]:
        """모든 Phase의 Task를 하나의 리스트로 반환"""
        all_tasks = []
        for phase in self.phases.values():
            all_tasks.extend(phase.tasks.values())
        return all_tasks

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """ID로 Task 조회 (모든 Phase에서 검색)"""
        for phase in self.phases.values():
            task = phase.get_task_by_id(task_id)
            if task:
                return task
        return None

    def get_current_task(self) -> Optional[Task]:
        """현재 진행 중인 Task 반환"""
        for task in self.get_all_tasks():
            if task.status == TaskStatus.IN_PROGRESS:
                return task
        return None

    def get_next_tasks(self) -> List[Task]:
        """다음에 수행 가능한 Task 목록 반환"""
        next_tasks = []
        all_tasks = self.get_all_tasks()
        for task in all_tasks:
            if task.status in [TaskStatus.PENDING, TaskStatus.READY]:
                if not task.dependencies:
                    next_tasks.append(task)
                else:
                    deps_completed = all((any((t.id == dep_id and t.status == TaskStatus.COMPLETED for t in all_tasks)) for dep_id in task.dependencies))
                    if deps_completed:
                        next_tasks.append(task)
        return next_tasks

    def update_progress(self) -> None:
        """Phase와 전체 Plan의 진행률 업데이트"""
        total_tasks = 0
        completed_tasks = 0
        for phase in self.phases.values():
            phase_tasks = list(phase.tasks.values())
            phase.total_tasks = len(phase_tasks)
            phase.completed_tasks = sum((1 for t in phase_tasks if t.status == TaskStatus.COMPLETED))
            phase.progress = phase.completed_tasks / phase.total_tasks * 100 if phase.total_tasks > 0 else 0.0
            total_tasks += phase.total_tasks
            completed_tasks += phase.completed_tasks

    def get_next_task(self) -> Optional[Tuple[str, Task]]:
        """다음에 수행할 작업 반환 (phase_id, task)"""
        for phase_id in self.phase_order:
            phase = self.phases.get(phase_id)
            if phase and phase.status != 'completed':
                for task_id in phase.task_order:
                    task = phase.tasks.get(task_id)
                    if task and task.status == TaskStatus.PENDING:
                        return (phase_id, task)
        return None
        self.overall_progress = completed_tasks / total_tasks * 100 if total_tasks > 0 else 0.0

class WorkTracking(BaseModelWithConfig):
    """작업 추적 모델"""
    file_access: Dict[str, Any] = Field(default_factory=dict)
    file_edits: Dict[str, int] = Field(default_factory=dict)
    function_edits: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    session_start: Union[datetime, str] = Field(default_factory=datetime.now)
    total_operations: int = 0
    task_tracking: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    current_task_work: Dict[str, Any] = Field(default_factory=lambda: {'task_id': None, 'start_time': None, 'files_accessed': [], 'functions_edited': [], 'operations': []})

    @validator('session_start', pre=True)
    def parse_session_start(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v

    def get_blocked_tasks(self) -> Dict[str, List[str]]:
        """의존성으로 인해 차단된 작업 목록 반환
        
        Returns:
            Dict[str, List[str]]: {작업ID: [차단하는 작업ID들]}
        """
        blocked = {}
        all_tasks = self.get_all_tasks()
        for task in all_tasks:
            if task.status in ['pending', 'ready'] and task.dependencies:
                incomplete_deps = []
                for dep_id in task.dependencies:
                    dep_task = self.get_task_by_id(dep_id)
                    if dep_task and dep_task.status != 'completed':
                        incomplete_deps.append(dep_id)
                if incomplete_deps:
                    blocked[task.id] = incomplete_deps
        return blocked

class FileAccessEntry(BaseModelWithConfig):
    """파일 접근 기록 항목"""
    file: str
    operation: str
    timestamp: Union[datetime, str]
    task_id: Optional[str] = None

    @validator('timestamp', pre=True)
    def parse_timestamp(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v

class ProjectContext(BaseModelWithConfig):
    """프로젝트 컨텍스트 - 메인 모델"""
    project_name: str
    project_id: str
    project_path: Union[str, Path]
    memory_root: Union[str, Path]
    created_at: Union[datetime, str] = Field(default_factory=datetime.now)
    updated_at: Union[datetime, str] = Field(default_factory=datetime.now)
    version: str = '7.0'
    metadata: Dict[str, Any] = Field(default_factory=dict)
    plan: Optional[Plan] = None
    current_focus: str = ''
    current_task: Optional[str] = None
    tasks: Dict[str, List[Any]] = Field(default_factory=lambda: {'next': [], 'done': []})
    analyzed_files: Dict[str, Any] = Field(default_factory=dict)
    work_tracking: Union[WorkTracking, Dict[str, Any]] = Field(default_factory=WorkTracking)
    file_access_history: List[Union[FileAccessEntry, Dict[str, Any]]] = Field(default_factory=list)
    plan_history: List[Dict[str, Any]] = Field(default_factory=list)
    coding_experiences: List[str] = Field(default_factory=list)
    progress: Dict[str, Any] = Field(default_factory=lambda: {'completed_tasks': 0, 'total_tasks': 0, 'percentage': 0.0})
    phase_reports: Dict[str, Any] = Field(default_factory=dict)
    error_log: List[Dict[str, Any]] = Field(default_factory=list)
    function_edit_history: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

    @validator('project_path', 'memory_root', pre=True)
    def convert_to_path(cls, v):
        if isinstance(v, str):
            return Path(v)
        return v

    @validator('created_at', 'updated_at', pre=True)
    def parse_datetime(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v

    @validator('work_tracking', pre=True)
    def parse_work_tracking(cls, v):
        if isinstance(v, dict) and (not isinstance(v, WorkTracking)):
            return WorkTracking(**v)
        return v

    @validator('file_access_history', pre=True)
    def parse_file_access_history(cls, v):
        if isinstance(v, list):
            parsed = []
            for item in v:
                if isinstance(item, dict) and (not isinstance(item, FileAccessEntry)):
                    parsed.append(FileAccessEntry(**item))
                else:
                    parsed.append(item)
            return parsed
        return v

    def get_current_phase(self) -> Optional[Phase]:
        """현재 단계 반환"""
        if self.plan:
            return self.plan.get_current_phase()
        return None

    def get_all_tasks(self) -> List[Task]:
        """모든 작업 반환"""
        if self.plan:
            return self.plan.get_all_tasks()
        return []

    def update_progress(self):
        """진행률 업데이트"""
        if self.plan:
            # Plan의 전체 진행률 업데이트
            self.plan.update_progress()
            
            # Context의 progress 딕셔너리 업데이트
            all_tasks = self.plan.get_all_tasks()
            completed = sum(1 for t in all_tasks if t.status == TaskStatus.COMPLETED)
            total = len(all_tasks)
            
            self.progress = {
                'completed_tasks': completed,
                'total_tasks': total,
                'percentage': round(self.plan.overall_progress, 1)
            }
    @classmethod
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectContext':
        """딕셔너리에서 ProjectContext 생성 (Plan 처리 개선)"""
        data = data.copy()
        for field in ['created_at', 'updated_at']:
            if field in data and isinstance(data[field], str):
                try:
                    data[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                except:
                    data[field] = datetime.now()
        if 'plan' in data and data['plan']:
            if isinstance(data['plan'], dict):
                plan_data = data['plan']
                if 'phases' in plan_data and isinstance(plan_data['phases'], dict):
                    for phase_id, phase_data in plan_data['phases'].items():
                        if 'tasks' in phase_data:
                            if isinstance(phase_data['tasks'], list):
                                tasks_dict = {}
                                for task in phase_data['tasks']:
                                    if isinstance(task, dict) and 'id' in task:
                                        tasks_dict[task['id']] = task
                                phase_data['tasks'] = tasks_dict
        return cls(**data)

    def to_json(self) -> str:
        """JSON 문자열로 변환"""
        return json.dumps(self.model_dump(), indent=2, ensure_ascii=False, default=str)

    @classmethod
    def from_json(cls, json_str: str) -> 'ProjectContext':
        """JSON 문자열에서 생성"""
        data = json.loads(json_str)
        return cls.from_dict(data)

def validate_context_data(data: Dict[str, Any]) -> Optional[ProjectContext]:
    """컨텍스트 데이터 검증 및 변환"""
    try:
        return ProjectContext.from_dict(data)
    except Exception as e:
        print(f'❌ 컨텍스트 데이터 검증 실패: {e}')
        return None