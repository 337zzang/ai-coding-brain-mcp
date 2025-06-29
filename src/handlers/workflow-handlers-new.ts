import { ExecuteCodeHandler } from './execute-code-handler';

interface CommandRequest {
  command: string;
  action: string;
  payload: Record<string, any>;
}

interface CommandResponse {
  status: 'success' | 'error';
  data?: Record<string, any>;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
}

/**
 * Execute a command through the new JSON protocol
 */
async function executeCommand(request: CommandRequest): Promise<CommandResponse> {
  const code = `
import json
import subprocess
import sys

# Command request
request = ${JSON.stringify(JSON.stringify(request))}

# Execute through command_executor
process = subprocess.Popen(
    [sys.executable, 'python/command_executor.py'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding='utf-8'
)

stdout, stderr = process.communicate(input=request)

if stderr:
    print(json.dumps({
        "status": "error",
        "error": {
            "code": "EXECUTION_ERROR",
            "message": stderr
        }
    }))
else:
    print(stdout)
`;

  const result = await ExecuteCodeHandler.handleExecuteCode({ code });
  
  if (result.success && result.stdout) {
    try {
      return JSON.parse(result.stdout);
    } catch (e) {
      return {
        status: 'error',
        error: {
          code: 'PARSE_ERROR',
          message: 'Failed to parse command response',
          details: { stdout: result.stdout, stderr: result.stderr }
        }
      };
    }
  }
  
  return {
    status: 'error',
    error: {
      code: 'HANDLER_ERROR',
      message: result.error || 'Unknown error',
      details: result
    }
  };
}

/**
 * Handle flow project command
 */
export async function handleFlowProject(args: { project_name: string }) {
  const response = await executeCommand({
    command: 'flow',
    action: 'project',
    payload: { project_name: args.project_name }
  });
  
  return {
    success: response.status === 'success',
    ...response.data,
    error: response.error?.message
  };
}

/**
 * Handle plan project command
 */
export async function handlePlanProject(args: { plan_name?: string; description?: string; reset?: boolean }) {
  const action = args.plan_name ? 'create' : 'show';
  
  const response = await executeCommand({
    command: 'plan',
    action,
    payload: {
      name: args.plan_name || '',
      description: args.description || '',
      reset: args.reset || false
    }
  });
  
  return {
    success: response.status === 'success',
    ...response.data,
    error: response.error?.message
  };
}

/**
 * Handle task management command
 */
export async function handleTaskManage(args: { action: string; args?: string[] }) {
  let payload: Record<string, any> = {};
  
  switch (args.action) {
    case 'add':
      if (args.args && args.args.length >= 3) {
        payload = {
          phase: args.args[0],
          title: args.args[1],
          description: args.args[2]
        };
      }
      break;
    case 'done':
    case 'remove':
      if (args.args && args.args.length >= 1) {
        payload = { task_id: args.args[0] };
      }
      break;
  }
  
  const response = await executeCommand({
    command: 'task',
    action: args.action,
    payload
  });
  
  return {
    success: response.status === 'success',
    ...response.data,
    error: response.error?.message
  };
}

/**
 * Handle next task command
 */
export async function handleNextTask() {
  const response = await executeCommand({
    command: 'next',
    action: 'execute',
    payload: {}
  });
  
  return {
    success: response.status === 'success',
    ...response.data,
    error: response.error?.message
  };
}

/**
 * Handle wisdom stats command
 */
export async function handleWisdomStats() {
  // For now, use the old execute method since wisdom is not migrated yet
  const code = `
from commands.wisdom import cmd_wisdom_stats
result = cmd_wisdom_stats()
print(result if isinstance(result, str) else "")
`;
  
  const execResult = await ExecuteCodeHandler.handleExecuteCode({ code });
  
  return {
    success: execResult.success,
    output: execResult.stdout || '',
    error: execResult.error
  };
}

/**
 * Handle other wisdom commands (not migrated yet)
 */
export async function handleTrackMistake(args: { mistake_type: string; context?: string }) {
  const code = `
from project_wisdom import get_wisdom_manager
wisdom = get_wisdom_manager()
wisdom.track_mistake("${args.mistake_type}", "${args.context || ''}")
print("Mistake tracked successfully")
`;
  
  const execResult = await ExecuteCodeHandler.handleExecuteCode({ code });
  
  return {
    success: execResult.success,
    output: execResult.stdout || '',
    error: execResult.error
  };
}

export async function handleAddBestPractice(args: { practice: string; category?: string }) {
  const code = `
from project_wisdom import get_wisdom_manager
wisdom = get_wisdom_manager()
wisdom.add_best_practice("${args.practice}", "${args.category || 'general'}")
print("Best practice added successfully")
`;
  
  const execResult = await ExecuteCodeHandler.handleExecuteCode({ code });
  
  return {
    success: execResult.success,
    output: execResult.stdout || '',
    error: execResult.error
  };
}
