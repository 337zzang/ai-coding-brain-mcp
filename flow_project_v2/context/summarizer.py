"""
Summarizer for Flow Project v2
Generates AI-friendly summaries of project progress and context
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
import json


class ContextSummarizer:
    """Generates intelligent summaries of project context"""

    def __init__(self, context_manager):
        self.context_manager = context_manager

    def generate_summary(self, format_type: str = "detailed") -> str:
        """
        Generate a summary of current context

        Args:
            format_type: "brief", "detailed", or "ai_optimized"

        Returns:
            Formatted summary string
        """
        if format_type == "brief":
            return self._generate_brief_summary()
        elif format_type == "detailed":
            return self._generate_detailed_summary()
        elif format_type == "ai_optimized":
            return self._generate_ai_optimized_summary()
        else:
            raise ValueError(f"Unknown format type: {format_type}")

    def _generate_brief_summary(self) -> str:
        """Generate a brief one-paragraph summary"""
        context = self.context_manager.context
        summary = context["summary"]

        # Calculate session duration
        started = datetime.fromisoformat(context["session"]["started_at"])
        duration = datetime.now() - started
        duration_str = self._format_duration(duration)

        brief = f"Flow Project v2 session active for {duration_str}. "
        brief += f"Progress: {summary['total_plans']} plans ({summary['completed_plans']} completed), "
        brief += f"{summary['total_tasks']} tasks ({summary['completed_tasks']} completed). "
        brief += f"Overall progress: {summary['overall_progress']:.1%}. "

        if summary['last_activity']:
            brief += f"Last activity: {summary['last_activity']}."

        return brief

    def _generate_detailed_summary(self) -> str:
        """Generate a detailed multi-section summary"""
        context = self.context_manager.context
        summary = context["summary"]

        lines = [
            "## 📊 Flow Project v2 - Detailed Summary",
            "",
            f"**Session ID**: {context['session']['session_id'][:8]}",
            f"**Started**: {self._format_timestamp(context['session']['started_at'])}",
            f"**Duration**: {self._calculate_duration_str()}",
            f"**Status**: {context['session']['status']}",
            "",
            "### 📈 Progress Overview",
            f"- **Plans**: {summary['total_plans']} total, {summary['completed_plans']} completed",
            f"- **Tasks**: {summary['total_tasks']} total, {summary['completed_tasks']} completed",
            f"- **Overall Progress**: {summary['overall_progress']:.1%}",
            ""
        ]

        # Active plans section
        active_plans = [p for p in context["plans"] if p["status"] == "active"]
        if active_plans:
            lines.extend([
                "### 🎯 Active Plans",
                ""
            ])
            for plan in active_plans[:5]:  # Limit to 5
                completion = plan.get('completion_rate', 0)
                lines.append(f"- **{plan['title']}**: {plan['task_count']} tasks, {completion:.0%} complete")
            if len(active_plans) > 5:
                lines.append(f"- ... and {len(active_plans) - 5} more")
            lines.append("")

        # Recent activity
        if context["history"]:
            lines.extend([
                "### 🕐 Recent Activity",
                ""
            ])
            for entry in context["history"][-5:]:  # Last 5 entries
                timestamp = self._format_timestamp(entry["timestamp"], relative=True)
                lines.append(f"- {timestamp}: {entry['action']} {entry['target']} '{entry['target_id']}'")
            lines.append("")

        # Key achievements
        if summary["key_achievements"]:
            lines.extend([
                "### 🏆 Key Achievements",
                ""
            ])
            for achievement in summary["key_achievements"]:
                lines.append(f"- {achievement}")
            lines.append("")

        # Next steps
        if summary["next_steps"]:
            lines.extend([
                "### 👉 Suggested Next Steps",
                ""
            ])
            for i, step in enumerate(summary["next_steps"], 1):
                lines.append(f"{i}. {step}")
            lines.append("")

        # Statistics
        lines.extend([
            "### 📊 Statistics",
            ""
        ])
        stats = self._calculate_statistics()
        for key, value in stats.items():
            lines.append(f"- **{key}**: {value}")

        return "\n".join(lines)

    def _generate_ai_optimized_summary(self) -> str:
        """Generate a summary optimized for AI context understanding"""
        context = self.context_manager.context

        # Structure data for AI consumption
        ai_summary = {
            "session_meta": {
                "id": context["session"]["session_id"][:8],
                "duration_minutes": self._calculate_duration_minutes(),
                "status": context["session"]["status"]
            },
            "progress": {
                "plans": {
                    "total": context["summary"]["total_plans"],
                    "completed": context["summary"]["completed_plans"],
                    "active": sum(1 for p in context["plans"] if p["status"] == "active")
                },
                "tasks": {
                    "total": context["summary"]["total_tasks"],
                    "completed": context["summary"]["completed_tasks"],
                    "in_progress": sum(1 for t in context["tasks"] if t["status"] == "in_progress"),
                    "todo": sum(1 for t in context["tasks"] if t["status"] == "todo")
                },
                "overall_progress_percent": round(context["summary"]["overall_progress"] * 100, 1)
            },
            "current_focus": self._identify_current_focus(),
            "recent_actions": self._get_recent_actions(5),
            "blockers": self._identify_blockers(),
            "recommendations": self._generate_recommendations()
        }

        # Format as structured text for AI
        lines = [
            "## AI-Optimized Context Summary",
            "",
            "### Current State",
            f"- Session: {ai_summary['session_meta']['id']} ({ai_summary['session_meta']['duration_minutes']}min)",
            f"- Overall Progress: {ai_summary['progress']['overall_progress_percent']}%",
            f"- Active Plans: {ai_summary['progress']['plans']['active']}",
            f"- Tasks In Progress: {ai_summary['progress']['tasks']['in_progress']}",
            "",
            "### Current Focus",
            ai_summary['current_focus'],
            "",
            "### Recent Actions (Chronological)",
        ]

        for action in ai_summary['recent_actions']:
            lines.append(f"- {action}")

        if ai_summary['blockers']:
            lines.extend([
                "",
                "### Identified Blockers",
            ])
            for blocker in ai_summary['blockers']:
                lines.append(f"- {blocker}")

        lines.extend([
            "",
            "### AI Recommendations",
        ])
        for i, rec in enumerate(ai_summary['recommendations'], 1):
            lines.append(f"{i}. {rec}")

        lines.extend([
            "",
            "### Quick Stats",
            f"- Velocity: {self._calculate_velocity()} tasks/hour",
            f"- Completion Rate: {self._calculate_completion_rate():.1%}",
            f"- Active Time: {self._calculate_active_time_percentage():.1%}",
        ])

        return "\n".join(lines)

    def _identify_current_focus(self) -> str:
        """Identify what the user is currently focused on"""
        context = self.context_manager.context

        # Check for in-progress tasks
        in_progress = [t for t in context["tasks"] if t["status"] == "in_progress"]
        if in_progress:
            task = in_progress[0]
            plan_title = self._get_plan_title(task["plan_id"])
            return f"Working on task '{task['title']}' in plan '{plan_title}'"

        # Check for recently updated plans
        if context["history"]:
            recent = context["history"][-1]
            if recent["target"] == "plan":
                plan = self._get_plan_by_id(recent["target_id"])
                if plan:
                    return f"Managing plan '{plan['title']}'"

        return "No specific focus identified"

    def _get_recent_actions(self, count: int = 5) -> List[str]:
        """Get recent actions in human-readable format"""
        context = self.context_manager.context
        actions = []

        for entry in context["history"][-count:]:
            timestamp = self._format_timestamp(entry["timestamp"], relative=True)
            action_str = f"{timestamp}: {entry['action']} {entry['target']} '{entry['target_id']}'"
            if entry.get("details", {}).get("status"):
                action_str += f" (status: {entry['details']['status']})"
            actions.append(action_str)

        return actions

    def _identify_blockers(self) -> List[str]:
        """Identify potential blockers or issues"""
        context = self.context_manager.context
        blockers = []

        # Check for stalled tasks
        for task in context["tasks"]:
            if task["status"] == "in_progress" and task["started_at"]:
                started = datetime.fromisoformat(task["started_at"])
                if (datetime.now() - started).total_seconds() > 3600:  # 1 hour
                    blockers.append(f"Task '{task['title']}' in progress for over an hour")

        # Check for plans with no progress
        for plan in context["plans"]:
            if plan["status"] == "active" and plan.get("completion_rate", 0) == 0:
                created = datetime.fromisoformat(plan["created_at"])
                if (datetime.now() - created).total_seconds() > 1800:  # 30 minutes
                    blockers.append(f"Plan '{plan['title']}' has no completed tasks")

        return blockers[:3]  # Limit to 3 blockers

    def _generate_recommendations(self) -> List[str]:
        """Generate AI-friendly recommendations"""
        context = self.context_manager.context
        recommendations = []

        # Check task distribution
        todo_count = sum(1 for t in context["tasks"] if t["status"] == "todo")
        in_progress_count = sum(1 for t in context["tasks"] if t["status"] == "in_progress")

        if in_progress_count == 0 and todo_count > 0:
            recommendations.append("Start working on a todo task")
        elif in_progress_count > 3:
            recommendations.append("Consider completing some in-progress tasks before starting new ones")

        # Check for plans without tasks
        empty_plans = [p for p in context["plans"] 
                      if p["status"] == "active" and p["task_count"] == 0]
        if empty_plans:
            recommendations.append(f"Add tasks to plan '{empty_plans[0]['title']}'")

        # Check completion rate
        if context["summary"]["overall_progress"] > 0.8:
            recommendations.append("Great progress! Consider archiving completed plans")
        elif context["summary"]["overall_progress"] < 0.2 and context["summary"]["total_tasks"] > 5:
            recommendations.append("Focus on completing a few tasks to build momentum")

        return recommendations[:3]  # Limit to 3 recommendations

    def _calculate_statistics(self) -> Dict[str, Any]:
        """Calculate various statistics"""
        context = self.context_manager.context
        stats = {}

        # Task statistics
        stats["Average tasks per plan"] = (
            f"{context['summary']['total_tasks'] / max(context['summary']['total_plans'], 1):.1f}"
        )

        # Time statistics
        completed_tasks = [t for t in context["tasks"] if t["status"] == "done" and t["duration"]]
        if completed_tasks:
            avg_duration = sum(t["duration"] for t in completed_tasks) / len(completed_tasks)
            stats["Average task duration"] = self._format_duration(timedelta(seconds=avg_duration))

        # Velocity
        stats["Current velocity"] = f"{self._calculate_velocity()} tasks/hour"

        # Activity pattern
        stats["Most active hour"] = self._find_most_active_hour()

        return stats

    def _calculate_velocity(self) -> float:
        """Calculate tasks completed per hour"""
        context = self.context_manager.context
        completed = context["summary"]["completed_tasks"]

        if completed == 0:
            return 0.0

        duration_hours = self._calculate_duration_minutes() / 60
        if duration_hours == 0:
            return 0.0

        return round(completed / duration_hours, 2)

    def _calculate_completion_rate(self) -> float:
        """Calculate overall completion rate"""
        context = self.context_manager.context
        total = context["summary"]["total_tasks"]

        if total == 0:
            return 0.0

        completed = context["summary"]["completed_tasks"]
        return completed / total

    def _calculate_active_time_percentage(self) -> float:
        """Estimate percentage of time actively working"""
        context = self.context_manager.context

        # Count history entries as active moments
        active_moments = len(context["history"])

        # Assume each moment represents ~5 minutes of activity
        active_minutes = active_moments * 5
        total_minutes = self._calculate_duration_minutes()

        if total_minutes == 0:
            return 0.0

        return min(100.0, (active_minutes / total_minutes) * 100)

    def _find_most_active_hour(self) -> str:
        """Find the hour with most activity"""
        context = self.context_manager.context
        hour_counts = defaultdict(int)

        for entry in context["history"]:
            timestamp = datetime.fromisoformat(entry["timestamp"])
            hour = timestamp.hour
            hour_counts[hour] += 1

        if not hour_counts:
            return "No activity yet"

        most_active = max(hour_counts.items(), key=lambda x: x[1])
        return f"{most_active[0]:02d}:00-{most_active[0]:02d}:59"

    def _format_timestamp(self, timestamp: str, relative: bool = False) -> str:
        """Format timestamp for display"""
        dt = datetime.fromisoformat(timestamp)

        if relative:
            delta = datetime.now() - dt
            if delta.total_seconds() < 60:
                return "just now"
            elif delta.total_seconds() < 3600:
                minutes = int(delta.total_seconds() / 60)
                return f"{minutes}m ago"
            elif delta.total_seconds() < 86400:
                hours = int(delta.total_seconds() / 3600)
                return f"{hours}h ago"
            else:
                return dt.strftime("%Y-%m-%d %H:%M")
        else:
            return dt.strftime("%Y-%m-%d %H:%M:%S")

    def _format_duration(self, duration: timedelta) -> str:
        """Format duration for display"""
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    def _calculate_duration_str(self) -> str:
        """Calculate session duration as string"""
        context = self.context_manager.context
        started = datetime.fromisoformat(context["session"]["started_at"])
        duration = datetime.now() - started
        return self._format_duration(duration)

    def _calculate_duration_minutes(self) -> int:
        """Calculate session duration in minutes"""
        context = self.context_manager.context
        started = datetime.fromisoformat(context["session"]["started_at"])
        duration = datetime.now() - started
        return int(duration.total_seconds() / 60)

    def _get_plan_title(self, plan_id: str) -> str:
        """Get plan title by ID"""
        plan = self._get_plan_by_id(plan_id)
        return plan["title"] if plan else "Unknown Plan"

    def _get_plan_by_id(self, plan_id: str) -> Optional[Dict]:
        """Get plan by ID"""
        context = self.context_manager.context
        for plan in context["plans"]:
            if plan["plan_id"] == plan_id:
                return plan
        return None
