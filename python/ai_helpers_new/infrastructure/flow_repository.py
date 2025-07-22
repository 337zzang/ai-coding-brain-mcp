"""
Flow Repository implementation with ProjectContext support
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from ..domain.models import Flow
from .project_context import ProjectContext


class FlowRepository:
    """Base repository interface for Flow storage"""

    def get(self, flow_id: str) -> Optional[Flow]:
        """Get a single Flow by ID"""
        flows = self.load_all()
        return flows.get(flow_id)

    def load_all(self) -> Dict[str, Flow]:
        """Load all Flows"""
        raise NotImplementedError

    def save(self, flow: Flow) -> None:
        """Save a single Flow"""
        raise NotImplementedError

    def save_all(self, flows: Dict[str, Flow]) -> None:
        """Save all Flows"""
        raise NotImplementedError

    def delete(self, flow_id: str) -> bool:
        """Delete a Flow by ID"""
        flows = self.load_all()
        if flow_id in flows:
            del flows[flow_id]
            self.save_all(flows)
            return True
        return False


class JsonFlowRepository(FlowRepository):
    """JSON file-based Flow repository with ProjectContext support"""

    def __init__(self, context: Optional[ProjectContext] = None, storage_path: Optional[str] = None):
        """Initialize repository with ProjectContext or legacy path

        Args:
            context: ProjectContext for dynamic path management (preferred)
            storage_path: Legacy storage path (deprecated)
        """
        if context is not None:
            # Type safety check
            if not isinstance(context, ProjectContext):
                raise TypeError(
                    f"context must be ProjectContext instance, "
                    f"got {type(context).__name__}. "
                    f"Did you mean to use storage_path parameter?"
                )
            self._context = context
        elif storage_path is not None:
            # Type safety check for storage_path
            if not isinstance(storage_path, str):
                raise TypeError(
                    f"storage_path must be string, got {type(storage_path).__name__}"
                )
            # Legacy mode - create context from path
            import warnings
            warnings.warn(
                "Using storage_path is deprecated. Use ProjectContext instead.",
                DeprecationWarning,
                stacklevel=2
            )
            self._context = self._create_context_from_path(storage_path)
        else:
            # Default to current directory
            self._context = ProjectContext(Path.cwd())

        self._ensure_file()
        self._cache: Optional[Dict[str, Flow]] = None

    @classmethod
    def from_path(cls, storage_path: Optional[str] = None) -> 'JsonFlowRepository':
        """Create repository from storage path (legacy compatibility)

        Args:
            storage_path: Path to flows.json file

        Returns:
            JsonFlowRepository instance
        """
        if storage_path:
            context = cls._create_context_from_path(storage_path)
        else:
            context = ProjectContext(Path.cwd())

        return cls(context=context)

    @staticmethod
    def _create_context_from_path(storage_path: str) -> ProjectContext:
        """Create ProjectContext from storage path

        Args:
            storage_path: Path to flows.json

        Returns:
            ProjectContext for the project
        """
        path = Path(storage_path)

        # Try to infer project root from path
        if path.name == "flows.json" and path.parent.name == ".ai-brain":
            # Standard structure: project/.ai-brain/flows.json
            project_root = path.parent.parent
        elif path.parent.exists() and path.parent.is_dir():
            # Use parent directory as project root
            project_root = path.parent
        else:
            # Fall back to current directory
            project_root = Path.cwd()

        return ProjectContext(project_root)

    @property
    def storage_path(self) -> Path:
        """Get current storage path dynamically from context"""
        return self._context.flow_file

    @property
    def context(self) -> ProjectContext:
        """Get current project context"""
        return self._context

    def set_context(self, context: ProjectContext):
        """Change project context

        Args:
            context: New project context
        """
        self._context = context
        self._cache = None  # Invalidate cache
        self._ensure_file()

    def _ensure_file(self):
        """Ensure flows.json file exists"""
        if not self.storage_path.exists():
            self._write_data({})

    def load_all(self) -> Dict[str, Flow]:
        """Load all Flows with caching"""
        if self._cache is None:
            self._cache = self._load_from_disk()
        return self._cache.copy()

    def _load_from_disk(self) -> Dict[str, Flow]:
        """Load Flows from disk"""
        try:
            data = self._read_data()
            flows = {}

            for flow_id, flow_data in data.items():
                if isinstance(flow_data, dict):
                    try:
                        flows[flow_id] = Flow.from_dict(flow_data)
                    except Exception as e:
                        print(f"Warning: Failed to load flow {flow_id}: {e}")
                        continue

            return flows

        except Exception as e:
            print(f"Error loading flows: {e}")
            return {}

    def save(self, flow: Flow) -> None:
        """Save a single Flow"""
        flows = self.load_all()
        flows[flow.id] = flow
        self.save_all(flows)

    def save_all(self, flows: Dict[str, Flow]) -> None:
        """Save all Flows with automatic backup"""
        # Create backup before saving
        self._create_backup()

        # Convert to dict format
        data = {}
        for flow_id, flow in flows.items():
            if isinstance(flow, Flow):
                data[flow_id] = flow.to_dict()
            else:
                # Legacy compatibility
                data[flow_id] = flow

        # Write data
        self._write_data(data)

        # Update cache
        self._cache = flows.copy()

    def delete(self, flow_id: str) -> bool:
        """Delete a Flow"""
        flows = self.load_all()
        if flow_id in flows:
            del flows[flow_id]
            self.save_all(flows)
            return True
        return False

    def _create_backup(self):
        """Create automatic backup of flows.json"""
        if self.storage_path.exists():
            backup_dir = self._context.ai_brain_dir / "backups"
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"flows_backup_{timestamp}.json"

            # Clean old backups (keep last 10)
            self._cleanup_old_backups(backup_dir, max_backups=10)

            # Copy current file to backup
            shutil.copy2(self.storage_path, backup_path)

    def _cleanup_old_backups(self, backup_dir: Path, max_backups: int):
        """Remove old backup files"""
        backups = sorted(backup_dir.glob("flows_backup_*.json"))
        if len(backups) > max_backups:
            for backup in backups[:-max_backups]:
                backup.unlink()

    def _read_data(self) -> dict:
        """Read JSON data from file"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in {self.storage_path}, returning empty dict")
            return {}
        except Exception as e:
            print(f"Error reading {self.storage_path}: {e}")
            return {}

    def _write_data(self, data: dict):
        """Write JSON data to file (atomic write)"""
        # Write to temporary file first
        temp_path = self.storage_path.with_suffix('.tmp')

        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Atomic replace
            temp_path.replace(self.storage_path)

        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise

    def get_project_info(self) -> dict:
        """Get current project information"""
        return {
            'project': str(self._context.root),
            'storage_path': str(self.storage_path),
            'flows_count': len(self.load_all()),
            'file_size': self.storage_path.stat().st_size if self.storage_path.exists() else 0,
            'has_cache': self._cache is not None
        }

    def clear_cache(self):
        """Clear the internal cache"""
        self._cache = None

    def sync(self):
        """Force reload from disk"""
        self.clear_cache()
        self._cache = self._load_from_disk()


class InMemoryFlowRepository(FlowRepository):
    """In-memory Flow repository for testing"""

    def __init__(self):
        self._flows: Dict[str, Flow] = {}

    def load_all(self) -> Dict[str, Flow]:
        return self._flows.copy()

    def save(self, flow: Flow) -> None:
        self._flows[flow.id] = flow

    def save_all(self, flows: Dict[str, Flow]) -> None:
        self._flows = flows.copy()

    def delete(self, flow_id: str) -> bool:
        if flow_id in self._flows:
            del self._flows[flow_id]
            return True
        return False
