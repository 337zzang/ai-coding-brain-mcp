"""
Flow and Project contexts for state management
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
import uuid
import os


@dataclass
class FlowContext:
    """Encapsulates flow work context"""
    context_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    current_plan_id: Optional[str] = None
    current_task_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def select_plan(self, plan_id: str) -> None:
        """Select a plan (encapsulate state change)"""
        self.current_plan_id = plan_id
        self.metadata['plan_selected_at'] = datetime.now()

    def select_task(self, task_id: str) -> None:
        """Select a task"""
        self.current_task_id = task_id
        self.metadata['task_selected_at'] = datetime.now()

    def clear(self) -> None:
        """Clear context"""
        self.current_plan_id = None
        self.current_task_id = None
        self.metadata.clear()


@dataclass
class ProjectContext:
    """Project work context"""
    name: str
    base_path: Optional[Path] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.base_path is None:
            # Try to find project automatically
            self.base_path = self._find_project_path(self.name)
        else:
            self.base_path = Path(self.base_path)

    def _find_project_path(self, project_name: str) -> Path:
        """Find project path using search strategy"""
        # Import here to avoid circular dependency
        from .project import _get_project_search_paths

        search_paths = _get_project_search_paths()

        for base_path in search_paths:
            candidate = base_path / project_name
            if candidate.exists() and candidate.is_dir():
                return candidate

        raise FileNotFoundError(f"Project not found: {project_name}")

    def resolve_path(self, relative_path: str) -> Path:
        """Resolve relative path against project base"""
        return self.base_path / relative_path

    def exists(self) -> bool:
        """Check if project exists"""
        return self.base_path.exists() if self.base_path else False

    @property
    def flow_path(self) -> Path:
        """Get flow data path for this project"""
        return self.resolve_path(".ai-brain/flow")
