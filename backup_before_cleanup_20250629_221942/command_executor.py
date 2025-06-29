#!/usr/bin/env python3
"""
Command Executor - Single entry point for TypeScript-Python communication
Replaces the old REPL-based approach with a clean JSON protocol
"""

import sys
import json
import traceback
from typing import Dict, Any

# Add project root to path
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.protocol_types import Request, Response


class CommandDispatcher:
    """Dispatches commands to appropriate handlers"""
    
    def __init__(self):
        # Initialize context for legacy code compatibility
        self._setup_legacy_context()
        
        # Command registry
        self.commands = {
            "plan": self.handle_plan,
            "task": self.handle_task,
            "flow": self.handle_flow,
            "next": self.handle_next,
            "execute": self.handle_execute  # For backward compatibility
        }
    
    def _setup_legacy_context(self):
        """Setup context for legacy code compatibility"""
        try:
            # Initialize UnifiedContextManager if needed
            from core.context_manager import UnifiedContextManager
            context_manager = UnifiedContextManager()
            context_manager.initialize_project("ai-coding-brain-mcp")
        except Exception:
            # Ignore if legacy context setup fails
            pass
    
    def dispatch(self, request: Request) -> Response:
        """Dispatch request to appropriate handler"""
        command = request.command.lower()
        
        if command not in self.commands:
            return Response.error(
                code="UNKNOWN_COMMAND",
                message=f"Unknown command: {command}",
                details={"available_commands": list(self.commands.keys())}
            )
        
        try:
            return self.commands[command](request)
        except Exception as e:
            return Response.error(
                code="COMMAND_ERROR",
                message=str(e),
                details={"traceback": traceback.format_exc()}
            )
    
    def handle_plan(self, request: Request) -> Response:
        """Handle plan commands"""
        action = request.action
        payload = request.payload
        
        try:
            from commands.plan import cmd_plan
            
            if action == "create":
                name = payload.get("name", "")
                description = payload.get("description", "")
                result = cmd_plan("create", name, description)
                return Response.success(result if isinstance(result, dict) else {"result": result})
            
            elif action == "show":
                result = cmd_plan("show")
                return Response.success(result if isinstance(result, dict) else {"result": result})
            
            else:
                return Response.error(
                    code="INVALID_ACTION",
                    message=f"Invalid action for plan: {action}"
                )
        except ImportError as e:
            return Response.error(
                code="IMPORT_ERROR",
                message=f"Failed to import plan command: {e}"
            )
    
    def handle_task(self, request: Request) -> Response:
        """Handle task commands"""
        action = request.action
        payload = request.payload
        
        try:
            from commands.task import cmd_task
            
            if action == "add":
                phase = payload.get("phase", "")
                title = payload.get("title", "")
                description = payload.get("description", "")
                result = cmd_task("add", phase, title, description)
                return Response.success({"task_id": result} if result else {"success": True})
            
            elif action == "list":
                result = cmd_task("list")
                return Response.success({"tasks": result} if result else {"tasks": []})
            
            elif action == "done":
                task_id = payload.get("task_id", "")
                result = cmd_task("done", task_id)
                return Response.success({"success": True})
            
            else:
                return Response.error(
                    code="INVALID_ACTION", 
                    message=f"Invalid action for task: {action}"
                )
        except ImportError as e:
            return Response.error(
                code="IMPORT_ERROR",
                message=f"Failed to import task command: {e}"
            )
    
    def handle_flow(self, request: Request) -> Response:
        """Handle flow commands"""
        action = request.action
        payload = request.payload
        
        try:
            from commands.enhanced_flow import flow_project
            
            if action == "project":
                project_name = payload.get("project_name", "")
                result = flow_project(project_name)
                return Response.success(result if isinstance(result, dict) else {"success": True})
            
            else:
                return Response.error(
                    code="INVALID_ACTION",
                    message=f"Invalid action for flow: {action}"
                )
        except ImportError as e:
            return Response.error(
                code="IMPORT_ERROR",
                message=f"Failed to import flow command: {e}"
            )
    
    def handle_next(self, request: Request) -> Response:
        """Handle next task command"""
        try:
            from commands.next import cmd_next
            result = cmd_next()
            return Response.success(result if isinstance(result, dict) else {"success": True})
        except ImportError as e:
            return Response.error(
                code="IMPORT_ERROR",
                message=f"Failed to import next command: {e}"
            )
    
    def handle_execute(self, request: Request) -> Response:
        """Handle execute command for backward compatibility"""
        code = request.payload.get("code", "")
        
        # Create isolated namespace
        namespace = {}
        
        # Capture stdout/stderr
        import io
        from contextlib import redirect_stdout, redirect_stderr
        
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        
        try:
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                exec(code, namespace)
            
            return Response.success({
                "stdout": stdout_buffer.getvalue(),
                "stderr": stderr_buffer.getvalue(),
                "namespace": {k: str(v) for k, v in namespace.items() 
                             if not k.startswith("__")}
            })
        except Exception as e:
            return Response.error(
                code="EXECUTION_ERROR",
                message=str(e),
                details={"traceback": traceback.format_exc()}
            )


def main():
    """Main entry point - reads JSON from stdin, returns JSON to stdout"""
    try:
        # Read input (single line JSON)
        input_data = sys.stdin.read()
        
        # Parse request
        request = Request.from_json(input_data)
        
        # Dispatch command
        dispatcher = CommandDispatcher()
        response = dispatcher.dispatch(request)
        
        # Return response
        print(response.to_json())
        
    except json.JSONDecodeError as e:
        error_response = Response.error(
            code="INVALID_JSON",
            message=f"Invalid JSON input: {e}",
            details={"input": input_data[:100] if 'input_data' in locals() else ""}
        )
        print(error_response.to_json())
    except Exception as e:
        error_response = Response.error(
            code="SYSTEM_ERROR",
            message=str(e),
            details={"traceback": traceback.format_exc()}
        )
        print(error_response.to_json())


if __name__ == "__main__":
    main()
