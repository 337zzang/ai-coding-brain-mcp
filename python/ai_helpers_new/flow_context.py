"""
Context classes for AI Coding Brain MCP

Provides ProjectContext and FlowContext to manage project
and workflow state in a structured way.
"""
from typing import Optional, Dict, Any, Union, List
from pathlib import Path
from dataclasses import dataclass, field
import os
import json
import platform


def find_project_path(project_name: str) -> Optional[Path]:
    """
    Find project path by searching common locations.

    Args:
        project_name: Name of the project to find

    Returns:
        Path to project or None if not found
    """
    base_paths = []

    # Check environment variable
    if os.environ.get('PROJECT_BASE_PATH'):
        base_paths.append(Path(os.environ['PROJECT_BASE_PATH']))

    # Platform-specific default paths
    home = Path.home()
    system = platform.system()

    if system == 'Windows':
        base_paths.extend([
            home / "Desktop",
            home / "바탕화면",  # Korean Windows
            home / "Documents",
            home / "문서"        # Korean Windows
        ])
    elif system == 'Darwin':  # macOS
        base_paths.extend([
            home / "Desktop",
            home / "Documents",
            home / "Developer"
        ])
    else:  # Linux and others
        base_paths.extend([
            home / "Desktop",
            home / "Documents",
            home / "projects",
            home
        ])

    # Search for project
    for base_path in base_paths:
        if base_path.exists():
            candidate = base_path / project_name
            if candidate.exists() and candidate.is_dir():
                return candidate

    return None


@dataclass
class ProjectContext:
    """
    Enhanced project context that handles all path resolution.

    This class replaces the need for os.chdir by maintaining
    project paths and resolving all paths relative to the project.
    """

    name: str
    base_path: Optional[Path] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    _original_cwd: Optional[Path] = field(default=None, init=False)

    def __post_init__(self):
        """Initialize project context."""
        # Save original working directory
        self._original_cwd = Path.cwd()

        # If no base_path provided, search for project
        if self.base_path is None:
            found_path = find_project_path(self.name)
            if found_path:
                self.base_path = found_path
            else:
                # Create in current directory as fallback
                self.base_path = self._original_cwd / self.name

        # Ensure base_path is absolute
        self.base_path = self.base_path.resolve()

        # Create project directory if it doesn't exist
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Load project metadata if exists
        self._load_metadata()

        # Update project info
        self.metadata['name'] = self.name
        self.metadata['path'] = str(self.base_path)
        self.metadata['type'] = self._detect_project_type()

    def resolve_path(self, relative_path: Union[str, Path]) -> Path:
        """
        Resolve a relative path within the project.

        Args:
            relative_path: Path relative to project base

        Returns:
            Absolute path within the project
        """
        # Handle absolute paths
        path = Path(relative_path)
        if path.is_absolute():
            return path

        # Resolve relative to project base
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

    def _detect_project_type(self) -> str:
        """Detect the type of project."""
        # Check for common project files
        if (self.base_path / "package.json").exists():
            return "node"
        elif (self.base_path / "requirements.txt").exists():
            return "python"
        elif (self.base_path / "Cargo.toml").exists():
            return "rust"
        elif (self.base_path / "go.mod").exists():
            return "go"
        elif (self.base_path / ".git").exists():
            return "git"
        else:
            return "generic"

    def _load_metadata(self):
        """Load project metadata from .ai-brain/project.json if exists."""
        metadata_path = self.resolve_path(".ai-brain/project.json")
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    saved_metadata = json.load(f)
                    self.metadata.update(saved_metadata)
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

    def list_files(self, pattern: str = "*", recursive: bool = True) -> List[Path]:
        """
        List files in the project matching a pattern.

        Args:
            pattern: Glob pattern for files
            recursive: Whether to search recursively

        Returns:
            List of file paths relative to project base
        """
        if recursive:
            files = self.base_path.rglob(pattern)
        else:
            files = self.base_path.glob(pattern)

        return [self.get_relative_path(f) for f in files if f.is_file()]

    def read_file(self, relative_path: Union[str, Path], 
                  encoding: str = 'utf-8') -> Optional[str]:
        """
        Read a file from the project.

        Args:
            relative_path: Path relative to project base
            encoding: File encoding

        Returns:
            File contents or None if error
        """
        try:
            file_path = self.resolve_path(relative_path)
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except Exception:
            return None

    def write_file(self, relative_path: Union[str, Path], 
                   content: str, encoding: str = 'utf-8') -> bool:
        """
        Write a file to the project.

        Args:
            relative_path: Path relative to project base
            content: File content
            encoding: File encoding

        Returns:
            True if successful
        """
        try:
            file_path = self.resolve_path(relative_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            return True
        except Exception:
            return False

    def get_project_info(self) -> Dict[str, Any]:
        """
        Get comprehensive project information.

        Returns:
            Dictionary with project details
        """
        return {
            'name': self.name,
            'path': str(self.base_path),
            'type': self.metadata.get('type', 'generic'),
            'exists': self.base_path.exists(),
            'is_git': (self.base_path / '.git').exists(),
            'has_flow': (self.base_path / '.ai-brain' / 'flow').exists(),
            'metadata': self.metadata
        }

    def __str__(self) -> str:
        """String representation."""
        return f"ProjectContext(name='{self.name}', path='{self.base_path}')"

    def __repr__(self) -> str:
        """Detailed representation."""
        return (f"ProjectContext(name='{self.name}', "
                f"base_path=Path('{self.base_path}'), "
                f"type='{self.metadata.get('type', 'generic')}')")


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
