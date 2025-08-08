"""
Project context management for ai_helpers_new
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any

class ProjectContext:
    """Simple project context holder"""
    def __init__(self, name: str = "default", path: Optional[Path] = None):
        self.name = name
        self.path = path or Path.cwd()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": str(self.path)
        }

# Global project context
_project_context: Optional[ProjectContext] = None

def get_project_context() -> Optional[ProjectContext]:
    """Get the current project context"""
    global _project_context
    if _project_context is None:
        # Create default context
        _project_context = ProjectContext(
            name=Path.cwd().name,
            path=Path.cwd()
        )
    return _project_context

def resolve_project_path(relative_path: str = "") -> Path:
    """Resolve a path relative to the project root"""
    context = get_project_context()
    if context:
        return context.path / relative_path
    return Path.cwd() / relative_path

def set_project_context(name: str, path: Optional[str] = None) -> ProjectContext:
    """Set the project context"""
    global _project_context
    project_path = Path(path) if path else Path.cwd()
    _project_context = ProjectContext(name, project_path)
    return _project_context
