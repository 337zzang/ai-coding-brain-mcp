"""
WorkflowManager 중심 아키텍처를 위한 데이터 모델
"""
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class TaskStatus(str, Enum):
    """작업 상태"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    
    
class PhaseStatus(str, Enum):
    """Phase 상태"""
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


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
    tasks: List[Task] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    
    def add_task(self, task: Task) -> None:
        """작업 추가"""
        task.phase_id = self.id
        self.tasks.append(task)
    
    def get_pending_tasks(self) -> List[Task]:
        """대기 중인 작업 목록"""
        return [t for t in self.tasks if t.status == TaskStatus.PENDING]
    
    def get_active_task(self) -> Optional[Task]:
        """진행 중인 작업"""
        for task in self.tasks:
            if task.status == TaskStatus.IN_PROGRESS:
                return task
        return None
    
    def is_complete(self) -> bool:
        """Phase 완료 여부"""
        return all(t.status == TaskStatus.COMPLETED for t in self.tasks)
    
    def update_status(self) -> None:
        """Phase 상태 업데이트"""
        if self.is_complete():
            self.status = PhaseStatus.COMPLETED
        elif any(t.status != TaskStatus.PENDING for t in self.tasks):
            self.status = PhaseStatus.IN_PROGRESS


class Plan(BaseModel):
    """계획 모델"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    phases: List[Phase] = Field(default_factory=list)
    current_phase_id: Optional[str] = None
    current_task_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    
    def add_phase(self, phase: Phase) -> None:
        """Phase 추가"""
        self.phases.append(phase)
        if not self.current_phase_id:
            self.current_phase_id = phase.id
    
    def get_current_phase(self) -> Optional[Phase]:
        """현재 Phase 조회"""
        if not self.current_phase_id:
            return None
        for phase in self.phases:
            if phase.id == self.current_phase_id:
                return phase
        return None
    
    def get_current_task(self) -> Optional[Task]:
        """현재 작업 조회"""
        if not self.current_task_id:
            return None
        for phase in self.phases:
            for task in phase.tasks:
                if task.id == self.current_task_id:
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
            current_index = next((i for i, p in enumerate(self.phases) if p.id == self.current_phase_id), -1)
            for i in range(current_index + 1, len(self.phases)):
                phase = self.phases[i]
                pending_tasks = phase.get_pending_tasks()
                if pending_tasks:
                    self.current_phase_id = phase.id
                    return pending_tasks[0]
        
        return None
    
    def get_all_tasks(self) -> List[Task]:
        """모든 작업 목록"""
        tasks = []
        for phase in self.phases:
            tasks.extend(phase.tasks)
        return tasks
    
    def get_progress(self) -> float:
        """전체 진행률 (0-100)"""
        all_tasks = self.get_all_tasks()
        if not all_tasks:
            return 0.0
        completed = sum(1 for t in all_tasks if t.status == TaskStatus.COMPLETED)
        return (completed / len(all_tasks)) * 100


class WorkflowState(BaseModel):
    """워크플로우 전체 상태"""
    project_name: str
    plan: Optional[Plan] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def update(self) -> None:
        """업데이트 시간 갱신"""
        self.updated_at = datetime.now()
