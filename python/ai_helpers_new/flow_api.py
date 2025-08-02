"""
Pythonic API for Flow system
Provides clean, intuitive interface
"""
from typing import Optional, List, Dict, Any
from .session import Session, get_current_session
from .contextual_flow_manager import ContextualFlowManager
from .domain.models import Plan, Task, TaskStatus


class FlowAPI:
    """User-friendly Pythonic API"""

    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_current_session()

    @property
    def manager(self) -> ContextualFlowManager:
        """Get flow manager from session"""
        if not self.session.flow_manager:
            raise RuntimeError("No project selected. Use session.set_project() first.")
        return self.session.flow_manager

    # Plan methods
    def create_plan(self, name: str, description: str = "") -> Plan:
        """Create a new plan

        Args:
            name: Plan name
            description: Plan description (optional)

        Returns:
            Created Plan object
        """
        plan = self.manager.create_plan(name)
        if description:
            plan.metadata['description'] = description
            self.manager.save_plan(plan)
        return plan

    def select_plan(self, plan_id: str) -> bool:
        """Select a plan

        Args:
            plan_id: Plan ID to select

        Returns:
            Success status
        """
        return self.manager.select_plan(plan_id)

    def list_plans(self) -> List[Plan]:
        """List all plans"""
        return self.manager.list_plans()

    def get_current_plan(self) -> Optional[Plan]:
        """Get currently selected plan"""
        return self.manager.get_current_plan()

    def delete_plan(self, plan_id: str) -> bool:
        """Delete a plan"""
        try:
            self.manager.delete_plan(plan_id)
            return True
        except Exception:
            return False

    # Task methods
    def add_task(self, title: str, plan_id: Optional[str] = None) -> Task:
        """Add task to current or specified plan"""
        if plan_id:
            return self.manager.add_task(plan_id, title)
        else:
            return self.manager.add_task_to_current_plan(title)

    def complete_task(self, task_id: str) -> bool:
        """Mark task as complete"""
        plan = self.get_current_plan()
        if plan and task_id in plan.tasks:
            task = plan.tasks[task_id]
            task.status = TaskStatus.DONE
            task.mark_done()
            self.manager.save_plan(plan)
            return True
        return False

    def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """Update task status"""
        plan = self.get_current_plan()
        if plan and task_id in plan.tasks:
            task = plan.tasks[task_id]
            task.status = status
            if status == TaskStatus.DONE:
                task.mark_done()
            self.manager.save_plan(plan)
            return True
        return False

    def list_tasks(self, plan_id: Optional[str] = None) -> List[Task]:
        """List tasks for current or specified plan"""
        if plan_id:
            plan = self.manager.get_plan(plan_id)
        else:
            plan = self.get_current_plan()

        if plan:
            return list(plan.tasks.values())
        return []

    # Convenience methods
    def get_status(self) -> Dict[str, Any]:
        """Get current status"""
        return {
            'project': self.session.project_context.name if self.session.project_context else None,
            'plan_count': len(self.list_plans()),
            'current_plan': self.get_current_plan(),
            'task_count': len(self.list_tasks()) if self.get_current_plan() else 0
        }

    # Fluent interface for chaining
    def with_plan(self, plan_id: str) -> 'FlowAPI':
        """Create API instance with specific plan context"""
        new_session = Session()
        new_session.project_context = self.session.project_context
        new_session.flow_manager = self.session.flow_manager
        new_api = FlowAPI(new_session)
        new_api.select_plan(plan_id)
        return new_api


def get_flow_api(session: Optional[Session] = None) -> FlowAPI:
    """Get Flow API instance"""
    return FlowAPI(session)
