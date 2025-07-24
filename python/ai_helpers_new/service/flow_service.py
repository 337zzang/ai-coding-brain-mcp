"""
Flow Service with ProjectContext support
"""

from typing import Dict, List, Optional
from datetime import datetime
import uuid
import os
from pathlib import Path

from ..domain.models import Flow, Plan, Task
from ..infrastructure.flow_repository import FlowRepository
from ..infrastructure.project_context import ProjectContext


class FlowService:
    """Flow management service with project-level isolation"""

    def __init__(self, repository: FlowRepository, context: Optional[ProjectContext] = None):
        """Initialize FlowService

        Args:
            repository: Flow repository instance
            context: ProjectContext for project-specific settings (optional)
        """
        self.repository = repository

        # Use context from repository if not provided
        if context is None and hasattr(repository, 'context'):
            self._context = repository.context
        elif context is not None:
            self._context = context
        else:
            # Fallback to current directory
            self._context = ProjectContext(Path.cwd())

        self._flows: Dict[str, Flow] = {}
        self._current_flow_id: Optional[str] = None
        self._sync_with_repository()
        self._load_current_flow()
        self._migrate_global_current_flow()

    @property
    def context(self) -> ProjectContext:
        """Get current project context"""
        return self._context

    @property
    def current_flow_file(self) -> Path:
        """Get project-specific current flow file path"""
        return self._context.current_flow_file

    def set_context(self, context: ProjectContext):
        """Change project context

        Args:
            context: New project context
        """
        self._context = context
        self._current_flow_id = None
        self._sync_with_repository()
        self._load_current_flow()

    def _sync_with_repository(self):
        """Synchronize with repository"""
        self._flows = self.repository.load_all()

    def _load_current_flow(self):
        """Load current flow from project-specific file"""
        if self.current_flow_file.exists():
            try:
                flow_id = self.current_flow_file.read_text().strip()
                if flow_id in self._flows:
                    self._current_flow_id = flow_id
                else:
                    # Invalid flow ID, remove file
                    self.current_flow_file.unlink()
                    self._current_flow_id = None
            except Exception as e:
                print(f"Error loading current flow: {e}")
                self._current_flow_id = None

    def _save_current_flow(self):
        """Save current flow ID to project-specific file"""
        if self._current_flow_id:
            try:
                self.current_flow_file.write_text(self._current_flow_id)
            except Exception as e:
                print(f"Error saving current flow: {e}")
        elif self.current_flow_file.exists():
            try:
                self.current_flow_file.unlink()
            except Exception as e:
                print(f"Error removing current flow file: {e}")

    def _migrate_global_current_flow(self):
        """Migrate from global current_flow.txt if exists (one-time migration)"""
        # Check for legacy global file
        global_file = Path.home() / ".ai-flow" / "current_flow.txt"

        if global_file.exists() and not self.current_flow_file.exists():
            try:
                # Read global current flow
                flow_id = global_file.read_text().strip()

                # If this flow exists in current project, migrate it
                if flow_id in self._flows:
                    self._current_flow_id = flow_id
                    self._save_current_flow()
                    print(f"Migrated current flow from global file: {flow_id}")

                    # Optional: Remove global file after successful migration
                    # global_file.unlink()

            except Exception as e:
                print(f"Failed to migrate global current flow: {e}")

    def create_flow(self, name: str) -> Flow:
        """Create a new Flow"""
        flow_id = f"flow_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

        flow = Flow(
            id=flow_id,
            name=name,
            plans={},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={}
        )

        self._flows[flow.id] = flow
        self.repository.save(flow)

        # Set as current if it's the first flow
        if len(self._flows) == 1:
            self.set_current_flow(flow.id)

        return flow

    def get_flow(self, flow_id: str) -> Optional[Flow]:
        """Get a Flow by ID"""
        return self._flows.get(flow_id)

    def list_flows(self) -> List[Flow]:
        """List all Flows"""
        return list(self._flows.values())

    def update_flow(self, flow: Flow) -> bool:
        """Update a Flow"""
        if flow.id in self._flows:
            flow.updated_at = datetime.now()
            self._flows[flow.id] = flow
            self.repository.save(flow)
            return True
        return False

    def delete_flow(self, flow_id: str) -> bool:
        """Delete a Flow"""
        if flow_id in self._flows:
            # Clear current flow if it's being deleted
            if self._current_flow_id == flow_id:
                self._current_flow_id = None
                self._save_current_flow()

            del self._flows[flow_id]
            self.repository.delete(flow_id)
            return True
        return False

    def get_current_flow(self) -> Optional[Flow]:
        """Get the current Flow"""
        if self._current_flow_id:
            return self._flows.get(self._current_flow_id)
        return None

    def set_current_flow(self, flow_id: str) -> bool:
        """Set the current Flow"""
        if flow_id in self._flows:
            self._current_flow_id = flow_id
            self._save_current_flow()
            return True
        return False

    def sync(self):
        """Force synchronization with repository"""
        self._sync_with_repository()
        self._load_current_flow()

    def get_project_info(self) -> dict:
        """Get project-specific service information"""
        return {
            'project': str(self._context.root),
            'flows_count': len(self._flows),
            'current_flow': self._current_flow_id,
            'current_flow_name': self.get_current_flow().name if self.get_current_flow() else None,
            'current_flow_file': str(self.current_flow_file),
            'has_legacy_global': (Path.home() / ".ai-flow" / "current_flow.txt").exists()
        }

    def clear_current_flow(self):
        """Clear the current flow selection"""
        self._current_flow_id = None
        self._save_current_flow()
