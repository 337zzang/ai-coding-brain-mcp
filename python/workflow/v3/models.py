"""
Workflow v3 데이터 모델
이벤트 기반 아키텍처를 위한 개선된 모델
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta

# 한국 표준시(KST) 정의
KST = timezone(timedelta(hours=9))
from enum import Enum
from typing import List, Dict, Any, Optional
import uuid
import json

# 통합 이벤트 타입 import
from events.unified_event_types import EventType

# v3에서 추가된 에러 처리 import
try:
    from .errors import InputValidator, WorkflowError
except ImportError:
    # 순환 참조 방지를 위한 폴백
    InputValidator = None
    WorkflowError = None


class TaskStatus(str, Enum):
    """태스크 상태"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PlanStatus(str, Enum):
    """플랜 상태"""
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass
class WorkflowEvent:
    """워크플로우 이벤트"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType = EventType.PLAN_CREATED
    timestamp: datetime = field(default_factory=lambda: datetime.now(KST))
    plan_id: str = ""
    task_id: Optional[str] = None
    user: str = "system"
    details: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """이벤트를 딕셔너리로 변환"""
        return {
            'id': self.id,
            'type': self.type.value,
            'timestamp': self.timestamp.isoformat(),
            'plan_id': self.plan_id,
            'task_id': self.task_id,
            'user': self.user,
            'details': self.details,
            'metadata': self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowEvent':
        """딕셔너리에서 이벤트 생성"""
        timestamp_str = data.get('timestamp', datetime.now(KST).isoformat())
        # Handle both offset-aware and naive datetime strings
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=KST)
        except:
            timestamp = datetime.now(KST)
            
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            type=EventType(data.get('type', 'plan_created')),
            timestamp=timestamp,
            plan_id=data.get('plan_id', ''),
            task_id=data.get('task_id'),
            user=data.get('user', 'system'),
            details=data.get('details', {}),
            metadata=data.get('metadata', {})
        )
    
    @classmethod
    def create_plan_event(cls, event_type: EventType, plan: 'WorkflowPlan', **kwargs) -> 'WorkflowEvent':
        """플랜 관련 이벤트 생성 헬퍼"""
        details = {
            "plan_id": plan.id,
            "plan_name": plan.name,
            "plan_status": plan.status.value,
            **kwargs
        }
        return cls(type=event_type, plan_id=plan.id, details=details)
    
    @classmethod
    def create_task_event(cls, event_type: EventType, task: 'WorkflowTask', plan_id: str, **kwargs) -> 'WorkflowEvent':
        """태스크 관련 이벤트 생성 헬퍼"""
        details = {
            "task_id": task.id,
            "task_title": task.title,
            "task_status": task.status.value,
            **kwargs
        }
        return cls(type=event_type, plan_id=plan_id, task_id=task.id, details=details)
    
    @classmethod
    def create_note_event(cls, event_type: EventType, task_id: str, plan_id: str, note: str, **kwargs) -> 'WorkflowEvent':
        """노트 관련 이벤트 생성 헬퍼"""
        details = {
            "task_id": task_id,
            "note": note,
            "timestamp": datetime.now(KST).isoformat(),
            **kwargs
        }
        return cls(type=event_type, plan_id=plan_id, task_id=task_id, details=details)
    
    @classmethod
    def create_system_event(cls, event_type: EventType, message: str, plan_id: str = "", **kwargs) -> 'WorkflowEvent':
        """시스템 관련 이벤트 생성 헬퍼"""
        details = {
            "message": message,
            "timestamp": datetime.now(KST).isoformat(),
            **kwargs
        }
        return cls(type=event_type, plan_id=plan_id, details=details)


@dataclass
class Task:
    """개선된 태스크 모델 v3"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    status: TaskStatus = TaskStatus.TODO
    created_at: datetime = field(default_factory=lambda: datetime.now(KST))
    updated_at: datetime = field(default_factory=lambda: datetime.now(KST))
    started_at: Optional[datetime] = None  # v3 추가
    completed_at: Optional[datetime] = None
    duration: Optional[int] = None  # v3 추가 - 소요시간(초)
    notes: List[str] = field(default_factory=list)
    outputs: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """생성 후 검증"""
        if InputValidator:
            self.title = InputValidator.validate_title(self.title, "태스크 제목")
            self.description = InputValidator.validate_description(self.description)
        else:
            # 폴백: 기본 검증
            if not self.title or not self.title.strip():
                raise ValueError("태스크 제목은 필수입니다")
            self.title = self.title.strip()
            if len(self.title) > 200:
                raise ValueError("태스크 제목은 200자를 초과할 수 없습니다")
    
    def start(self) -> None:
        """태스크 시작"""
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.now(KST)
        self.updated_at = datetime.now(KST)
        
    def complete(self, note: str = "") -> None:
        """태스크 완료"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now(KST)
        self.updated_at = datetime.now(KST)
        
        if self.started_at:
            self.duration = int((self.completed_at - self.started_at).total_seconds())
            
        if note:
            self.notes.append(f"[완료] {note}")
    
    def fail(self, error: str) -> None:
        """태스크 실패"""
        self.status = TaskStatus.CANCELLED  # FAILED가 없으므로 CANCELLED 사용
        self.updated_at = datetime.now(KST)
        self.notes.append(f"[실패] {error}")
        
    def block(self, blocker: str) -> None:
        """태스크 차단"""
        # 현재 상태를 outputs에 저장
        if 'previous_status' not in self.outputs:
            self.outputs['previous_status'] = self.status.value
        self.outputs['blocker'] = blocker
        self.outputs['blocked_at'] = datetime.now(KST).isoformat()
        self.updated_at = datetime.now(KST)
        self.notes.append(f"[차단] {blocker}")
        
    def unblock(self) -> None:
        """태스크 차단 해제"""
        if 'previous_status' in self.outputs:
            # 이전 상태로 복원
            prev_status = self.outputs.pop('previous_status', TaskStatus.TODO.value)
            self.status = TaskStatus(prev_status)
        if 'blocker' in self.outputs:
            del self.outputs['blocker']
        if 'blocked_at' in self.outputs:
            del self.outputs['blocked_at']
        self.updated_at = datetime.now(KST)
        self.notes.append("[차단 해제]")
        
    def cancel(self, reason: str = "") -> None:
        """태스크 취소"""
        self.status = TaskStatus.CANCELLED
        self.updated_at = datetime.now(KST)
        if reason:
            self.notes.append(f"[취소] {reason}")
        else:
            self.notes.append("[취소]")
    
    def to_dict(self) -> Dict[str, Any]:
        """객체를 딕셔너리로 변환"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration': self.duration,
            'notes': self.notes,
            'outputs': self.outputs
        }

    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """딕셔너리에서 객체 생성"""
        # 타임스탬프 처리
        created_at = cls._parse_datetime(data.get('created_at'))
        updated_at = cls._parse_datetime(data.get('updated_at'))
        started_at = cls._parse_datetime(data.get('started_at')) if data.get('started_at') else None
        completed_at = cls._parse_datetime(data.get('completed_at')) if data.get('completed_at') else None
        
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            title=data.get('title', ''),
            description=data.get('description', ''),
            status=TaskStatus(data.get('status', 'todo')),
            created_at=created_at,
            updated_at=updated_at,
            started_at=started_at,
            completed_at=completed_at,
            duration=data.get('duration'),
            notes=data.get('notes', []),
            outputs=data.get('outputs', {})
        )
    
    @staticmethod
    def _parse_datetime(dt_str: Optional[str]) -> datetime:
        """날짜/시간 문자열 파싱"""
        if not dt_str:
            return datetime.now(KST)
        try:
            dt = datetime.fromisoformat(dt_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=KST)
            return dt
        except:
            return datetime.now(KST)


@dataclass
class WorkflowPlan:
    """개선된 워크플로우 플랜 모델 v3"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    status: PlanStatus = PlanStatus.DRAFT
    tasks: List[Task] = field(default_factory=list)
    current_task_index: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(KST))
    updated_at: datetime = field(default_factory=lambda: datetime.now(KST))
    completed_at: Optional[datetime] = None  # v3 추가
    archived_at: Optional[datetime] = None  # v3 추가
    stats: Dict[str, Any] = field(default_factory=dict)  # v3 추가
    metadata: Dict[str, Any] = field(default_factory=dict)

    
    def __post_init__(self):
        """생성 후 검증"""
        if InputValidator:
            self.name = InputValidator.validate_title(self.name, "플랜 이름")
            self.description = InputValidator.validate_description(self.description)
        else:
            # 폴백: 기본 검증
            if not self.name or not self.name.strip():
                raise ValueError("플랜 이름은 필수입니다")
            self.name = self.name.strip()
            if len(self.name) > 200:
                raise ValueError("플랜 이름은 200자를 초과할 수 없습니다")
            
    def start(self) -> None:
        """플랜 시작"""
        self.status = PlanStatus.ACTIVE
        self.updated_at = datetime.now(KST)
        
    def complete(self) -> None:
        """플랜 완료"""
        self.status = PlanStatus.COMPLETED
        self.completed_at = datetime.now(KST)
        self.updated_at = datetime.now(KST)
        self._update_stats()
        
    def archive(self) -> None:
        """플랜 보관 처리"""
        self.status = PlanStatus.ARCHIVED
        self.archived_at = datetime.now(KST)
        self.updated_at = datetime.now(KST)
        self._update_stats()

    def archive(self) -> None:
        """플랜 아카이브"""
        if self.status != PlanStatus.COMPLETED:
            self.complete()
        self.status = PlanStatus.ARCHIVED
        self.archived_at = datetime.now(KST)
        self.updated_at = datetime.now(KST)
        
    def _update_stats(self) -> None:
        """통계 정보 업데이트"""
        total_tasks = len(self.tasks)
        completed_tasks = len([t for t in self.tasks if t.status == TaskStatus.COMPLETED])
        total_duration = sum(t.duration or 0 for t in self.tasks)
        
        self.stats = {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completion_rate': completed_tasks / total_tasks if total_tasks > 0 else 0,
            'total_duration_seconds': total_duration,
            'average_task_duration': total_duration / completed_tasks if completed_tasks > 0 else 0
        }
        
    def get_current_task(self) -> Optional[Task]:
        """현재 작업 중인 태스크 반환"""
        # current_task_index가 유효하면 해당 태스크 반환
        if 0 <= self.current_task_index < len(self.tasks):
            task = self.tasks[self.current_task_index]
            # 완료되지 않은 태스크만 반환
            if task.status in [TaskStatus.TODO, TaskStatus.IN_PROGRESS]:
                return task
        
        # 폴백: 첫 번째 미완료 태스크 찾기
        for i, task in enumerate(self.tasks):
            if task.status in [TaskStatus.TODO, TaskStatus.IN_PROGRESS]:
                # current_task_index 자동 업데이트
                self.current_task_index = i
                return task
        
        return None

        
    def to_dict(self) -> Dict[str, Any]:
        """객체를 딕셔너리로 변환"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status.value,
            'tasks': [task.to_dict() for task in self.tasks],
            'current_task_index': self.current_task_index,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'archived_at': self.archived_at.isoformat() if self.archived_at else None,
            'stats': self.stats,
            'metadata': self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowPlan':
        """딕셔너리에서 객체 생성"""
        # 타임스탬프 처리
        created_at = Task._parse_datetime(data.get('created_at'))
        updated_at = Task._parse_datetime(data.get('updated_at'))
        completed_at = Task._parse_datetime(data.get('completed_at')) if data.get('completed_at') else None
        archived_at = Task._parse_datetime(data.get('archived_at')) if data.get('archived_at') else None
        
        # 태스크 복원
        tasks = [Task.from_dict(task_data) for task_data in data.get('tasks', [])]
        
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            name=data.get('name', ''),
            description=data.get('description', ''),
            status=PlanStatus(data.get('status', 'draft')),
            tasks=tasks,
            current_task_index=data.get('current_task_index', 0),
            created_at=created_at,
            updated_at=updated_at,
            completed_at=completed_at,
            archived_at=archived_at,
            stats=data.get('stats', {}),
            metadata=data.get('metadata', {})
        )


@dataclass
class WorkflowState:
    """워크플로우 전체 상태 관리"""
    current_plan: Optional[WorkflowPlan] = None
    events: List[WorkflowEvent] = field(default_factory=list)
    version: str = "3.0.0"
    last_saved: datetime = field(default_factory=lambda: datetime.now(KST))
    metadata: Dict[str, Any] = field(default_factory=dict)

    
    def add_event(self, event: WorkflowEvent) -> None:
        """이벤트 추가"""
        self.events.append(event)
        self.last_saved = datetime.now(KST)
        
    def get_all_plans(self) -> List[WorkflowPlan]:
        """모든 플랜 반환 (현재는 current_plan만)"""
        return [self.current_plan] if self.current_plan else []
        
    def to_dict(self) -> Dict[str, Any]:
        """상태를 딕셔너리로 변환 (v46: plans + active_plan_id 구조)"""
        # 새로운 구조: plans 배열과 active_plan_id 사용
        plans = []
        active_plan_id = None
        
        if self.current_plan:
            plans = [self.current_plan.to_dict()]
            active_plan_id = self.current_plan.id
            
        return {
            'plans': plans,
            'active_plan_id': active_plan_id,
            'events': [event.to_dict() for event in self.events],
            'version': self.version,
            'last_saved': self.last_saved.isoformat(),
            'metadata': self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowState':
        """딕셔너리에서 상태 복원 (개선된 버전)"""
        current_plan = None
        
        # 새로운 구조: plans 배열과 active_plan_id 처리
        if data.get('plans') and data.get('active_plan_id'):
            # plans 배열에서 active_plan 찾기
            for plan_data in data['plans']:
                if plan_data.get('id') == data['active_plan_id']:
                    current_plan = WorkflowPlan.from_dict(plan_data)
                    break
        # 기존 구조 지원 (backward compatibility)
        elif data.get('current_plan'):
            current_plan = WorkflowPlan.from_dict(data['current_plan'])
            
        events = [WorkflowEvent.from_dict(e) for e in data.get('events', [])]
        last_saved = Task._parse_datetime(data.get('last_saved'))
        
        return cls(
            current_plan=current_plan,
            events=events,
            version=data.get('version', '3.0.0'),
            last_saved=last_saved,
            metadata=data.get('metadata', {})
        )
        
    def get_plan_history(self) -> List[Dict[str, Any]]:
        """이벤트 로그에서 플랜 히스토리 추출"""
        plan_events = {}
        
        for event in self.events:
            if event.type in [EventType.PLAN_CREATED, EventType.PLAN_STARTED]:
                plan_events[event.plan_id] = {
                    'id': event.plan_id,
                    'name': event.details.get('name', 'Unknown'),
                    'created_at': event.timestamp,
                    'status': 'active'
                }
            elif event.type == EventType.PLAN_ARCHIVED:
                if event.plan_id in plan_events:
                    plan_events[event.plan_id]['status'] = 'archived'
                    plan_events[event.plan_id]['archived_at'] = event.timestamp
                    
        return list(plan_events.values())
