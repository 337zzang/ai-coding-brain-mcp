"""
AI Coding Brain Pydantic 데이터 모델
버전: 1.0
작성일: 2025-06-24

이 모듈은 프로젝트의 모든 데이터 구조를 Pydantic 모델로 정의합니다.
타입 안정성과 자동 검증을 제공하여 런타임 오류를 방지합니다.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any, Union
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import json


class TaskStatus(str, Enum):
    """작업의 상태를 정의하는 Enum"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELED = "canceled"


class BaseModelWithConfig(BaseModel):
    """
    JSON 직렬화와 Path 객체 처리를 위한 기본 모델
    """
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            Path: str,
            datetime: lambda v: v.isoformat() if v else None
        }
        
    def model_dump(self, **kwargs):
        """Path 객체를 문자열로 변환하여 반환"""
        d = super().model_dump(**kwargs)
        return self._convert_paths_to_str(d)
    
    # 하위 호환성을 위한 별칭
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
    id: str
    title: str
    description: str = ""
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    priority: str = Field(default='medium', pattern='^(high|medium|low)$')
    phase_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    completed: bool = False
    subtasks: List[str] = Field(default_factory=list)
    work_summary: Optional[Dict[str, Any]] = None
    dependencies: List[str] = Field(default_factory=list)  # 의존성 작업 ID 목록
    related_files: List[str] = Field(default_factory=list)  # 관련 파일 목록
    
    # 상태 관리 강화 필드
    state_history: List[Dict[str, Any]] = Field(default_factory=list)  # 상태 변경 이력
    blocking_reason: Optional[str] = None  # 차단 이유
    estimated_hours: Optional[float] = None  # 예상 소요 시간
    actual_hours: Optional[float] = None  # 실제 소요 시간
    
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
    
    def mark_completed(self):
        """작업을 완료 상태로 표시"""
        self.completed = True
        self.status = 'completed'
        self.completed_at = datetime.now()
    
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
        # 유효한 상태 전환 규칙
        valid_transitions = {
            'pending': ['ready', 'blocked', 'cancelled'],
            'ready': ['in_progress', 'blocked', 'cancelled'],
            'blocked': ['ready', 'cancelled'],
            'in_progress': ['completed', 'blocked', 'cancelled'],
            'completed': [],  # 완료된 작업은 상태 변경 불가
            'cancelled': []   # 취소된 작업은 상태 변경 불가
        }
        
        current_valid = valid_transitions.get(self.status, [])
        
        if new_status not in current_valid:
            return False
        
        # 상태 전환
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now()
        
        # 상태 이력 기록
        self.state_history.append({
            'from': old_status,
            'to': new_status,
            'timestamp': self.updated_at,
            'reason': self.blocking_reason if new_status == 'blocked' else None
        })
        
        # 상태별 추가 처리
        if new_status == 'in_progress':
            self.started_at = datetime.now()
        elif new_status == 'completed':
            self.completed_at = datetime.now()
            self.completed = True
            # 실제 소요 시간 계산
            if self.started_at:
                self.actual_hours = (self.completed_at - self.started_at).total_seconds() / 3600
        elif new_status == 'blocked':
            # blocking_reason은 transition_to 호출 전에 설정되어야 함
            pass
        
        return True
    
    def can_start(self) -> bool:
        """작업 시작 가능 여부 확인
        
        Returns:
            bool: 시작 가능하면 True
        """
        # 시작 가능한 상태: pending 또는 ready
        return self.status in ['pending', 'ready']
    
    def check_dependencies(self) -> List[str]:
        """충족되지 않은 의존성 목록 반환
        
        Returns:
            List[str]: 충족되지 않은 의존성 ID 목록
        """
        # 실제 의존성 체크는 Plan 레벨에서 수행
        # 여기서는 의존성 목록만 반환
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
    
    def get_time_in_state(self, state: Optional[str] = None) -> float:
        """특정 상태(또는 현재 상태)에 머문 시간 계산 (시간 단위)
        
        Args:
            state: 조회할 상태 (None이면 현재 상태)
            
        Returns:
            float: 해당 상태에 머문 시간 (시간 단위)
        """
        if state is None:
            state = self.status
        
        total_hours = 0.0
        
        # 상태 이력에서 해당 상태에 머문 시간 계산
        for i, entry in enumerate(self.state_history):
            if entry['to'] == state:
                # 다음 상태 변경까지의 시간 계산
                if i + 1 < len(self.state_history):
                    next_entry = self.state_history[i + 1]
                    duration = next_entry['timestamp'] - entry['timestamp']
                else:
                    # 마지막 상태면 현재까지의 시간
                    duration = datetime.now() - entry['timestamp']
                
                total_hours += duration.total_seconds() / 3600
        
        # 현재 상태가 요청한 상태와 같고 이력이 없으면
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
            # 시작 시간 + 예상 소요 시간
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
            return min(100.0, (elapsed / self.estimated_hours) * 100)
        else:
            return 0.0


class Phase(BaseModelWithConfig):
    """단계(Phase) 모델"""
    id: str
    name: str
    description: str = ""
    status: str = Field(default='pending', pattern='^(pending|in_progress|completed)$')
    tasks: List[Task] = Field(default_factory=list)
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """ID로 작업 찾기"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def add_task(self, title: str, description: str = "") -> Task:
        """새 작업 추가"""
        task_id = f"{self.id.split('-')[1]}-{len(self.tasks) + 1}"
        task = Task(
            id=task_id,
            title=title,
            description=description,
            phase_id=self.id
        )
        self.tasks.append(task)
        return task
    
    @property
    def progress(self) -> Dict[str, Any]:
        """진행률 계산"""
        total = len(self.tasks)
        completed = len([t for t in self.tasks if t.completed])
        return {
            'total': total,
            'completed': completed,
            'percentage': (completed / total * 100) if total > 0 else 0
        }
    
    def get_progress_details(self) -> Dict[str, Any]:
        """상세 진행 상황 반환
        
        Returns:
            Dict[str, Any]: 상태별 작업 수, 진행률 등 상세 정보
        """
        status_count = {
            'pending': 0,
            'ready': 0,
            'in_progress': 0,
            'completed': 0,
            'blocked': 0,
            'cancelled': 0
        }
        
        for task in self.tasks:
            status_count[task.status] = status_count.get(task.status, 0) + 1
        
        return {
            'status_count': status_count,
            'total_tasks': len(self.tasks),
            'active_tasks': status_count['in_progress'],
            'completion_rate': self.progress['percentage'],
            'blocked_rate': (status_count['blocked'] / len(self.tasks) * 100) if self.tasks else 0
        }
    
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
                # 예상 시간이 설정된 경우
                if task.estimated_hours:
                    remaining_hours += task.estimated_hours
            elif task.status == 'in_progress':
                # 진행 중인 작업의 남은 시간
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
        # pending이나 ready 상태의 작업 중 우선순위가 가장 높은 것
        available_tasks = [t for t in self.tasks if t.status in ['pending', 'ready']]
        
        if not available_tasks:
            return None
        
        # 우선순위로 정렬
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
    
    def get_current_phase(self) -> Optional[Phase]:
        """현재 단계 반환"""
        if self.current_phase:
            return self.phases.get(self.current_phase)
        return None
    
    def get_all_tasks(self) -> List[Task]:
        """모든 작업 반환"""
        all_tasks = []
        for phase in self.phases.values():
            all_tasks.extend(phase.tasks)
        return all_tasks
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """ID로 작업 찾기"""
        for phase in self.phases.values():
            task = phase.get_task_by_id(task_id)
            if task:
                return task
        return None
    
    @property
    def overall_progress(self) -> Dict[str, Any]:
        """전체 진행률 계산"""
        all_tasks = self.get_all_tasks()
        total = len(all_tasks)
        completed = len([t for t in all_tasks if t.completed])
        return {
            'total_tasks': total,
            'completed_tasks': completed,
            'percentage': (completed / total * 100) if total > 0 else 0
        }
    
    def get_next_task(self) -> Optional[Task]:
        """우선순위와 의존성을 고려하여 다음 실행할 작업 반환
        
        Returns:
            Optional[Task]: 다음 실행할 작업, 없으면 None
        """
        ready_tasks = self.get_ready_tasks()
        
        if not ready_tasks:
            return None
        
        # 우선순위로 정렬 (HIGH > MEDIUM > LOW)
        ready_tasks.sort(key=lambda t: t.get_priority_value(), reverse=True)
        
        # 동일 우선순위인 경우 생성 시간 순
        ready_tasks.sort(key=lambda t: (t.get_priority_value(), t.created_at), 
                        reverse=True)
        
        return ready_tasks[0]
    
    def get_ready_tasks(self) -> List[Task]:
        """실행 가능한 모든 작업 목록 반환
        
        Returns:
            List[Task]: 실행 가능한 작업들
        """
        ready_tasks = []
        
        for phase in self.phases.values():
            for task in phase.tasks:
                # pending 상태이고 의존성이 충족된 작업
                if task.status == "pending" and self._check_task_dependencies(task):
                    ready_tasks.append(task)
                # 이미 ready 상태인 작업
                elif task.status == "ready":
                    ready_tasks.append(task)
        
        return ready_tasks
    
    def get_blocked_tasks(self) -> List[Task]:
        """의존성으로 인해 차단된 작업 목록 반환
        
        Returns:
            List[Task]: 차단된 작업들
        """
        blocked_tasks = []
        
        for phase in self.phases.values():
            for task in phase.tasks:
                # pending 상태이지만 의존성이 충족되지 않은 작업
                if task.status == "pending" and not self._check_task_dependencies(task):
                    blocked_tasks.append(task)
                # 명시적으로 blocked 상태인 작업
                elif task.status == "blocked":
                    blocked_tasks.append(task)
        
        return blocked_tasks
    
    def reorder_by_priority(self) -> None:
        """모든 Phase의 작업을 우선순위로 재정렬"""
        for phase in self.phases.values():
            # Phase 내 작업들을 우선순위로 정렬
            phase.tasks.sort(key=lambda t: t.get_priority_value(), reverse=True)
    
    def update_task_status(self, task_id: str, status: str) -> bool:
        """작업 상태 업데이트
        
        Args:
            task_id: 작업 ID
            status: 새로운 상태
            
        Returns:
            bool: 성공 여부
        """
        task = self.get_task_by_id(task_id)
        if task:
            old_status = task.status
            task.status = status
            task.updated_at = datetime.now()
            
            # 상태 전환에 따른 추가 처리
            if status == "in_progress" and old_status != "in_progress":
                task.started_at = datetime.now()
            elif status == "completed" and old_status != "completed":
                task.completed_at = datetime.now()
                task.completed = True
            
            return True
        return False
    
    def _check_task_dependencies(self, task: Task) -> bool:
        """작업의 의존성 충족 여부 확인 (내부 헬퍼)
        
        Args:
            task: 확인할 작업
            
        Returns:
            bool: 의존성이 모두 충족되면 True
        """
        if not task.dependencies:
            return True
        
        for dep_id in task.dependencies:
            dep_task = self.get_task_by_id(dep_id)
            if not dep_task or dep_task.status != "completed":
                return False
        
        return True


class WorkTracking(BaseModelWithConfig):
    """작업 추적 모델"""
    file_access: Dict[str, Any] = Field(default_factory=dict)  # 더 유연한 타입
    file_edits: Dict[str, int] = Field(default_factory=dict)
    function_edits: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    session_start: Union[datetime, str] = Field(default_factory=datetime.now)
    total_operations: int = 0
    task_tracking: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    current_task_work: Dict[str, Any] = Field(default_factory=lambda: {
        'task_id': None,
        'start_time': None,
        'files_accessed': [],
        'functions_edited': [],
        'operations': []
    })
    
    @validator('session_start', pre=True)
    def parse_session_start(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v


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
    # 기본 정보
    project_name: str
    project_id: str
    project_path: Union[str, Path]
    memory_root: Union[str, Path]
    
    # 시간 정보
    created_at: Union[datetime, str] = Field(default_factory=datetime.now)
    updated_at: Union[datetime, str] = Field(default_factory=datetime.now)
    
    # 버전 및 메타데이터
    version: str = "7.0"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # 작업 관련
    plan: Optional[Plan] = None
    current_focus: str = ""
    current_task: Optional[str] = None
    tasks: Dict[str, List[Any]] = Field(default_factory=lambda: {'next': [], 'done': []})
    
    # 분석 및 추적
    analyzed_files: Dict[str, Any] = Field(default_factory=dict)
    work_tracking: Union[WorkTracking, Dict[str, Any]] = Field(default_factory=WorkTracking)
    file_access_history: List[Union[FileAccessEntry, Dict[str, Any]]] = Field(default_factory=list)
    
    # 기타
    plan_history: List[Dict[str, Any]] = Field(default_factory=list)
    coding_experiences: List[str] = Field(default_factory=list)
    progress: Dict[str, Any] = Field(default_factory=lambda: {
        'completed_tasks': 0,
        'total_tasks': 0,
        'percentage': 0.0
    })
    phase_reports: Dict[str, Any] = Field(default_factory=dict)
    error_log: List[Dict[str, Any]] = Field(default_factory=list)
    
    # 추가 필드 (선택적)
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
        if isinstance(v, dict) and not isinstance(v, WorkTracking):
            return WorkTracking(**v)
        return v
    
    @validator('file_access_history', pre=True)
    def parse_file_access_history(cls, v):
        if isinstance(v, list):
            parsed = []
            for item in v:
                if isinstance(item, dict) and not isinstance(item, FileAccessEntry):
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
            progress_info = self.plan.overall_progress
            self.progress.update(progress_info)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectContext':
        """딕셔너리에서 ProjectContext 생성"""
        # Plan 데이터 처리
        if 'plan' in data and data['plan'] and isinstance(data['plan'], dict):
            plan_data = data['plan'].copy()
            # phases 처리
            if 'phases' in plan_data:
                phases = {}
                for phase_id, phase_data in plan_data['phases'].items():
                    if 'tasks' in phase_data:
                        tasks = []
                        for task_data in phase_data['tasks']:
                            tasks.append(Task(**task_data))
                        phase_data['tasks'] = tasks
                    phases[phase_id] = Phase(**phase_data)
                plan_data['phases'] = phases
            data['plan'] = Plan(**plan_data)
        
        return cls(**data)
    
    def to_json(self) -> str:
        """JSON 문자열로 변환"""
        return json.dumps(self.model_dump(), indent=2, ensure_ascii=False, default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ProjectContext':
        """JSON 문자열에서 생성"""
        data = json.loads(json_str)
        return cls.from_dict(data)


# 유틸리티 함수
def validate_context_data(data: Dict[str, Any]) -> Optional[ProjectContext]:
    """컨텍스트 데이터 검증 및 변환"""
    try:
        return ProjectContext.from_dict(data)
    except Exception as e:
        print(f"❌ 컨텍스트 데이터 검증 실패: {e}")
        return None
