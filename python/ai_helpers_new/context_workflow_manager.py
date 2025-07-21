"""
ContextWorkflowManager - WorkflowManager with Context tracking
Decorator pattern implementation for non-intrusive integration
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime
import sys

# Add flow_project_v2 to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from flow_project_v2.context import ContextManager, SessionManager, ContextSummarizer
    CONTEXT_AVAILABLE = True
except ImportError:
    CONTEXT_AVAILABLE = False


class ContextWorkflowManager:
    """
    Decorator for WorkflowManager that adds Context tracking capabilities
    Uses environment variable CONTEXT_SYSTEM to enable/disable context features
    """

    def __init__(self, workflow_manager):
        """
        Initialize with existing WorkflowManager instance

        Args:
            workflow_manager: Existing WorkflowManager instance
        """
        self.wm = workflow_manager

        # Check if context should be enabled
        self.context_enabled = (
            os.environ.get('CONTEXT_SYSTEM', 'off').lower() == 'on'
            and CONTEXT_AVAILABLE
        )

        if self.context_enabled:
            try:
                # Initialize context components
                data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'flow_project_v2', 'data')
                self.context_mgr = ContextManager(data_dir)
                self.session_mgr = SessionManager(self.context_mgr, auto_save_interval=None)  # No auto-save
                self.summarizer = ContextSummarizer(self.context_mgr)
                print("✅ Context System enabled")
            except Exception as e:
                print(f"⚠️ Context System initialization failed: {e}")
                self.context_enabled = False
        else:
            if not CONTEXT_AVAILABLE:
                print("ℹ️ Context System not available (missing modules)")
            else:
                print("ℹ️ Context System disabled (set CONTEXT_SYSTEM=on to enable)")

    # Delegate all attributes to wrapped WorkflowManager
    def __getattr__(self, name):
        """Forward all undefined attributes to wrapped WorkflowManager"""
        return getattr(self.wm, name)

    # Override specific methods to add context tracking

    def add_task(self, name: str, description: str = "") -> Dict[str, Any]:
        """Add task with context tracking"""
        result = self.wm.add_task(name, description)

        if self.context_enabled and result.get('ok'):
            try:
                task_data = result['data']
                # Track in context
                self.context_mgr.update_task_context(task_data['id'], {
                    'plan_id': 'workflow',  # Default plan for workflow tasks
                    'title': task_data['name'],
                    'status': task_data['status'],
                    'created_at': task_data.get('created_at', datetime.now().isoformat())
                })
                self.context_mgr.add_history_entry(
                    'created', 'task', task_data['id'], 
                    {'name': task_data['name']}
                )
            except Exception as e:
                print(f"⚠️ Context tracking error: {e}")

        return result

    def start_task(self, task_id: str) -> Dict[str, Any]:
        """Start task with context tracking"""
        result = self.wm.start_task(task_id)

        if self.context_enabled and result.get('ok'):
            try:
                task_data = result['data']
                # Update context
                self.context_mgr.update_task_context(task_id, {
                    'status': 'in_progress'
                })
                self.context_mgr.add_history_entry(
                    'started', 'task', task_id, {}
                )
            except Exception as e:
                print(f"⚠️ Context tracking error: {e}")

        return result

    def complete_task(self, task_id: str, summary: str = "") -> Dict[str, Any]:
        """Complete task with context tracking and save"""
        result = self.wm.complete_task(task_id, summary)

        if self.context_enabled and result.get('ok'):
            try:
                task_data = result['data']
                # Update context
                self.context_mgr.update_task_context(task_id, {
                    'status': 'completed'
                })
                self.context_mgr.add_history_entry(
                    'completed', 'task', task_id, 
                    {'summary': summary}
                )

                # Save on completion (instead of auto-save)
                self.context_mgr.save()
                self.session_mgr.save_session('task_completion')

            except Exception as e:
                print(f"⚠️ Context tracking error: {e}")

        return result

    def wf_command(self, command: str) -> Dict[str, Any]:
        """Extended command handler with context commands"""

        # Handle context-specific commands if enabled
        if self.context_enabled and command.startswith('/'):
            parts = command.strip().split()
            cmd = parts[0][1:]  # Remove leading /
            args = parts[1:] if len(parts) > 1 else []

            # Context commands
            if cmd == 'context':
                return self._handle_context_command(args)
            elif cmd == 'session':
                return self._handle_session_command(args)
            elif cmd == 'history':
                return self._handle_history_command(args)
            elif cmd == 'stats':
                return self._show_stats()

        # Pass through to original WorkflowManager
        return self.wm.wf_command(command)

    def _handle_context_command(self, args: list) -> Dict[str, Any]:
        """Handle /context commands"""
        if not args:
            # Default to brief summary
            summary = self.summarizer.generate_summary('brief')
            return {'ok': True, 'data': summary}

        subcommand = args[0]
        if subcommand == 'show':
            format_type = args[1] if len(args) > 1 else 'brief'
            if format_type in ['brief', 'detailed', 'ai']:
                summary = self.summarizer.generate_summary(format_type)
                return {'ok': True, 'data': summary}
            else:
                return {'ok': False, 'error': f"Unknown format: {format_type}. Use brief, detailed, or ai"}
        else:
            return {'ok': False, 'error': f"Unknown context command: {subcommand}"}

    def _handle_session_command(self, args: list) -> Dict[str, Any]:
        """Handle /session commands"""
        if not args:
            return {'ok': False, 'error': "Session command requires subcommand: save, list, restore"}

        subcommand = args[0]

        if subcommand == 'save':
            name = args[1] if len(args) > 1 else ""
            path = self.session_mgr.save_session('manual')
            if path:
                return {'ok': True, 'data': f"Session saved to: {path}"}
            else:
                return {'ok': False, 'error': "Failed to save session"}

        elif subcommand == 'list':
            sessions = self.session_mgr.list_sessions()
            if sessions:
                output = "\n📁 Available sessions:\n"
                for session in sessions[:10]:
                    output += f"  - {session['session_id'][:8]} ({session['type']}) - {session['timestamp']}\n"
                return {'ok': True, 'data': output}
            else:
                return {'ok': True, 'data': "No sessions found"}

        elif subcommand == 'restore':
            if len(args) < 2:
                return {'ok': False, 'error': "Session restore requires session file path"}
            session_file = args[1]
            if self.session_mgr.restore_session(session_file):
                return {'ok': True, 'data': f"Session restored from: {session_file}"}
            else:
                return {'ok': False, 'error': "Failed to restore session"}

        else:
            return {'ok': False, 'error': f"Unknown session command: {subcommand}"}

    def _handle_history_command(self, args: list) -> Dict[str, Any]:
        """Handle /history command"""
        limit = int(args[0]) if args and args[0].isdigit() else 10

        history = self.context_mgr.context.get('history', [])
        recent = history[-limit:]

        if recent:
            output = f"\n📜 Recent history (last {len(recent)} entries):\n"
            for entry in recent:
                timestamp = entry['timestamp'].split('T')[1].split('.')[0]  # Time only
                output += f"  {timestamp} - {entry['action']} {entry['target']} '{entry['target_id']}'\n"
            return {'ok': True, 'data': output}
        else:
            return {'ok': True, 'data': "No history available"}

    def _show_stats(self) -> Dict[str, Any]:
        """Show statistics"""
        summary = self.context_mgr.get_summary()

        output = "\n📊 Workflow Statistics:\n"
        output += f"  Total tasks: {summary['total_tasks']}\n"
        output += f"  Completed: {summary['completed_tasks']}\n"
        output += f"  Progress: {summary['overall_progress']:.1%}\n"
        output += f"  Last activity: {summary['last_activity']}\n"

        if summary['key_achievements']:
            output += "\n🏆 Achievements:\n"
            for achievement in summary['key_achievements']:
                output += f"  - {achievement}\n"

        return {'ok': True, 'data': output}

    def _show_help(self) -> Dict[str, Any]:
        """Extended help with context commands"""
        base_help = self.wm._show_help()

        if self.context_enabled:
            context_help = """
📝 Context Commands:
  /context [show brief|detailed|ai] - Show context summary
  /session save [name]              - Save current session
  /session list                     - List saved sessions
  /session restore <file>           - Restore session
  /history [n]                      - Show last n history entries
  /stats                            - Show statistics
"""
            base_help['data'] += context_help

        return base_help


def create_context_workflow_manager(workflow_manager):
    """Factory function to create ContextWorkflowManager"""
    return ContextWorkflowManager(workflow_manager)
