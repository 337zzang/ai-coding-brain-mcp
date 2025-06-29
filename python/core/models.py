"""
WorkflowManager 중심 아키텍처를 위한 데이터 모델
"""
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, validator
from pathlib import Path
import uuid
import json


class TaskStatus(str, Enum):
    """작업 상태"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    
    
class PhaseStatus(str, Enum):
    """Phase 상태"""
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


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


class Task(BaseModel):
    """작업 모델"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    phase_id: str
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    content: Optional[str] = None  # 완료 내용
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    estimated_hours: float = 1.0
    actual_hours: float = 0.0
    priority: str = Field(default='medium', pattern='^(high|medium|low)$')
    completed: bool = False
    
    def can_start(self) -> bool:
        """작업을 시작할 수 있는지 확인"""
        return self.status == TaskStatus.PENDING
    
    def can_complete(self) -> bool:
        """작업을 완료할 수 있는지 확인"""
        return self.status == TaskStatus.IN_PROGRESS
    
    def start(self) -> bool:
        """작업 시작"""
        if self.can_start():
            self.status = TaskStatus.IN_PROGRESS
            return True
        return False
    
    def complete(self, content: Optional[str] = None) -> bool:
        """작업 완료"""
        if self.can_complete():
            self.status = TaskStatus.COMPLETED
            self.completed_at = datetime.now()
            self.completed = True
            if content:
                self.content = content
            return True
        return False


class Phase(BaseModel):
    """Phase 모델"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    status: PhaseStatus = PhaseStatus.PLANNING
    tasks: Dict[str, Task] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Task 순서 및 진행률 관리
    task_order: List[str] = Field(default_factory=list)  # Task 표시 순서
    progress: float = 0.0  # Phase 진행률 (0-100%)
    completed_tasks: int = 0  # 완료된 Task 수
    total_tasks: int = 0  # 전체 Task 수
    
    def add_task(self, task: Task) -> None:
        """작업 추가"""
        task.phase_id = self.id
        self.tasks[task.id] = task
        if task.id not in self.task_order:
            self.task_order.append(task.id)
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """ID로 작업 찾기"""
        return self.tasks.get(task_id)
    
    def get_pending_tasks(self) -> List[Task]:
        """대기 중인 작업 목록"""
        return [t for t in self.tasks.values() if t.status == TaskStatus.PENDING]
    
    def get_active_task(self) -> Optional[Task]:
        """진행 중인 작업"""
        for task in self.tasks.values():
            if task.status == TaskStatus.IN_PROGRESS:
                return task
        return None
    
    def is_complete(self) -> bool:
        """Phase 완료 여부"""
        return all(t.status == TaskStatus.COMPLETED for t in self.tasks.values())
    
    def update_status(self) -> None:
        """Phase 상태 업데이트"""
        if self.is_complete():
            self.status = PhaseStatus.COMPLETED
        elif any(t.status != TaskStatus.PENDING for t in self.tasks.values()):
            self.status = PhaseStatus.IN_PROGRESS


class Plan(BaseModel):
    """계획 모델"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    phases: Dict[str, Phase] = Field(default_factory=dict)
    current_phase_id: Optional[str] = None
    current_task_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Phase 순서 및 진행률 관리
    phase_order: List[str] = Field(default_factory=list)  # Phase 표시 순서
    overall_progress: float = 0.0  # 전체 진행률 (0-100%)
    
    # 통합 정보
    project_insights: Dict[str, Any] = Field(default_factory=dict)  # ProjectAnalyzer 분석 결과
    wisdom_data: Dict[str, Any] = Field(default_factory=dict)  # Wisdom 시스템 데이터
    
    @property
    def current_phase(self) -> Optional[str]:
        """현재 phase ID 반환"""
        return self.current_phase_id
    
    def add_phase(self, phase: Phase) -> None:
        """Phase 추가"""
        self.phases[phase.id] = phase
        if phase.id not in self.phase_order:
            self.phase_order.append(phase.id)
        if not self.current_phase_id:
            self.current_phase_id = phase.id
    
    def get_current_phase(self) -> Optional[Phase]:
        """현재 Phase 조회"""
        if not self.current_phase_id:
            return None
        return self.phases.get(self.current_phase_id)
    
    def get_current_task(self) -> Optional[Task]:
        """현재 작업 조회"""
        if not self.current_task_id:
            return None
        for phase in self.phases.values():
            task = phase.get_task_by_id(self.current_task_id)
            if task:
                return task
        return None
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """ID로 Task 조회 (모든 Phase에서 검색)"""
        for phase in self.phases.values():
            task = phase.get_task_by_id(task_id)
            if task:
                return task
        return None
    
    def get_next_task(self) -> Optional[Task]:
        """다음 작업 찾기"""
        # 현재 Phase에서 대기 중인 작업 찾기
        current_phase = self.get_current_phase()
        if current_phase:
            pending_tasks = current_phase.get_pending_tasks()
            if pending_tasks:
                return pending_tasks[0]
        
        # 다음 Phase로 이동
        if self.current_phase_id:
            current_index = next((i for i, p in enumerate(self.phase_order) if p == self.current_phase_id), -1)
            for i in range(current_index + 1, len(self.phase_order)):
                phase_id = self.phase_order[i]
                phase = self.phases.get(phase_id)
                if phase:
                    pending_tasks = phase.get_pending_tasks()
                    if pending_tasks:
                        self.current_phase_id = phase.id
                        return pending_tasks[0]
        
        return None
    
    def get_all_tasks(self) -> List[Task]:
        """모든 작업 목록"""
        tasks = []
        for phase in self.phases.values():
            tasks.extend(phase.tasks.values())
        return tasks
    
    def get_progress(self) -> float:
        """전체 진행률 (0-100)"""
        all_tasks = self.get_all_tasks()
        if not all_tasks:
            return 0.0
        completed = sum(1 for t in all_tasks if t.status == TaskStatus.COMPLETED)
        return (completed / len(all_tasks)) * 100


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
    version: str = "8.0"
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
    language: str = "python"  # 기본값 추가
    
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
            progress = self.plan.get_progress()
            all_tasks = self.plan.get_all_tasks()
            completed = sum(1 for t in all_tasks if t.status == TaskStatus.COMPLETED)
            self.progress = {
                'completed_tasks': completed,
                'total_tasks': len(all_tasks),
                'percentage': progress
            }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectContext':
        """딕셔너리에서 ProjectContext 생성 (Plan 처리 개선)"""
        # 복사본 생성하여 원본 데이터 보호
        data = data.copy()
        
        # datetime 문자열 처리
        for field in ['created_at', 'updated_at']:
            if field in data and isinstance(data[field], str):
                try:
                    data[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                except:
                    data[field] = datetime.now()
        
        # Plan 데이터는 dict 상태로 유지
        # ProjectContext의 validator가 자동으로 Plan 객체로 변환
        if 'plan' in data and data['plan']:
            if isinstance(data['plan'], dict):
                # phases가 있으면 tasks 구조만 정리
                plan_data = data['plan']
                if 'phases' in plan_data and isinstance(plan_data['phases'], dict):
                    for phase_id, phase_data in plan_data['phases'].items():
                        if 'tasks' in phase_data:
                            # tasks가 list인 경우 dict로 변환
                            if isinstance(phase_data['tasks'], list):
                                tasks_dict = {}
                                for task in phase_data['tasks']:
                                    if isinstance(task, dict) and 'id' in task:
                                        tasks_dict[task['id']] = task
                                phase_data['tasks'] = tasks_dict
        
        # ProjectContext 생성
        return cls(**data)
    
    def to_json(self) -> str:
        """JSON 문자열로 변환"""
        return json.dumps(self.model_dump(), indent=2, ensure_ascii=False, default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ProjectContext':
        """JSON 문자열에서 생성"""
        data = json.loads(json_str)
        return cls.from_dict(data)


class WorkflowState(BaseModel):
    """워크플로우 전체 상태"""
    project_name: str
    plan: Optional[Plan] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def update(self) -> None:
        """업데이트 시간 갱신"""
        self.updated_at = datetime.now()


# 유틸리티 함수
def validate_context_data(data: Dict[str, Any]) -> Optional[ProjectContext]:
    """컨텍스트 데이터 검증 및 변환"""
    try:
        return ProjectContext.from_dict(data)
    except Exception as e:
        print(f"❌ 컨텍스트 데이터 검증 실패: {e}")
        return None
