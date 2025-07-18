"""
워크플로우 시스템 v2.0 데이터 스키마
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class TaskStatus(Enum):
    TODO = "todo"
    DOING = "doing"
    DONE = "done"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

class ArtifactType(Enum):
    FILE = "file"
    COMMIT = "commit"
    URL = "url"
    DOCUMENT = "document"
    CODE = "code"

@dataclass
class Artifact:
    """작업 산출물"""
    type: ArtifactType
    path: Optional[str] = None
    content: Optional[str] = None
    commit_hash: Optional[str] = None
    commit_message: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class Task:
    """확장된 Task 모델"""
    id: int
    name: str
    status: TaskStatus = TaskStatus.TODO
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_minutes: Optional[int] = None
    summary: Optional[str] = None
    artifacts: List[Artifact] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    dependencies: List[int] = field(default_factory=list)
    assignee: Optional[str] = None
    priority: int = 3  # 1-5, 1이 가장 높음

    def to_dict(self) -> Dict[str, Any]:
        """JSON 직렬화를 위한 딕셔너리 변환"""
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_minutes": self.duration_minutes,
            "summary": self.summary,
            "artifacts": [
                {
                    "type": a.type.value,
                    "path": a.path,
                    "content": a.content,
                    "commit_hash": a.commit_hash,
                    "commit_message": a.commit_message,
                    "url": a.url,
                    "description": a.description,
                    "created_at": a.created_at
                } for a in self.artifacts
            ],
            "tags": self.tags,
            "dependencies": self.dependencies,
            "assignee": self.assignee,
            "priority": self.priority
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """딕셔너리에서 Task 객체 생성"""
        artifacts = []
        for a in data.get("artifacts", []):
            artifacts.append(Artifact(
                type=ArtifactType(a["type"]),
                path=a.get("path"),
                content=a.get("content"),
                commit_hash=a.get("commit_hash"),
                commit_message=a.get("commit_message"),
                url=a.get("url"),
                description=a.get("description"),
                created_at=a.get("created_at", datetime.now().isoformat())
            ))

        return cls(
            id=data["id"],
            name=data["name"],
            status=TaskStatus(data.get("status", "todo")),
            created_at=data.get("created_at", datetime.now().isoformat()),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            duration_minutes=data.get("duration_minutes"),
            summary=data.get("summary"),
            artifacts=artifacts,
            tags=data.get("tags", []),
            dependencies=data.get("dependencies", []),
            assignee=data.get("assignee"),
            priority=data.get("priority", 3)
        )

@dataclass
class WorkflowEvent:
    """통합 이벤트 모델"""
    id: str
    type: str  # task_created, task_started, task_completed, etc.
    timestamp: str
    task_id: Optional[int] = None
    user: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "timestamp": self.timestamp,
            "task_id": self.task_id,
            "user": self.user,
            "data": self.data,
            "before_state": self.before_state,
            "after_state": self.after_state
        }

@dataclass
class WorkflowV2:
    """워크플로우 v2.0 메인 모델"""
    version: str = "2.0"
    project: str = ""
    status: str = "active"  # active, paused, completed, archived
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    focus_task_id: Optional[int] = None
    tasks: List[Task] = field(default_factory=list)
    events: List[WorkflowEvent] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "project": self.project,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "focus_task_id": self.focus_task_id,
            "tasks": [t.to_dict() for t in self.tasks],
            "events": [e.to_dict() for e in self.events],
            "metadata": self.metadata
        }
