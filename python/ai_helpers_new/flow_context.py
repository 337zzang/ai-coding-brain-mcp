"""
Context classes for AI Coding Brain MCP

Provides ProjectContext and FlowContext to manage project
and workflow state in a structured way.
"""

from typing import Optional, Dict, Any, Union
from pathlib import Path
from dataclasses import dataclass, field
import os
import json


@dataclass
class ProjectContext:
    """
    Represents a project's context including paths and metadata.

    This class handles all project-specific information and provides
    utilities for resolving paths within the project.
    """

    name: str
    base_path: Optional[Path] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize project context."""
        # If no base_path provided, use current directory / project name
        if self.base_path is None:
            self.base_path = Path.cwd() / self.name

        # Ensure base_path is absolute
        self.base_path = self.base_path.resolve()

        # Create project directory if it doesn't exist
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Load project metadata if exists
        self._load_metadata()

    def resolve_path(self, relative_path: Union[str, Path]) -> Path:
        """
        Resolve a relative path within the project.

        Args:
            relative_path: Path relative to project base

        Returns:
            Absolute path within the project
        """
        return (self.base_path / relative_path).resolve()

    def ensure_directory(self, relative_path: Union[str, Path]) -> Path:
        """
        Ensure a directory exists within the project.

        Args:
            relative_path: Path relative to project base

        Returns:
            Absolute path to the directory
        """
        path = self.resolve_path(relative_path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _load_metadata(self):
        """Load project metadata from .ai-brain/project.json if exists."""
        metadata_path = self.resolve_path(".ai-brain/project.json")
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            except Exception:
                # Ignore errors, use default empty metadata
                pass

    def save_metadata(self):
        """Save project metadata to .ai-brain/project.json."""
        self.ensure_directory(".ai-brain")
        metadata_path = self.resolve_path(".ai-brain/project.json")

        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)

    def get_relative_path(self, absolute_path: Union[str, Path]) -> Path:
        """
        Get a path relative to the project base.

        Args:
            absolute_path: Absolute path

        Returns:
            Path relative to project base

        Raises:
            ValueError: If path is not within the project
        """
        abs_path = Path(absolute_path).resolve()
        try:
            return abs_path.relative_to(self.base_path)
        except ValueError:
            raise ValueError(f"Path {abs_path} is not within project {self.base_path}")

    def __str__(self) -> str:
        """String representation."""
        return f"ProjectContext(name='{self.name}', path='{self.base_path}')"


@dataclass
class FlowContext:
    """
    Represents the current flow state including active plan and task.

    This class manages the workflow state and provides utilities
    for tracking progress and metadata.
    """

    current_plan_id: Optional[str] = None
    current_task_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    history: list = field(default_factory=list)

    def set_plan(self, plan_id: str, plan_data: Optional[Dict] = None):
        """
        Set the current plan.

        Args:
            plan_id: ID of the plan
            plan_data: Optional plan metadata
        """
        self.current_plan_id = plan_id
        self.current_task_id = None  # Reset task when changing plan

        # Add to history
        self.history.append({
            'type': 'plan_selected',
            'plan_id': plan_id,
            'timestamp': self._get_timestamp()
        })

        # Update metadata
        if plan_data:
            self.metadata[f'plan_{plan_id}'] = plan_data

    def set_task(self, task_id: str, task_data: Optional[Dict] = None):
        """
        Set the current task.

        Args:
            task_id: ID of the task
            task_data: Optional task metadata
        """
        if not self.current_plan_id:
            raise ValueError("Cannot set task without active plan")

        self.current_task_id = task_id

        # Add to history
        self.history.append({
            'type': 'task_selected',
            'task_id': task_id,
            'plan_id': self.current_plan_id,
            'timestamp': self._get_timestamp()
        })

        # Update metadata
        if task_data:
            self.metadata[f'task_{task_id}'] = task_data

    def clear_task(self):
        """Clear the current task."""
        self.current_task_id = None

    def clear_plan(self):
        """Clear the current plan and task."""
        self.current_plan_id = None
        self.current_task_id = None

    def get_state(self) -> Dict[str, Any]:
        """
        Get the current flow state.

        Returns:
            Dictionary containing current state
        """
        return {
            'current_plan_id': self.current_plan_id,
            'current_task_id': self.current_task_id,
            'metadata': self.metadata,
            'history_length': len(self.history)
        }

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()

    def __str__(self) -> str:
        """String representation."""
        plan = self.current_plan_id or 'None'
        task = self.current_task_id or 'None'
        return f"FlowContext(plan={plan}, task={task})"
