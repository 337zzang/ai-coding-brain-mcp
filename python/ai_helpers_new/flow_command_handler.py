"""
FlowCommandHandler - Handler for /flow commands
Manages Flow Project v2 operations and switching between flows
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from flow_project_v2.flow_manager_integrated import FlowManagerWithContext
    FLOW_V2_AVAILABLE = True
except ImportError:
    FLOW_V2_AVAILABLE = False
    print("⚠️ Flow Project v2 not available")


class FlowCommandHandler:
    """Handles /flow commands for managing Flow Projects"""

    def __init__(self, data_dir: str = ".ai-brain"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.flows_dir = Path("flow_project_v2/flows")
        self.flows_dir.mkdir(parents=True, exist_ok=True)

        self.current_flow_file = self.data_dir / "current_flow.json"
        self.flows_registry = self.data_dir / "flows_registry.json"

        # Load or create flows registry
        self._load_flows_registry()

        # Current flow manager
        self.current_flow = None
        self.current_flow_id = None
        self._load_current_flow()

    def _load_flows_registry(self):
        """Load registry of all flows"""
        if self.flows_registry.exists():
            try:
                with open(self.flows_registry, 'r', encoding='utf-8') as f:
                    self.flows = json.load(f)
            except:
                self.flows = {}
        else:
            self.flows = {}
            self._save_flows_registry()

    def _save_flows_registry(self):
        """Save flows registry"""
        with open(self.flows_registry, 'w', encoding='utf-8') as f:
            json.dump(self.flows, f, indent=2, ensure_ascii=False)

    def _load_current_flow(self):
        """Load current active flow"""
        if self.current_flow_file.exists():
            try:
                with open(self.current_flow_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.current_flow_id = data.get('current_flow_id')
                    if self.current_flow_id and FLOW_V2_AVAILABLE:
                        flow_data_dir = self.flows_dir / self.current_flow_id
                        if flow_data_dir.exists():
                            self.current_flow = FlowManagerWithContext(str(flow_data_dir))
            except Exception as e:
                print(f"Error loading current flow: {e}")

    def _save_current_flow(self):
        """Save current flow reference"""
        data = {
            'current_flow_id': self.current_flow_id,
            'updated_at': datetime.now().isoformat()
        }
        with open(self.current_flow_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def handle_flow_command(self, args: List[str]) -> Dict[str, Any]:
        """Main handler for /flow commands"""
        if not args:
            return self._show_current_flow()

        subcommand = args[0]
        sub_args = args[1:] if len(args) > 1 else []

        commands = {
            'list': self._list_flows,
            'switch': lambda: self._switch_flow(sub_args),
            'create': lambda: self._create_flow(sub_args),
            'delete': lambda: self._delete_flow(sub_args),
            'status': self._show_flow_status,
            'plan': lambda: self._handle_plan_command(sub_args),
            'task': lambda: self._handle_task_command(sub_args),
            'summary': lambda: self._show_summary(sub_args),
            'export': self._export_flow,
            'import': lambda: self._import_flow(sub_args),
            'help': self._show_flow_help
        }

        if subcommand in commands:
            return commands[subcommand]()
        else:
            return {'ok': False, 'error': f"Unknown flow command: {subcommand}. Use /flow help"}

    def _show_current_flow(self) -> Dict[str, Any]:
        """Show current flow info"""
        if not self.current_flow_id:
            return {'ok': True, 'data': "No active flow. Use /flow create <name> or /flow list"}

        flow_info = self.flows.get(self.current_flow_id, {})
        output = f"\n🌊 Current Flow: {flow_info.get('name', self.current_flow_id)}\n"
        output += f"ID: {self.current_flow_id}\n"
        output += f"Created: {flow_info.get('created_at', 'Unknown')}\n"

        if self.current_flow and hasattr(self.current_flow, 'get_summary'):
            summary = self.current_flow.get_summary('brief')
            output += f"\nSummary: {summary}"

        return {'ok': True, 'data': output}

    def _list_flows(self) -> Dict[str, Any]:
        """List all available flows"""
        if not self.flows:
            return {'ok': True, 'data': "No flows created yet. Use /flow create <name>"}

        output = "\n📋 Available Flows:\n"
        for flow_id, flow_info in self.flows.items():
            current = " (current)" if flow_id == self.current_flow_id else ""
            output += f"\n[{flow_id}] {flow_info['name']}{current}\n"
            output += f"  Created: {flow_info.get('created_at', 'Unknown')}\n"
            output += f"  Description: {flow_info.get('description', 'No description')}\n"

        return {'ok': True, 'data': output}

    def _create_flow(self, args: List[str]) -> Dict[str, Any]:
        """Create a new flow"""
        if not args:
            return {'ok': False, 'error': "Flow name required. Usage: /flow create <name>"}

        if not FLOW_V2_AVAILABLE:
            return {'ok': False, 'error': "Flow Project v2 is not available"}

        name = ' '.join(args)
        flow_id = f"flow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Create flow directory
        flow_data_dir = self.flows_dir / flow_id
        flow_data_dir.mkdir(exist_ok=True)

        # Register flow
        self.flows[flow_id] = {
            'name': name,
            'created_at': datetime.now().isoformat(),
            'description': f"Flow project: {name}"
        }
        self._save_flows_registry()

        # Switch to new flow
        return self._switch_flow([flow_id])

    def _switch_flow(self, args: List[str]) -> Dict[str, Any]:
        """Switch to a different flow"""
        if not args:
            return {'ok': False, 'error': "Flow ID required. Use /flow list to see available flows"}

        flow_id = args[0]

        # Check if flow exists
        if flow_id not in self.flows:
            # Try to find by name
            for fid, finfo in self.flows.items():
                if finfo['name'].lower() == flow_id.lower():
                    flow_id = fid
                    break
            else:
                return {'ok': False, 'error': f"Flow '{flow_id}' not found"}

        if not FLOW_V2_AVAILABLE:
            return {'ok': False, 'error': "Flow Project v2 is not available"}

        # Save current flow if exists
        if self.current_flow:
            try:
                self.current_flow.close()
            except:
                pass

        # Load new flow
        flow_data_dir = self.flows_dir / flow_id
        flow_data_dir.mkdir(exist_ok=True)

        try:
            self.current_flow = FlowManagerWithContext(str(flow_data_dir))
            self.current_flow_id = flow_id
            self._save_current_flow()

            flow_info = self.flows[flow_id]
            return {'ok': True, 'data': f"Switched to flow: {flow_info['name']} ({flow_id})"}
        except Exception as e:
            return {'ok': False, 'error': f"Failed to switch flow: {e}"}

    def _delete_flow(self, args: List[str]) -> Dict[str, Any]:
        """Delete a flow (with confirmation)"""
        if not args:
            return {'ok': False, 'error': "Flow ID required"}

        flow_id = args[0]

        if flow_id not in self.flows:
            return {'ok': False, 'error': f"Flow '{flow_id}' not found"}

        if flow_id == self.current_flow_id:
            return {'ok': False, 'error': "Cannot delete current flow. Switch to another flow first"}

        # Confirm deletion
        if len(args) < 2 or args[1] != "confirm":
            flow_info = self.flows[flow_id]
            return {
                'ok': True, 
                'data': f"⚠️ Delete flow '{flow_info['name']}'? Use: /flow delete {flow_id} confirm"
            }

        # Delete flow
        import shutil
        flow_data_dir = self.flows_dir / flow_id
        if flow_data_dir.exists():
            shutil.rmtree(flow_data_dir)

        del self.flows[flow_id]
        self._save_flows_registry()

        return {'ok': True, 'data': f"Flow '{flow_id}' deleted"}

    def _show_flow_status(self) -> Dict[str, Any]:
        """Show detailed flow status"""
        if not self.current_flow:
            return {'ok': False, 'error': "No active flow"}

        if hasattr(self.current_flow, 'get_summary'):
            summary = self.current_flow.get_summary('detailed')
            return {'ok': True, 'data': summary}
        else:
            return {'ok': False, 'error': "Current flow does not support status"}

    def _handle_plan_command(self, args: List[str]) -> Dict[str, Any]:
        """Handle plan-related commands"""
        if not self.current_flow:
            return {'ok': False, 'error': "No active flow"}

        if not args:
            return {'ok': False, 'error': "Plan command required. Use: add, list"}

        action = args[0]

        if action == 'add':
            if len(args) < 2:
                return {'ok': False, 'error': "Plan title required"}
            title = ' '.join(args[1:])
            plan = self.current_flow.create_plan(title)
            return {'ok': True, 'data': f"Plan created: {plan['id']} - {plan['title']}"}

        elif action == 'list':
            # List plans
            if hasattr(self.current_flow, 'plans'):
                plans = self.current_flow.plans
                if not plans:
                    return {'ok': True, 'data': "No plans in current flow"}

                output = "\n📋 Plans:\n"
                for plan_id, plan in plans.items():
                    output += f"  [{plan_id}] {plan['title']} ({plan['status']})\n"
                return {'ok': True, 'data': output}
            else:
                return {'ok': False, 'error': "Current flow does not support plans"}

        else:
            return {'ok': False, 'error': f"Unknown plan action: {action}"}

    def _handle_task_command(self, args: List[str]) -> Dict[str, Any]:
        """Handle task-related commands"""
        if not self.current_flow:
            return {'ok': False, 'error': "No active flow"}

        if not args:
            return {'ok': False, 'error': "Task command required. Use: add <plan_id> <title>"}

        action = args[0]

        if action == 'add':
            if len(args) < 3:
                return {'ok': False, 'error': "Usage: /flow task add <plan_id> <title>"}
            plan_id = args[1]
            title = ' '.join(args[2:])

            task = self.current_flow.create_task(plan_id, title)
            if task:
                return {'ok': True, 'data': f"Task created: {task['id']} - {task['title']}"}
            else:
                return {'ok': False, 'error': "Failed to create task. Check plan ID"}

        else:
            return {'ok': False, 'error': f"Unknown task action: {action}"}

    def _show_summary(self, args: List[str]) -> Dict[str, Any]:
        """Show flow summary"""
        if not self.current_flow:
            return {'ok': False, 'error': "No active flow"}

        format_type = args[0] if args else 'brief'

        if format_type not in ['brief', 'detailed', 'ai']:
            return {'ok': False, 'error': "Format must be: brief, detailed, or ai"}

        if hasattr(self.current_flow, 'get_summary'):
            summary = self.current_flow.get_summary(format_type)
            return {'ok': True, 'data': summary}
        else:
            return {'ok': False, 'error': "Current flow does not support summaries"}

    def _export_flow(self) -> Dict[str, Any]:
        """Export current flow to JSON"""
        if not self.current_flow:
            return {'ok': False, 'error': "No active flow"}

        export_data = {
            'flow_id': self.current_flow_id,
            'flow_info': self.flows.get(self.current_flow_id, {}),
            'exported_at': datetime.now().isoformat()
        }

        # Add flow data if available
        if hasattr(self.current_flow, 'context_manager'):
            export_data['context'] = self.current_flow.context_manager.context

        # Save to file
        export_file = f"flow_export_{self.current_flow_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        export_path = self.data_dir / export_file

        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        return {'ok': True, 'data': f"Flow exported to: {export_path}"}

    def _import_flow(self, args: List[str]) -> Dict[str, Any]:
        """Import flow from JSON"""
        if not args:
            return {'ok': False, 'error': "Import file required"}

        # TODO: Implement import functionality
        return {'ok': False, 'error': "Import functionality not yet implemented"}

    def _show_flow_help(self) -> Dict[str, Any]:
        """Show flow command help"""
        help_text = """
🌊 Flow Commands:
  /flow                          - Show current flow
  /flow list                     - List all flows
  /flow create <name>            - Create new flow
  /flow switch <id/name>         - Switch to flow
  /flow delete <id> [confirm]    - Delete flow
  /flow status                   - Detailed flow status

  Plan Commands:
  /flow plan add <title>         - Add plan to current flow
  /flow plan list                - List plans in flow

  Task Commands:
  /flow task add <plan> <title>  - Add task to plan

  Other Commands:
  /flow summary [format]         - Show summary (brief/detailed/ai)
  /flow export                   - Export flow to JSON
  /flow import <file>            - Import flow from JSON
  /flow help                     - Show this help
"""
        return {'ok': True, 'data': help_text}


# Singleton instance
_flow_handler = None

def get_flow_handler() -> FlowCommandHandler:
    """Get or create FlowCommandHandler instance"""
    global _flow_handler
    if _flow_handler is None:
        _flow_handler = FlowCommandHandler()
    return _flow_handler
