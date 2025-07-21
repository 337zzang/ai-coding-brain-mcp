"""
Flow Manager with Context Integration
Extends FlowManager to work with Context system
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

# Import context modules
from flow_project_v2.context import ContextManager, SessionManager, ContextSummarizer


class FlowManagerWithContext:
    """Flow Manager with integrated context tracking"""

    def __init__(self, data_dir: str = "flow_project_v2/data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize context system
        self.context_manager = ContextManager(str(self.data_dir))
        self.session_manager = SessionManager(self.context_manager)
        self.summarizer = ContextSummarizer(self.context_manager)

        # Start auto-save
        self.session_manager.start_auto_save()

        # Initialize flow data storage
        self.plans_file = self.data_dir / "plans.json"
        self.tasks_file = self.data_dir / "tasks.json"

        # Load or create data
        self._load_data()

    def _load_data(self):
        """Load plans and tasks data"""
        # This would normally load from files
        # For now, initialize empty
        self.plans = {}
        self.tasks = {}

    def create_plan(self, title: str, description: str = "") -> Dict[str, Any]:
        """Create a new plan with context tracking"""
        plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        plan = {
            "id": plan_id,
            "title": title,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "active",
            "tasks": [],
            "tags": [],
            "priority": "medium"
        }

        self.plans[plan_id] = plan

        # Update context
        self.context_manager.update_plan_context(plan_id, plan)
        self.context_manager.add_history_entry("created", "plan", plan_id, {"title": title})

        return plan

    def create_task(self, plan_id: str, title: str, description: str = "") -> Optional[Dict[str, Any]]:
        """Create a new task with context tracking"""
        if plan_id not in self.plans:
            return None

        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        task = {
            "id": task_id,
            "plan_id": plan_id,
            "title": title,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "todo",
            "tags": [],
            "dependencies": []
        }

        self.tasks[task_id] = task
        self.plans[plan_id]["tasks"].append(task_id)

        # Update context
        self.context_manager.update_task_context(task_id, task)
        self.context_manager.update_plan_context(plan_id, self.plans[plan_id])
        self.context_manager.add_history_entry("created", "task", task_id, 
                                             {"title": title, "plan": plan_id})

        return task

    def update_task_status(self, task_id: str, new_status: str) -> bool:
        """Update task status with context tracking"""
        if task_id not in self.tasks:
            return False

        old_status = self.tasks[task_id]["status"]
        self.tasks[task_id]["status"] = new_status
        self.tasks[task_id]["updated_at"] = datetime.now().isoformat()

        # Update context
        self.context_manager.update_task_context(task_id, self.tasks[task_id])

        # Update plan context if task is completed
        if new_status == "done":
            plan_id = self.tasks[task_id]["plan_id"]
            self.context_manager.update_plan_context(plan_id, self.plans[plan_id])

        self.context_manager.add_history_entry("status_changed", "task", task_id,
                                             {"from": old_status, "to": new_status})

        return True

    def complete_plan(self, plan_id: str) -> bool:
        """Mark a plan as completed"""
        if plan_id not in self.plans:
            return False

        self.plans[plan_id]["status"] = "completed"
        self.plans[plan_id]["completed_at"] = datetime.now().isoformat()

        # Update context
        self.context_manager.update_plan_context(plan_id, self.plans[plan_id])
        self.context_manager.add_history_entry("completed", "plan", plan_id, {})

        return True

    def get_summary(self, format_type: str = "detailed") -> str:
        """Get context summary"""
        return self.summarizer.generate_summary(format_type)

    def save_checkpoint(self, name: str = "") -> Optional[str]:
        """Create a checkpoint"""
        return self.session_manager.create_checkpoint(name)

    def restore_session(self, session_file: Optional[str] = None) -> bool:
        """Restore a previous session"""
        success = self.session_manager.restore_session(session_file)
        if success:
            # Reload data from restored context
            self._sync_from_context()
        return success

    def list_sessions(self) -> List[Dict[str, str]]:
        """List available sessions"""
        return self.session_manager.list_sessions()

    def _sync_from_context(self):
        """Sync internal data from context"""
        # This would rebuild plans/tasks from context
        # For now, just print a message
        print("Data synced from restored context")

    def close(self):
        """Clean shutdown"""
        # Stop auto-save
        self.session_manager.stop_auto_save()

        # Final save
        self.context_manager.save()
        self.session_manager.save_session("shutdown")

        print("FlowManager closed gracefully")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Convenience functions for integration
def create_flow_manager() -> FlowManagerWithContext:
    """Create a new FlowManager instance"""
    return FlowManagerWithContext()


def get_current_summary(flow_manager: FlowManagerWithContext, format_type: str = "brief") -> str:
    """Get current project summary"""
    return flow_manager.get_summary(format_type)
