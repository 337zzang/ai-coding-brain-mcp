"""
AI Coding Brain Pydantic 데이터 모델
버전: 1.0
작성일: 2025-06-24

이 모듈은 프로젝트의 모든 데이터 구조를 Pydantic 모델로 정의합니다.
타입 안정성과 자동 검증을 제공하여 런타임 오류를 방지합니다.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from pathlib import Path
import json


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
    status: str = Field(default='pending', pattern='^(pending|in_progress|completed|blocked)$')
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
