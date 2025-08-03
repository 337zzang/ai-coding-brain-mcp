"""
Pythonic Flow API for AI Coding Brain MCP

Provides a clean, object-oriented interface to the flow system
as an alternative to the command-based interface.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime

from .session import Session, get_current_session
from .contextual_flow_manager import ContextualFlowManager
from .flow_context import FlowContext


class FlowAPI:
    """
    Pythonic API for flow management.

    This class provides methods that correspond to the flow commands
    but in a more Pythonic, object-oriented style.

    Example usage:
        api = get_flow_api()
        plan = api.create_plan("My Project")
        task = api.add_task("Implement feature")
        api.update_task_status(task['id'], 'in_progress')
    """

    def __init__(self, manager: Optional[ContextualFlowManager] = None, 
                 session: Optional[Session] = None):
        """
        Initialize the Flow API.

        Args:
            manager: Optional flow manager (will be created from session if not provided)
            session: Optional session (uses current session if not provided)
        """
        self.session = session or get_current_session()

        if manager:
            self.manager = manager
        else:
            if not self.session.is_initialized:
                raise ValueError("Session not initialized. Call session.set_project() first.")
            self.manager = self.session.flow_manager

    @property
    def context(self) -> FlowContext:
        """Get the current flow context."""
        return self.manager.get_context()

    # ========== Plan Management ==========

    def create_plan(self, name: str, description: str = "") -> Dict[str, Any]:
        """
        Create a new plan.

        Args:
            name: Plan name
            description: Optional description

        Returns:
            Created plan data

        Example:
            plan = api.create_plan("Backend Development", "API implementation")
        """
        return self.manager.create_plan(name, description)

    def list_plans(self) -> List[Dict[str, Any]]:
        """
        List all plans.

        Returns:
            List of plan dictionaries

        Example:
            plans = api.list_plans()
            for plan in plans:
                print(f"{plan['id']}: {plan['name']}")
        """
        return self.manager.list_plans()

    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific plan by ID.

        Args:
            plan_id: Plan ID

        Returns:
            Plan data or None if not found
        """
        return self.manager.get_plan(plan_id)

    def select_plan(self, plan_id: str) -> bool:
        """
        Select a plan as current.

        Args:
            plan_id: Plan ID to select

        Returns:
            True if successful

        Example:
            if api.select_plan("plan_20240101_project"):
                print("Plan selected")
        """
        return self.manager.select_plan(plan_id)

    def delete_plan(self, plan_id: str) -> bool:
        """
        Delete a plan.

        Args:
            plan_id: Plan ID to delete

        Returns:
            True if successful
        """
        # For now, delegate to the manager
        # In future, implement proper deletion
        plan_path = self.manager.flow_path / 'plans' / plan_id
        if plan_path.exists():
            import shutil
            shutil.rmtree(plan_path)

            # Clear from context if it was selected
            if self.context.current_plan_id == plan_id:
                self.context.clear_plan()
                self.manager._save_flow_state()

            return True
        return False

    def get_current_plan(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently selected plan.

        Returns:
            Current plan data or None
        """
        return self.manager.get_current_plan()

    # ========== Task Management ==========

    def add_task(self, title: str, description: str = "") -> Optional[Dict[str, Any]]:
        """
        Add a task to the current plan.

        Args:
            title: Task title
            description: Optional description

        Returns:
            Created task data or None if no plan selected

        Example:
            task = api.add_task("Write tests", "Unit tests for auth module")
        """
        return self.manager.add_task(title, description)

    def list_tasks(self) -> List[Dict[str, Any]]:
        """
        List all tasks in the current plan.

        Returns:
            List of task dictionaries
        """
        plan = self.get_current_plan()
        if not plan:
            return []

        return list(plan.get('tasks', {}).values())

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task data or None if not found
        """
        plan = self.get_current_plan()
        if not plan:
            return None

        return plan.get('tasks', {}).get(task_id)

    def update_task_status(self, task_id: str, status: str) -> bool:
        """
        Update task status.

        Args:
            task_id: Task ID
            status: New status ('todo', 'in_progress', 'done')

        Returns:
            True if successful

        Example:
            api.update_task_status("task_001", "in_progress")
        """
        return self.manager.update_task_status(task_id, status)

    def start_task(self, task_id: str) -> bool:
        """
        Start working on a task (sets status to in_progress).

        Args:
            task_id: Task ID

        Returns:
            True if successful
        """
        return self.update_task_status(task_id, 'in_progress')

    def complete_task(self, task_id: str) -> bool:
        """
        Mark a task as done.

        Args:
            task_id: Task ID

        Returns:
            True if successful
        """
        return self.update_task_status(task_id, 'done')

    def get_current_task(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently selected task.

        Returns:
            Current task data or None
        """
        return self.manager.get_current_task()

    # ========== Status and Info ==========

    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status information.

        Returns:
            Status dictionary containing:
            - project_name: Current project name
            - plan_count: Total number of plans
            - current_plan: Current plan info
            - task_summary: Task statistics

        Example:
            status = api.get_status()
            print(f"Project: {status['project_name']}")
            print(f"Plans: {status['plan_count']}")
        """
        plans = self.list_plans()
        current_plan = self.get_current_plan()

        status = {
            'project_name': self.session.get_project_name(),
            'project_path': str(self.session.get_project_path()),
            'plan_count': len(plans),
            'current_plan': None,
            'task_summary': {
                'total': 0,
                'todo': 0,
                'in_progress': 0,
                'done': 0
            }
        }

        if current_plan:
            tasks = current_plan.get('tasks', {})
            todo_count = sum(1 for t in tasks.values() if t['status'] == 'todo')
            in_progress = sum(1 for t in tasks.values() if t['status'] == 'in_progress')
            done_count = sum(1 for t in tasks.values() if t['status'] == 'done')

            status['current_plan'] = {
                'id': current_plan['id'],
                'name': current_plan['name'],
                'task_count': len(tasks)
            }
            status['task_summary'] = {
                'total': len(tasks),
                'todo': todo_count,
                'in_progress': in_progress,
                'done': done_count
            }

        return status

    def get_recent_plans(self, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Get the most recent plans.

        Args:
            limit: Maximum number of plans to return

        Returns:
            List of recent plans
        """
        plans = self.list_plans()
        return plans[:limit]  # Already sorted by creation date

    # ========== Utility Methods ==========

    def switch_project(self, project_name: str, project_path: Optional[str] = None) -> bool:
        """
        Switch to a different project.

        Args:
            project_name: Project name
            project_path: Optional project path

        Returns:
            True if successful
        """
        try:
            self.session.set_project(project_name, project_path)
            self.manager = self.session.flow_manager
            return True
        except Exception:
            return False

    def clear_current_task(self):
        """Clear the current task selection."""
        self.context.clear_task()
        self.manager._save_flow_state()

    def clear_current_plan(self):
        """Clear the current plan selection."""
        self.context.clear_plan()
        self.manager._save_flow_state()



    def create_task(self, plan_id: str, title: str) -> Dict[str, Any]:
        """새 Task 생성

        Args:
            plan_id: Plan ID
            title: Task 제목

        Returns:
            생성된 Task 정보
        """
        task = self.manager.create_task(plan_id, title)
        if task:
            return self._task_to_dict(task)
        return {"error": f"Failed to create task in plan '{plan_id}'"}

    def delete_task(self, plan_id: str, task_id: str) -> Dict[str, Any]:
        """Task 삭제

        Args:
            plan_id: Plan ID
            task_id: Task ID

        Returns:
            삭제 결과
        """
        # Manager에 delete_task가 없으면 tasks에서 직접 제거
        plan = self.manager.get_plan(plan_id)
        if plan and hasattr(plan, 'tasks') and task_id in plan.tasks:
            del plan.tasks[task_id]
            return {"ok": True, "message": "Task deleted"}
        return {"ok": False, "error": "Task not found"}

def get_flow_api(session: Optional[Session] = None) -> FlowAPI:
    """
    Get a FlowAPI instance.

    Args:
        session: Optional session (uses current session if not provided)

    Returns:
        FlowAPI instance

    Example:
        # Using current session
        api = get_flow_api()

        # Using specific session (for testing)
        test_session = Session()
        test_session.set_project("test")
        api = get_flow_api(test_session)
    """
    return FlowAPI(session=session)
