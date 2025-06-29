#!/usr/bin/env python3
"""
Simplified Command Executor - Direct command execution without complex serialization
"""

import sys
import json
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def execute_command(command_data):
    """Execute command and return result"""
    try:
        command = command_data.get('command', '').lower()
        action = command_data.get('action', '')
        payload = command_data.get('payload', {})
        
        # Import commands as needed
        if command == 'plan':
            from commands.plan import cmd_plan
            if action == 'create':
                result = cmd_plan('create', payload.get('name', ''), payload.get('description', ''))
            elif action == 'show':
                result = cmd_plan('show')
            else:
                return {"status": "error", "error": {"code": "INVALID_ACTION", "message": f"Invalid action: {action}"}}
        
        elif command == 'task':
            from commands.task import cmd_task
            if action == 'add':
                result = cmd_task('add', payload.get('phase'), payload.get('title'), payload.get('description'))
            elif action == 'list':
                result = cmd_task('list')
            elif action == 'done':
                result = cmd_task('done', payload.get('task_id'))
            else:
                return {"status": "error", "error": {"code": "INVALID_ACTION", "message": f"Invalid action: {action}"}}
        
        elif command == 'flow':
            from commands.enhanced_flow import flow_project
            if action == 'project':
                result = flow_project(payload.get('project_name', ''))
            else:
                return {"status": "error", "error": {"code": "INVALID_ACTION", "message": f"Invalid action: {action}"}}
        
        elif command == 'execute':
            # Execute arbitrary code
            code = payload.get('code', '')
            namespace = {}
            
            import io
            from contextlib import redirect_stdout, redirect_stderr
            
            stdout_buffer = io.StringIO()
            stderr_buffer = io.StringIO()
            
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                exec(code, namespace)
            
            return {
                "status": "success",
                "data": {
                    "stdout": stdout_buffer.getvalue(),
                    "stderr": stderr_buffer.getvalue()
                }
            }
        
        else:
            return {
                "status": "error",
                "error": {
                    "code": "UNKNOWN_COMMAND",
                    "message": f"Unknown command: {command}"
                }
            }
        
        # Handle result
        if isinstance(result, dict):
            return {"status": "success", "data": result}
        elif isinstance(result, str):
            return {"status": "success", "data": {"message": result}}
        elif result is None:
            return {"status": "success", "data": {"success": True}}
        else:
            return {"status": "success", "data": {"result": str(result)}}
            
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": {
                "code": "EXECUTION_ERROR",
                "message": str(e),
                "details": {"traceback": traceback.format_exc()}
            }
        }


def main():
    """Main entry point"""
    try:
        # Read JSON from stdin
        input_data = sys.stdin.read()
        command_data = json.loads(input_data)
        
        # Execute command
        result = execute_command(command_data)
        
        # Return JSON result
        print(json.dumps(result))
        
    except json.JSONDecodeError as e:
        error = {
            "status": "error",
            "error": {
                "code": "INVALID_JSON",
                "message": f"Invalid JSON: {e}"
            }
        }
        print(json.dumps(error))
    except Exception as e:
        error = {
            "status": "error",
            "error": {
                "code": "SYSTEM_ERROR",
                "message": str(e)
            }
        }
        print(json.dumps(error))


if __name__ == "__main__":
    # Suppress print output from imported modules
    import builtins
    _original_print = builtins.print
    
    def silent_print(*args, **kwargs):
        # Only allow our own JSON output
        if args and isinstance(args[0], str) and args[0].startswith('{'):
            _original_print(*args, **kwargs)
    
    # Temporarily replace print during imports
    builtins.print = silent_print
    
    # Run main
    main()
