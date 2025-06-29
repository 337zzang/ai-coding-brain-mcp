#!/usr/bin/env python3
"""
Simplified Command Executor - Version 3.0
Stable version with better error handling
"""

import sys
import json
import os
import io
from contextlib import redirect_stdout, redirect_stderr

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def execute_command(command_data):
    """Execute command and return result"""
    try:
        command = command_data.get('command', '').lower()
        action = command_data.get('action', '')
        payload = command_data.get('payload', {})
        
        # Capture all output
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        
        result = None
        
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            if command == 'execute':
                # Execute arbitrary code
                code = payload.get('code', '')
                namespace = {
                    'sys': sys,
                    'os': os,
                    'json': json,
                    '__builtins__': __builtins__
                }
                exec(code, namespace)
                result = {"executed": True}
                
            elif command == 'plan':
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
            
            else:
                return {
                    "status": "error",
                    "error": {
                        "code": "UNKNOWN_COMMAND",
                        "message": f"Unknown command: {command}"
                    }
                }
        
        # Get captured output
        stdout_str = stdout_buffer.getvalue()
        stderr_str = stderr_buffer.getvalue()
        
        # Build response
        data = {}
        if command == 'execute':
            data['stdout'] = stdout_str
            data['stderr'] = stderr_str
        else:
            # For other commands, include result
            if isinstance(result, dict):
                data = result
            elif result is not None:
                data['result'] = str(result)
            else:
                data['success'] = True
            
            # Add output if any
            if stdout_str:
                data['output'] = stdout_str
                
        return {"status": "success", "data": data}
            
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
    main()
