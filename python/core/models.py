"""
AI Coding Brain Pydantic ?°ì´??ëª¨ë¸
ë²„ì „: 1.0
?‘ì„±?? 2025-06-24

??ëª¨ë“ˆ?€ ?„ë¡œ?íŠ¸??ëª¨ë“  ?°ì´??êµ¬ì¡°ë¥?Pydantic ëª¨ë¸ë¡??•ì˜?©ë‹ˆ??
?€???ˆì •?±ê³¼ ?ë™ ê²€ì¦ì„ ?œê³µ?˜ì—¬ ?°í????¤ë¥˜ë¥?ë°©ì??©ë‹ˆ??
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import json


class TaskStatus(str, Enum):
    """?‘ì—…???íƒœë¥??•ì˜?˜ëŠ” Enum"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELED = "canceled"


class BaseModelWithConfig(BaseModel):
    """
    JSON ì§ë ¬?”ì? Path ê°ì²´ ì²˜ë¦¬ë¥??„í•œ ê¸°ë³¸ ëª¨ë¸
    """
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            Path: str,
            datetime: lambda v: v.isoformat() if v else None
        }
        
    def model_dump(self, **kwargs):
        """Path ê°ì²´ë¥?ë¬¸ì?´ë¡œ ë³€?˜í•˜??ë°˜í™˜"""
        d = super().model_dump(**kwargs)
        return self._convert_paths_to_str(d)
    
    # ?˜ìœ„ ?¸í™˜?±ì„ ?„í•œ ë³„ì¹­
    def dict(self, **kwargs):
        """?˜ìœ„ ?¸í™˜?±ì„ ?„í•œ ë³„ì¹­ (deprecated)"""
        return self.model_dump(**kwargs)
    
    def _convert_paths_to_str(self, obj):
        """?¬ê??ìœ¼ë¡?Path ê°ì²´ë¥?ë¬¸ì?´ë¡œ ë³€??""
        if isinstance(obj, dict):
            return {k: self._convert_paths_to_str(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_paths_to_str(item) for item in obj]
        elif isinstance(obj, Path):
            return str(obj)
        return obj


class Task(BaseModelWithConfig):
    """?‘ì—…(Task) ëª¨ë¸"""
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
    dependencies: List[str] = Field(default_factory=list)  # ?˜ì¡´???‘ì—… ID ëª©ë¡
    related_files: List[str] = Field(default_factory=list)  # ê´€???Œì¼ ëª©ë¡
    
    # ?íƒœ ê´€ë¦?ê°•í™” ?„ë“œ
    state_history: List[Dict[str, Any]] = Field(default_factory=list)  # ?íƒœ ë³€ê²??´ë ¥
    blocking_reason: Optional[str] = None  # ì°¨ë‹¨ ?´ìœ 
    estimated_hours: Optional[float] = None  # ?ˆìƒ ?Œìš” ?œê°„
    actual_hours: Optional[float] = None  # ?¤ì œ ?Œìš” ?œê°„
    
    # ?˜ì¡´???•ì¥
    blocks: List[str] = Field(default_factory=list)  # ???‘ì—…??ì°¨ë‹¨?˜ëŠ” ?‘ì—… ID??
    
    # ?ë™??ë°??µí•© ?•ë³´
    auto_generated: bool = False  # ProjectAnalyzerê°€ ?ë™ ?ì„±?ˆëŠ”ì§€
    wisdom_hints: List[str] = Field(default_factory=list)  # Wisdom ?œìŠ¤???ŒíŠ¸
    context_data: Dict[str, Any] = Field(default_factory=dict)  # Taskë³??…ë¦½ ì»¨í…?¤íŠ¸
    
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
        """?‘ì—…???„ë£Œ ?íƒœë¡??œì‹œ"""
        self.completed = True
        self.status = 'completed'
        self.completed_at = datetime.now()
    
    def mark_started(self):
        """?‘ì—…???œì‘ ?íƒœë¡??œì‹œ"""
        self.status = 'in_progress'
        self.started_at = datetime.now()
    
    def get_priority_value(self) -> int:
        """?°ì„ ?œìœ„ë¥??«ìë¡?ë³€??(?•ë ¬??"""
        priority_map = {'high': 3, 'medium': 2, 'low': 1}
        return priority_map.get(self.priority, 2)
    
    def transition_to(self, new_status: str) -> bool:
        """? íš¨???íƒœ ?„í™˜ ?˜í–‰
        
        Args:
            new_status: ?„í™˜???íƒœ
            
        Returns:
            bool: ?„í™˜ ?±ê³µ ?¬ë?
        """
        # ? íš¨???íƒœ ?„í™˜ ê·œì¹™
        valid_transitions = {
            'pending': ['ready', 'blocked', 'cancelled'],
            'ready': ['in_progress', 'blocked', 'cancelled'],
            'blocked': ['ready', 'cancelled'],
            'in_progress': ['completed', 'blocked', 'cancelled'],
            'completed': [],  # ?„ë£Œ???‘ì—…?€ ?íƒœ ë³€ê²?ë¶ˆê?
            'cancelled': []   # ì·¨ì†Œ???‘ì—…?€ ?íƒœ ë³€ê²?ë¶ˆê?
        }
        
        current_valid = valid_transitions.get(self.status, [])
        
        if new_status not in current_valid:
            return False
        
        # ?íƒœ ?„í™˜
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now()
        
        # ?íƒœ ?´ë ¥ ê¸°ë¡
        self.state_history.append({
            'from': old_status,
            'to': new_status,
            'timestamp': self.updated_at,
            'reason': self.blocking_reason if new_status == 'blocked' else None
        })
        
        # ?íƒœë³?ì¶”ê? ì²˜ë¦¬
        if new_status == 'in_progress':
            self.started_at = datetime.now()
        elif new_status == 'completed':
            self.completed_at = datetime.now()
            self.completed = True
            # ?¤ì œ ?Œìš” ?œê°„ ê³„ì‚°
            if self.started_at:
                self.actual_hours = (self.completed_at - self.started_at).total_seconds() / 3600
        elif new_status == 'blocked':
            # blocking_reason?€ transition_to ?¸ì¶œ ?„ì— ?¤ì •?˜ì–´????
            pass
        
        return True
    
    def can_start(self) -> bool:
        """?‘ì—… ?œì‘ ê°€???¬ë? ?•ì¸
        
        Returns:
            bool: ?œì‘ ê°€?¥í•˜ë©?True
        """
        # ?œì‘ ê°€?¥í•œ ?íƒœ: pending ?ëŠ” ready
        return self.status in ['pending', 'ready']
    
    def check_dependencies(self) -> List[str]:
        """ì¶©ì¡±?˜ì? ?Šì? ?˜ì¡´??ëª©ë¡ ë°˜í™˜
        
        Returns:
            List[str]: ì¶©ì¡±?˜ì? ?Šì? ?˜ì¡´??ID ëª©ë¡
        """
        # ?¤ì œ ?˜ì¡´??ì²´í¬??Plan ?ˆë²¨?ì„œ ?˜í–‰
        # ?¬ê¸°?œëŠ” ?˜ì¡´??ëª©ë¡ë§?ë°˜í™˜
        return self.dependencies if self.dependencies else []
    
    def add_dependency(self, task_id: str) -> None:
        """?˜ì¡´??ì¶”ê?
        
        Args:
            task_id: ?˜ì¡´???‘ì—… ID
        """
        if not self.dependencies:
            self.dependencies = []
        
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)
            self.updated_at = datetime.now()
    
    def remove_dependency(self, task_id: str) -> None:
        """?˜ì¡´???œê±°
        
        Args:
            task_id: ?œê±°???˜ì¡´???‘ì—… ID
        """
        if self.dependencies and task_id in self.dependencies:
            self.dependencies.remove(task_id)
            self.updated_at = datetime.now()
    
    def get_time_in_state(self, state: Optional[str] = None) -> float:
        """?¹ì • ?íƒœ(?ëŠ” ?„ì¬ ?íƒœ)??ë¨¸ë¬¸ ?œê°„ ê³„ì‚° (?œê°„ ?¨ìœ„)
        
        Args:
            state: ì¡°íšŒ???íƒœ (None?´ë©´ ?„ì¬ ?íƒœ)
            
        Returns:
            float: ?´ë‹¹ ?íƒœ??ë¨¸ë¬¸ ?œê°„ (?œê°„ ?¨ìœ„)
        """
        if state is None:
            state = self.status
        
        total_hours = 0.0
        
        # ?íƒœ ?´ë ¥?ì„œ ?´ë‹¹ ?íƒœ??ë¨¸ë¬¸ ?œê°„ ê³„ì‚°
        for i, entry in enumerate(self.state_history):
            if entry['to'] == state:
                # ?¤ìŒ ?íƒœ ë³€ê²½ê¹Œì§€???œê°„ ê³„ì‚°
                if i + 1 < len(self.state_history):
                    next_entry = self.state_history[i + 1]
                    duration = next_entry['timestamp'] - entry['timestamp']
                else:
                    # ë§ˆì?ë§??íƒœë©??„ì¬ê¹Œì????œê°„
                    duration = datetime.now() - entry['timestamp']
                
                total_hours += duration.total_seconds() / 3600
        
        # ?„ì¬ ?íƒœê°€ ?”ì²­???íƒœ?€ ê°™ê³  ?´ë ¥???†ìœ¼ë©?
        if state == self.status and total_hours == 0:
            if state == 'in_progress' and self.started_at:
                total_hours = (datetime.now() - self.started_at).total_seconds() / 3600
            elif state == 'completed' and self.completed_at and self.started_at:
                total_hours = (self.completed_at - self.started_at).total_seconds() / 3600
        
        return total_hours
    
    def set_blocking_reason(self, reason: str) -> None:
        """ì°¨ë‹¨ ?´ìœ  ?¤ì •
        
        Args:
            reason: ì°¨ë‹¨ ?´ìœ 
        """
        self.blocking_reason = reason
        self.updated_at = datetime.now()
    
    def estimate_completion_time(self) -> Optional[datetime]:
        """?ˆìƒ ?„ë£Œ ?œê°„ ê³„ì‚°
        
        Returns:
            Optional[datetime]: ?ˆìƒ ?„ë£Œ ?œê°„
        """
        if self.status == 'completed':
            return self.completed_at
        
        if self.status == 'in_progress' and self.started_at and self.estimated_hours:
            # ?œì‘ ?œê°„ + ?ˆìƒ ?Œìš” ?œê°„
            return self.started_at + timedelta(hours=self.estimated_hours)
        
        return None
    
    def get_progress_percentage(self) -> float:
        """?‘ì—… ì§„í–‰ë¥?ê³„ì‚° (0-100)
        
        Returns:
            float: ì§„í–‰ë¥?(0-100)
        """
        if self.status == 'completed':
            return 100.0
        elif self.status == 'in_progress' and self.started_at and self.estimated_hours:
            elapsed = (datetime.now() - self.started_at).total_seconds() / 3600
            return min(100.0, (elapsed / self.estimated_hours) * 100)
        else:
            return 0.0


class Phase(BaseModelWithConfig):
    """?¨ê³„(Phase) ëª¨ë¸"""
    id: str
    name: str
    description: str = ""
    status: str = Field(default='pending', pattern='^(pending|in_progress|completed)$')
    
    # Task ?œì„œ ë°?ì§„í–‰ë¥?ê´€ë¦?
    task_order: List[str] = Field(default_factory=list)  # Task ?œì‹œ ?œì„œ
    progress: float = 0.0  # Phase ì§„í–‰ë¥?(0-100%)
    completed_tasks: int = 0  # ?„ë£Œ??Task ??
    total_tasks: int = 0  # ?„ì²´ Task ??
    
    # Phase ë©”í??°ì´??
    estimated_days: Optional[float] = None  # ?ˆìƒ ?Œìš” ?¼ìˆ˜
    started_at: Optional[datetime] = None  # Phase ?œì‘ ?œê°„
    completed_at: Optional[datetime] = None  # Phase ?„ë£Œ ?œê°„
    tasks: Dict[str, Task] = Field(default_factory=dict)
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """IDë¡??‘ì—… ì°¾ê¸°"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def add_task(self, title: str, description: str = "") -> Task:
        """???‘ì—… ì¶”ê?"""
        task_id = f"{self.id.split('-')[1]}-{len(self.tasks) + 1}"
        task = Task(
            id=task_id,
            title=title,
            description=description,
            phase_id=self.id
        )
        self.tasks[task_id] = task
        self.task_order.append(task_id)  # ?œì„œ ê¸°ë¡
        return task
    
    @property
    def progress(self) -> Dict[str, Any]:
        """ì§„í–‰ë¥?ê³„ì‚°"""
        total = len(self.tasks)
        completed = len([t for t in self.tasks.values() if t.completed])
        return {
            'total': total,
            'completed': completed,
            'percentage': (completed / total * 100) if total > 0 else 0
        }
    
    def get_progress_details(self) -> Dict[str, Any]:
        """?ì„¸ ì§„í–‰ ?í™© ë°˜í™˜
        
        Returns:
            Dict[str, Any]: ?íƒœë³??‘ì—… ?? ì§„í–‰ë¥????ì„¸ ?•ë³´
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
        """?„ì¬ ì§„í–‰ ì¤‘ì¸ ?‘ì—… ë°˜í™˜
        
        Returns:
            Optional[Task]: ì§„í–‰ ì¤‘ì¸ ?‘ì—… (?†ìœ¼ë©?None)
        """
        for task in self.tasks:
            if task.status == 'in_progress':
                return task
        return None
    
    def can_complete(self) -> bool:
        """Phase ?„ë£Œ ê°€???¬ë? ?•ì¸
        
        Returns:
            bool: ëª¨ë“  ?‘ì—…???„ë£Œ/ì·¨ì†Œ?˜ì—ˆ?¼ë©´ True
        """
        for task in self.tasks:
            if task.status not in ['completed', 'cancelled']:
                return False
        return True
    
    def estimate_remaining_time(self) -> float:
        """?¨ì? ?ˆìƒ ?œê°„ ê³„ì‚° (?œê°„ ?¨ìœ„)
        
        Returns:
            float: ?¨ì? ?ˆìƒ ?œê°„
        """
        remaining_hours = 0.0
        
        for task in self.tasks:
            if task.status in ['pending', 'ready', 'blocked']:
                # ?ˆìƒ ?œê°„???¤ì •??ê²½ìš°
                if task.estimated_hours:
                    remaining_hours += task.estimated_hours
            elif task.status == 'in_progress':
                # ì§„í–‰ ì¤‘ì¸ ?‘ì—…???¨ì? ?œê°„
                if task.estimated_hours and task.started_at:
                    elapsed = (datetime.now() - task.started_at).total_seconds() / 3600
                    remaining = max(0, task.estimated_hours - elapsed)
                    remaining_hours += remaining
        
        return remaining_hours
    
    def get_next_task(self) -> Optional[Task]:
        """Phase ?´ì—???¤ìŒ ?¤í–‰???‘ì—… ë°˜í™˜
        
        Returns:
            Optional[Task]: ?¤ìŒ ?‘ì—… (?†ìœ¼ë©?None)
        """
        # pending?´ë‚˜ ready ?íƒœ???‘ì—… ì¤??°ì„ ?œìœ„ê°€ ê°€???’ì? ê²?
        available_tasks = [t for t in self.tasks if t.status in ['pending', 'ready']]
        
        if not available_tasks:
            return None
        
        # ?°ì„ ?œìœ„ë¡??•ë ¬
        available_tasks.sort(key=lambda t: t.get_priority_value(), reverse=True)
        return available_tasks[0]


class Plan(BaseModelWithConfig):
    """ê³„íš(Plan) ëª¨ë¸"""
    name: str
    description: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    phases: Dict[str, Phase] = Field(default_factory=dict)  # Phase ID -> Phase ê°ì²´
    current_phase: Optional[str] = None  # ?„ì¬ ì§„í–‰ ì¤‘ì¸ Phase ID
    current_task: Optional[str] = None  # ?„ì¬ ì§„í–‰ ì¤‘ì¸ Task ID
    
    # Phase ?œì„œ ë°?ì§„í–‰ë¥?ê´€ë¦?
    phase_order: List[str] = Field(default_factory=list)  # Phase ?œì‹œ ?œì„œ
    overall_progress: float = 0.0  # ?„ì²´ ì§„í–‰ë¥?(0-100%)
    
    # ?µí•© ?•ë³´
    project_insights: Dict[str, Any] = Field(default_factory=dict)  # ProjectAnalyzer ë¶„ì„ ê²°ê³¼
    wisdom_data: Dict[str, Any] = Field(default_factory=dict)  # Wisdom ?œìŠ¤???°ì´??
    
    
    def get_all_tasks(self) -> List[Task]:
        """ëª¨ë“  Phase??Taskë¥??˜ë‚˜??ë¦¬ìŠ¤?¸ë¡œ ë°˜í™˜"""
        all_tasks = []
        for phase in self.phases.values():
            all_tasks.extend(phase.tasks.values())
        return all_tasks
    
    def get_current_task(self) -> Optional[Task]:
        """?„ì¬ ì§„í–‰ ì¤‘ì¸ Task ë°˜í™˜"""
        for task in self.get_all_tasks():
            if task.status == TaskStatus.IN_PROGRESS:
                return task
        return None
    
    def get_next_tasks(self) -> List[Task]:
        """?¤ìŒ???˜í–‰ ê°€?¥í•œ Task ëª©ë¡ ë°˜í™˜"""
        next_tasks = []
        all_tasks = self.get_all_tasks()
        
        for task in all_tasks:
            if task.status in [TaskStatus.PENDING, TaskStatus.READY]:
                # ?˜ì¡´??ì²´í¬
                if not task.dependencies:
                    next_tasks.append(task)
                else:
                    # ëª¨ë“  ?˜ì¡´?±ì´ ?„ë£Œ?˜ì—ˆ?”ì? ?•ì¸
                    deps_completed = all(
                        any(t.id == dep_id and t.status == TaskStatus.COMPLETED 
                            for t in all_tasks)
                        for dep_id in task.dependencies
                    )
                    if deps_completed:
                        next_tasks.append(task)
        
        return next_tasks
    
    def update_progress(self) -> None:
        """Phase?€ ?„ì²´ Plan??ì§„í–‰ë¥??…ë°?´íŠ¸"""
        total_tasks = 0
        completed_tasks = 0
        
        # ê°?Phase??ì§„í–‰ë¥?ê³„ì‚°
        for phase in self.phases.values():
            phase_tasks = list(phase.tasks.values())
            phase.total_tasks = len(phase_tasks)
            phase.completed_tasks = sum(1 for t in phase_tasks if t.status == TaskStatus.COMPLETED)
            phase.progress = (phase.completed_tasks / phase.total_tasks * 100) if phase.total_tasks > 0 else 0.0
            
            total_tasks += phase.total_tasks
            completed_tasks += phase.completed_tasks
        
        # ?„ì²´ ì§„í–‰ë¥?ê³„ì‚°

    def get_next_task(self) -> Optional[Tuple[str, Task]]:
        """?¤ìŒ???˜í–‰???‘ì—… ë°˜í™˜ (phase_id, task)"""
        for phase_id in self.phase_order:
            phase = self.phases.get(phase_id)
            if phase and phase.status != 'completed':
                # Task order???°ë¼ ?œì„œ?€ë¡??•ì¸
                for task_id in phase.task_order:
                    task = phase.tasks.get(task_id)
                    if task and task.status == TaskStatus.PENDING:
                        return phase_id, task
        return None
        self.overall_progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
class WorkTracking(BaseModelWithConfig):
    """?‘ì—… ì¶”ì  ëª¨ë¸"""
    file_access: Dict[str, Any] = Field(default_factory=dict)  # ??? ì—°???€??
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
    """?Œì¼ ?‘ê·¼ ê¸°ë¡ ??ª©"""
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
    """?„ë¡œ?íŠ¸ ì»¨í…?¤íŠ¸ - ë©”ì¸ ëª¨ë¸"""
    # ê¸°ë³¸ ?•ë³´
    project_name: str
    project_id: str
    project_path: Union[str, Path]
    memory_root: Union[str, Path]
    
    # ?œê°„ ?•ë³´
    created_at: Union[datetime, str] = Field(default_factory=datetime.now)
    updated_at: Union[datetime, str] = Field(default_factory=datetime.now)
    
    # ë²„ì „ ë°?ë©”í??°ì´??
    version: str = "7.0"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # ?‘ì—… ê´€??
    plan: Optional[Plan] = None
    current_focus: str = ""
    current_task: Optional[str] = None
    tasks: Dict[str, List[Any]] = Field(default_factory=lambda: {'next': [], 'done': []})
    
    # ë¶„ì„ ë°?ì¶”ì 
    analyzed_files: Dict[str, Any] = Field(default_factory=dict)
    work_tracking: Union[WorkTracking, Dict[str, Any]] = Field(default_factory=WorkTracking)
    file_access_history: List[Union[FileAccessEntry, Dict[str, Any]]] = Field(default_factory=list)
    
    # ê¸°í?
    plan_history: List[Dict[str, Any]] = Field(default_factory=list)
    coding_experiences: List[str] = Field(default_factory=list)
    progress: Dict[str, Any] = Field(default_factory=lambda: {
        'completed_tasks': 0,
        'total_tasks': 0,
        'percentage': 0.0
    })
    phase_reports: Dict[str, Any] = Field(default_factory=dict)
    error_log: List[Dict[str, Any]] = Field(default_factory=list)
    
    # ì¶”ê? ?„ë“œ (? íƒ??
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
        """?„ì¬ ?¨ê³„ ë°˜í™˜"""
        if self.plan:
            return self.plan.get_current_phase()
        return None
    
    def get_all_tasks(self) -> List[Task]:
        """ëª¨ë“  ?‘ì—… ë°˜í™˜"""
        if self.plan:
            return self.plan.get_all_tasks()
        return []
    
    def update_progress(self):
        """ì§„í–‰ë¥??…ë°?´íŠ¸"""
        if self.plan:
            progress_info = self.plan.overall_progress
            self.progress.update(progress_info)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectContext':
        """?•ì…”?ˆë¦¬?ì„œ ProjectContext ?ì„±"""
        # Plan ?°ì´??ì²˜ë¦¬
        if 'plan' in data and data['plan'] and isinstance(data['plan'], dict):
            plan_data = data['plan'].copy()
            # phases ì²˜ë¦¬
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
        """JSON ë¬¸ì?´ë¡œ ë³€??""
        return json.dumps(self.model_dump(), indent=2, ensure_ascii=False, default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ProjectContext':
        """JSON ë¬¸ì?´ì—???ì„±"""
        data = json.loads(json_str)
        return cls.from_dict(data)


# ? í‹¸ë¦¬í‹° ?¨ìˆ˜
def validate_context_data(data: Dict[str, Any]) -> Optional[ProjectContext]:
    """ì»¨í…?¤íŠ¸ ?°ì´??ê²€ì¦?ë°?ë³€??""
    try:
        return ProjectContext.from_dict(data)
    except Exception as e:
        print(f"??ì»¨í…?¤íŠ¸ ?°ì´??ê²€ì¦??¤íŒ¨: {e}")
        return None
