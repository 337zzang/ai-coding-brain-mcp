"""
Context Manager for Flow Project v2
Handles context persistence, session management, and summarization
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


class ContextManager:
    """Manages project context and session state"""

    def __init__(self, data_dir: str = "flow_project_v2/data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.context_file = self.data_dir / "current_context.json"
        self.archive_dir = self.data_dir / "archive"
        self.archive_dir.mkdir(exist_ok=True)

        self.context: Dict[str, Any] = self._load_or_create_context()
        self._last_save_time = datetime.now()

    def _load_or_create_context(self) -> Dict[str, Any]:
        """Load existing context or create new one"""
        if self.context_file.exists():
            try:
                with open(self.context_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load context: {e}")
                self._archive_corrupted_context()

        # Create new context
        return self._create_new_context()

    def _create_new_context(self) -> Dict[str, Any]:
        """Create a new context structure"""
        return {
            "session": {
                "session_id": str(uuid.uuid4()),
                "project_id": "flow_project_v2",
                "started_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "status": "active"
            },
            "plans": [],
            "tasks": [],
            "history": [],
            "summary": {
                "total_plans": 0,
                "completed_plans": 0,
                "total_tasks": 0,
                "completed_tasks": 0,
                "overall_progress": 0.0,
                "last_activity": "Session started",
                "key_achievements": [],
                "next_steps": []
            },
            "metadata": {
                "ai_model": "claude-3-opus",
                "context_version": "2.0",
                "tags": [],
                "custom": {}
            }
        }

    def save(self, force: bool = False) -> bool:
        """Save context to disk"""
        try:
            # Update last_updated timestamp
            self.context["session"]["last_updated"] = datetime.now().isoformat()

            # Save to file
            with open(self.context_file, 'w', encoding='utf-8') as f:
                json.dump(self.context, f, indent=2, ensure_ascii=False)

            self._last_save_time = datetime.now()
            return True
        except Exception as e:
            print(f"Error saving context: {e}")
            return False

    def add_history_entry(self, action: str, target: str, target_id: str, details: Dict = None):
        """Add entry to history"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "target": target,
            "target_id": target_id,
            "details": details or {}
        }
        self.context["history"].append(entry)

        # Update last activity
        self.context["summary"]["last_activity"] = f"{action} {target} '{target_id}'"

        # Auto-save if needed
        self._auto_save()

    def update_plan_context(self, plan_id: str, plan_data: Dict):
        """Update context when plan changes"""
        # Find or create plan entry
        plan_entry = None
        for p in self.context["plans"]:
            if p["plan_id"] == plan_id:
                plan_entry = p
                break

        if not plan_entry:
            plan_entry = {
                "plan_id": plan_id,
                "title": plan_data.get("title", ""),
                "created_at": plan_data.get("created_at", datetime.now().isoformat()),
                "status": plan_data.get("status", "active"),
                "task_count": 0,
                "completion_rate": 0.0
            }
            self.context["plans"].append(plan_entry)
        else:
            # Update existing entry
            plan_entry.update({
                "status": plan_data.get("status", plan_entry["status"]),
                "task_count": len(plan_data.get("tasks", [])),
                "completion_rate": self._calculate_completion_rate(plan_data)
            })

        # Update summary
        self._update_summary()

        # Add to history
        self.add_history_entry("updated", "plan", plan_id, {"status": plan_entry["status"]})

    def update_task_context(self, task_id: str, task_data: Dict):
        """Update context when task changes"""
        # Find or create task entry
        task_entry = None
        for t in self.context["tasks"]:
            if t["task_id"] == task_id:
                task_entry = t
                break

        if not task_entry:
            task_entry = {
                "task_id": task_id,
                "plan_id": task_data.get("plan_id", ""),
                "title": task_data.get("title", ""),
                "status": task_data.get("status", "todo"),
                "started_at": None,
                "completed_at": None,
                "duration": None
            }
            self.context["tasks"].append(task_entry)

        # Update status and timestamps
        old_status = task_entry["status"]
        new_status = task_data.get("status", old_status)

        if old_status != "in_progress" and new_status == "in_progress":
            task_entry["started_at"] = datetime.now().isoformat()
        elif new_status == "done" and not task_entry["completed_at"]:
            task_entry["completed_at"] = datetime.now().isoformat()
            if task_entry["started_at"]:
                start = datetime.fromisoformat(task_entry["started_at"])
                duration = (datetime.now() - start).total_seconds()
                task_entry["duration"] = int(duration)

        task_entry["status"] = new_status

        # Update summary
        self._update_summary()

        # Add to history
        self.add_history_entry("updated", "task", task_id, {"status": new_status})

    def get_summary(self, format_type="brief") -> Dict[str, Any]:
        """Get current context summary"""
        self._update_summary()
        return self.context["summary"]

    def _update_summary(self):
        """Update summary statistics"""
        summary = self.context["summary"]

        # Count plans
        summary["total_plans"] = len(self.context["plans"])
        summary["completed_plans"] = sum(1 for p in self.context["plans"] 
                                       if p["status"] == "completed")

        # Count tasks
        summary["total_tasks"] = len(self.context["tasks"])
        summary["completed_tasks"] = sum(1 for t in self.context["tasks"] 
                                       if t["status"] == "done")

        # Calculate overall progress
        if summary["total_tasks"] > 0:
            summary["overall_progress"] = summary["completed_tasks"] / summary["total_tasks"]
        else:
            summary["overall_progress"] = 0.0

        # Update key achievements
        self._update_achievements()

        # Update next steps
        self._update_next_steps()

    def _update_achievements(self):
        """Update key achievements list"""
        achievements = []

        # Check for completed plans
        completed_plans = [p for p in self.context["plans"] if p["status"] == "completed"]
        if completed_plans:
            achievements.append(f"Completed {len(completed_plans)} plans")

        # Check for task streaks
        completed_tasks = sum(1 for t in self.context["tasks"] if t["status"] == "done")
        if completed_tasks >= 5:
            achievements.append(f"Completed {completed_tasks} tasks")

        self.context["summary"]["key_achievements"] = achievements

    def _update_next_steps(self):
        """Suggest next steps based on current state"""
        next_steps = []

        # Check for incomplete tasks
        todo_tasks = [t for t in self.context["tasks"] if t["status"] == "todo"]
        if todo_tasks:
            next_steps.append(f"Complete {len(todo_tasks)} remaining tasks")

        # Check for plans without tasks
        for plan in self.context["plans"]:
            if plan["task_count"] == 0 and plan["status"] == "active":
                next_steps.append(f"Add tasks to plan '{plan['title']}'")
                break

        # If no plans exist
        if not self.context["plans"]:
            next_steps.append("Create your first plan")

        self.context["summary"]["next_steps"] = next_steps[:3]  # Limit to 3 suggestions

    def _calculate_completion_rate(self, plan_data: Dict) -> float:
        """Calculate completion rate for a plan"""
        tasks = plan_data.get("tasks", [])
        if not tasks:
            return 0.0

        completed = sum(1 for t in tasks if t.get("status") == "done")
        return completed / len(tasks)

    def _auto_save(self):
        """Auto-save if enough time has passed"""
        # Save every 30 seconds
        if (datetime.now() - self._last_save_time).total_seconds() > 30:
            self.save()

    def _archive_corrupted_context(self):
        """Archive corrupted context file"""
        if self.context_file.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"corrupted_context_{timestamp}.json"
            archive_path = self.archive_dir / archive_name
            self.context_file.rename(archive_path)
            print(f"Archived corrupted context to: {archive_path}")

    def archive_session(self, reason: str = "manual"):
        """Archive current session and start fresh"""
        if self.context:
            # Update session status
            self.context["session"]["status"] = "completed"
            self.save()

            # Archive file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_id = self.context["session"]["session_id"][:8]
            archive_name = f"session_{session_id}_{timestamp}_{reason}.json"
            archive_path = self.archive_dir / archive_name

            self.context_file.rename(archive_path)
            print(f"Session archived to: {archive_path}")

            # Create new context
            self.context = self._create_new_context()
            self.save()

    def get_history(self, limit=10):
        """작업 히스토리 반환"""
        try:
            history = []
            # 최근 히스토리 항목 반환
            if hasattr(self, 'history') and self.history:
                history = self.history[-limit:]
            elif hasattr(self, 'context') and 'history' in self.context:
                history = self.context['history'][-limit:]
            return history
        except Exception as e:
            return [{'error': f'히스토리 조회 실패: {str(e)}'}]

    def get_stats(self):
        """통계 정보 반환"""
        try:
            stats = {
                'total_tasks': 0,
                'completed_tasks': 0,
                'files_modified': 0,
                'commands_executed': 0
            }

            # 실제 데이터가 있으면 사용
            if hasattr(self, 'context'):
                stats['total_tasks'] = len(self.context.get('tasks', []))
                stats['completed_tasks'] = len([t for t in self.context.get('tasks', []) if t.get('status') == 'completed'])

            return stats
        except Exception as e:
            return {'error': f'통계 생성 실패: {str(e)}'}

