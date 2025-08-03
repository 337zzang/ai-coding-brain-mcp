"""
Contextual Flow Manager for AI Coding Brain MCP

A new flow manager that works with Session and Context objects
to provide better state management and isolation.
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
import json
import os
import uuid

from .flow_context import ProjectContext, FlowContext


class ContextualFlowManager:
    """
    Flow manager that uses ProjectContext and maintains FlowContext.

    This manager replaces the global state management with proper
    context-based approach, enabling better testing and multi-project support.
    """

    def __init__(self, flow_path: Path, project_context: ProjectContext):
        """
        Initialize the flow manager.

        Args:
            flow_path: Path to flow storage directory
            project_context: The project context this manager belongs to
        """
        self.flow_path = flow_path
        self.project_context = project_context
        self.flow_context = FlowContext()

        # Ensure flow directory exists
        self.flow_path.mkdir(parents=True, exist_ok=True)

        # Load existing flow state if available
        self._load_flow_state()

    def create_plan(self, name: str, description: str = "") -> Dict[str, Any]:
        """
        Create a new plan.

        Args:
            name: Plan name
            description: Optional description

        Returns:
            Created plan data
        """
        # Generate plan ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plan_id = f"plan_{timestamp}_{name.replace(' ', '_')[:50]}"

        # Create plan data
        plan_data = {
            'id': plan_id,
            'name': name,
            'description': description,
            'status': 'active',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'tasks': {},
            'metadata': {}
        }

        # Save plan
        plan_path = self.flow_path / 'plans' / plan_id
        plan_path.mkdir(parents=True, exist_ok=True)

        plan_file = plan_path / 'plan.json'
        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(plan_data, f, indent=2, ensure_ascii=False)

        # Update flow context
        self.flow_context.set_plan(plan_id, plan_data)
        self._save_flow_state()

        return plan_data

    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a plan by ID.

        Args:
            plan_id: Plan ID

        Returns:
            Plan data or None if not found
        """
        plan_file = self.flow_path / 'plans' / plan_id / 'plan.json'
        if not plan_file.exists():
            return None

        with open(plan_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def list_plans(self) -> List[Dict[str, Any]]:
        """
        List all plans.

        Returns:
            List of plan data
        """
        plans_dir = self.flow_path / 'plans'
        if not plans_dir.exists():
            return []

        plans = []
        for plan_dir in plans_dir.iterdir():
            if plan_dir.is_dir():
                plan_file = plan_dir / 'plan.json'
                if plan_file.exists():
                    with open(plan_file, 'r', encoding='utf-8') as f:
                        plans.append(json.load(f))

        # Sort by creation date (newest first)
        plans.sort(key=lambda p: p.get('created_at', ''), reverse=True)
        return plans

    def select_plan(self, plan_id: str) -> bool:
        """
        Select a plan as current.

        Args:
            plan_id: Plan ID to select

        Returns:
            True if successful
        """
        plan = self.get_plan(plan_id)
        if not plan:
            return False

        self.flow_context.set_plan(plan_id, plan)
        self._save_flow_state()
        return True

    def add_task(self, title: str, description: str = "") -> Optional[Dict[str, Any]]:
        """
        Add a task to the current plan.

        Args:
            title: Task title
            description: Optional description

        Returns:
            Created task data or None if no plan selected
        """
        if not self.flow_context.current_plan_id:
            return None

        # Generate task ID
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

        # Create task data
        task_data = {
            'id': task_id,
            'title': title,
            'description': description,
            'status': 'todo',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'metadata': {}
        }

        # Load and update plan
        plan = self.get_plan(self.flow_context.current_plan_id)
        if not plan:
            return None

        plan['tasks'][task_id] = task_data
        plan['updated_at'] = datetime.now().isoformat()

        # Save updated plan
        plan_file = self.flow_path / 'plans' / self.flow_context.current_plan_id / 'plan.json'
        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)

        return task_data

    def update_task_status(self, task_id: str, status: str) -> bool:
        """
        Update task status.

        Args:
            task_id: Task ID
            status: New status (todo, in_progress, done)

        Returns:
            True if successful
        """
        if not self.flow_context.current_plan_id:
            return False

        plan = self.get_plan(self.flow_context.current_plan_id)
        if not plan or task_id not in plan['tasks']:
            return False

        # Update task
        plan['tasks'][task_id]['status'] = status
        plan['tasks'][task_id]['updated_at'] = datetime.now().isoformat()

        if status == 'done':
            plan['tasks'][task_id]['completed_at'] = datetime.now().isoformat()
        elif status == 'in_progress' and not self.flow_context.current_task_id:
            # Auto-select task if starting work
            self.flow_context.set_task(task_id, plan['tasks'][task_id])
            self._save_flow_state()

        # Save updated plan
        plan_file = self.flow_path / 'plans' / self.flow_context.current_plan_id / 'plan.json'
        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)

        return True

    def get_context(self) -> FlowContext:
        """Get the current flow context."""
        return self.flow_context

    def _load_flow_state(self):
        """Load flow state from disk."""
        state_file = self.flow_path / 'flow_state.json'
        if state_file.exists():
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    self.flow_context.current_plan_id = state.get('current_plan_id')
                    self.flow_context.current_task_id = state.get('current_task_id')
                    self.flow_context.metadata = state.get('metadata', {})
            except Exception:
                # Ignore errors, use default state
                pass

    def _save_flow_state(self):
        """Save flow state to disk."""
        state_file = self.flow_path / 'flow_state.json'
        state = {
            'current_plan_id': self.flow_context.current_plan_id,
            'current_task_id': self.flow_context.current_task_id,
            'metadata': self.flow_context.metadata,
            'updated_at': datetime.now().isoformat()
        }

        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    def get_current_plan(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected plan."""
        if not self.flow_context.current_plan_id:
            return None
        return self.get_plan(self.flow_context.current_plan_id)

    def get_current_task(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected task."""
        if not self.flow_context.current_task_id:
            return None

        plan = self.get_current_plan()
        if not plan:
            return None

        return plan['tasks'].get(self.flow_context.current_task_id)
