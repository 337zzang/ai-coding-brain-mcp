"""
Manager Adapter for backward compatibility

Provides a compatibility layer between the old UltraSimpleFlowManager
interface and the new ContextualFlowManager.
"""

from typing import Optional, List, Dict, Any
from pathlib import Path

from .contextual_flow_manager import ContextualFlowManager


class ManagerAdapter:
    """
    Adapter that makes ContextualFlowManager compatible with 
    UltraSimpleFlowManager interface.

    This allows existing code to continue working while we migrate
    to the new session-based architecture.
    """

    def __init__(self, contextual_manager: ContextualFlowManager):
        """Initialize adapter with a contextual manager."""
        self.manager = contextual_manager
        self.project_path = str(self.manager.project_context.base_path)
        self.project_name = self.manager.project_context.name

    # ========== Plan-related methods ==========

    def create_plan(self, name: str, description: str = "") -> 'PlanAdapter':
        """Create a plan and return a plan adapter."""
        plan_data = self.manager.create_plan(name, description)
        return PlanAdapter(plan_data)

    def list_plans(self) -> List['PlanAdapter']:
        """List all plans as plan adapters."""
        plans_data = self.manager.list_plans()
        return [PlanAdapter(p) for p in plans_data]

    def get_plan(self, plan_id: str) -> Optional['PlanAdapter']:
        """Get a plan by ID as a plan adapter."""
        plan_data = self.manager.get_plan(plan_id)
        if plan_data:
            return PlanAdapter(plan_data)
        return None

    def delete_plan(self, plan_id: str) -> bool:
        """Delete a plan."""
        # Implement deletion logic
        plan_path = Path(self.project_path) / '.ai-brain' / 'flow' / 'plans' / plan_id
        if plan_path.exists():
            import shutil
            shutil.rmtree(plan_path)

            # Clear from context if selected
            if self.manager.flow_context.current_plan_id == plan_id:
                self.manager.flow_context.clear_plan()
                self.manager._save_flow_state()

            return True
        return False

    # ========== Task-related methods ==========

    def add_task_to_plan(self, plan_id: str, title: str, description: str = "") -> Optional['TaskAdapter']:
        """Add a task to a specific plan."""
        # Temporarily select the plan
        current_plan = self.manager.flow_context.current_plan_id
        self.manager.select_plan(plan_id)

        # Add task
        task_data = self.manager.add_task(title, description)

        # Restore previous plan
        if current_plan and current_plan != plan_id:
            self.manager.select_plan(current_plan)

        if task_data:
            return TaskAdapter(task_data)
        return None

    def update_task_status(self, plan_id: str, task_id: str, status: str) -> bool:
        """Update task status."""
        # Temporarily select the plan
        current_plan = self.manager.flow_context.current_plan_id
        self.manager.select_plan(plan_id)

        # Update status
        success = self.manager.update_task_status(task_id, status)

        # Restore previous plan
        if current_plan and current_plan != plan_id:
            self.manager.select_plan(current_plan)

        return success

    # ========== Additional compatibility methods ==========

    def create_task(self, task_title: str, task_description: str = "") -> Optional['TaskAdapter']:
        """Create a task in the current plan (for compatibility)."""
        task_data = self.manager.add_task(task_title, task_description)
        if task_data:
            return TaskAdapter(task_data)
        return None

    def delete_task(self, plan_id: str, task_id: str) -> bool:
        """Delete a task (for compatibility)."""
        # Implementation depends on requirements
        return False

    def get_task(self, plan_id: str, task_id: str) -> Optional['TaskAdapter']:
        """Get a task by ID (for compatibility)."""
        plan_data = self.manager.get_plan(plan_id)
        if plan_data:
            task_data = plan_data.get('tasks', {}).get(task_id)
            if task_data:
                return TaskAdapter(task_data)
        return None



class PlanAdapter:
    """Adapter to make plan dict look like the old Plan class."""

    def __init__(self, plan_data: Dict[str, Any]):
        self.id = plan_data['id']
        self.name = plan_data['name']
        self.description = plan_data.get('description', '')
        self.status = plan_data.get('status', 'active')
        self.created_at = plan_data.get('created_at', '')
        self.updated_at = plan_data.get('updated_at', '')
        self.tasks = {
            task_id: TaskAdapter(task_data)
            for task_id, task_data in plan_data.get('tasks', {}).items()
        }
        self._data = plan_data

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self._data


class TaskAdapter:
    """Adapter to make task dict look like the old Task class."""

    def __init__(self, task_data: Dict[str, Any]):
        self.id = task_data['id']
        self.title = task_data['title']
        self.description = task_data.get('description', '')
        self.status = task_data.get('status', 'todo')
        self.created_at = task_data.get('created_at', '')
        self.updated_at = task_data.get('updated_at', '')
        self._data = task_data

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self._data
