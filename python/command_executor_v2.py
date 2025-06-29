#!/usr/bin/env python3
"""
Simplified Command Executor - Direct command execution without complex serialization
Version 2.1 - Improved print handling
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
        
        # Special handling for execute command
        if command == 'execute':
            # Execute arbitrary code
            code = payload.get('code', '')
            namespace = {}
            
            import io
            from contextlib import redirect_stdout, redirect_stderr
            
            stdout_buffer = io.StringIO()
            stderr_buffer = io.StringIO()
            
            # Execute with output capture
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                exec(code, namespace)
            
            return {
                "status": "success",
                "data": {
                    "stdout": stdout_buffer.getvalue(),
                    "stderr": stderr_buffer.getvalue()
                }
            }
            
        # For other commands, we need to handle print suppression differently
        import builtins
        _original_print = builtins.print
        captured_output = []
        
        def capture_print(*args, **kwargs):
            # Capture the output
            output = io.StringIO()
            kwargs['file'] = output
            _original_print(*args, **kwargs)
            captured_output.append(output.getvalue())
        
        # Temporarily replace print
        builtins.print = capture_print
        
        try:
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
            
            else:
                return {
                    "status": "error",
                    "error": {
                        "code": "UNKNOWN_COMMAND",
                        "message": f"Unknown command: {command}"
                    }
                }
            
            # Handle result
            data = {}
            if isinstance(result, dict):
                data = result
            elif isinstance(result, str):
                data = {"message": result}
            elif result is None:
                data = {"success": True}
            else:
                data = {"result": str(result)}
            
            # Add captured output if any
            if captured_output:
                data["output"] = ''.join(captured_output)
                
            return {"status": "success", "data": data}
            
        finally:
            # Restore original print
            builtins.print = _original_print
            
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
    # Save original print for our use
    import builtins
    _final_print = builtins.print
    
    try:
        # Read JSON from stdin
        input_data = sys.stdin.read()
        command_data = json.loads(input_data)
        
        # Execute command
        result = execute_command(command_data)
        
        # Return JSON result using original print
        _final_print(json.dumps(result))
        
    except json.JSONDecodeError as e:
        error = {
            "status": "error",
            "error": {
                "code": "INVALID_JSON",
                "message": f"Invalid JSON: {e}"
            }
        }
        _final_print(json.dumps(error))
    except Exception as e:
        error = {
            "status": "error",
            "error": {
                "code": "SYSTEM_ERROR",
                "message": str(e)
            }
        }
        _final_print(json.dumps(error))


if __name__ == "__main__":
    main()
