import { getCommandExecutor } from '../services/command-executor';
import type { CommandRequest, CommandResponse } from '../services/command-executor';

const executor = getCommandExecutor();

/**
 * Handle flow project command
 */
export async function handleFlowProject(args: { project_name: string }) {
  const response = await executor.execute({
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
  
  const response = await executor.execute({
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
  
  const response = await executor.execute({
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
  const response = await executor.execute({
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
  // Use legacy execute for now
  const response = await executor.executeCode(`
from commands.wisdom import cmd_wisdom_stats
result = cmd_wisdom_stats()
print(result if isinstance(result, str) else "")
`);
  
  if (response.status === 'success' && response.data) {
    return {
      success: true,
      output: response.data.stdout || '',
      error: undefined
    };
  }
  
  return {
    success: false,
    output: '',
    error: response.error?.message || 'Unknown error'
  };
}

/**
 * Handle track mistake command
 */
export async function handleTrackMistake(args: { mistake_type: string; context?: string }) {
  const response = await executor.executeCode(`
from project_wisdom import get_wisdom_manager
wisdom = get_wisdom_manager()
wisdom.track_mistake("${args.mistake_type}", "${args.context || ''}")
print("Mistake tracked successfully")
`);
  
  if (response.status === 'success' && response.data) {
    return {
      success: true,
      output: response.data.stdout || '',
      error: undefined
    };
  }
  
  return {
    success: false,
    output: '',
    error: response.error?.message || 'Unknown error'
  };
}

/**
 * Handle add best practice command
 */
export async function handleAddBestPractice(args: { practice: string; category?: string }) {
  const response = await executor.executeCode(`
from project_wisdom import get_wisdom_manager
wisdom = get_wisdom_manager()
wisdom.add_best_practice("${args.practice}", "${args.category || 'general'}")
print("Best practice added successfully")
`);
  
  if (response.status === 'success' && response.data) {
    return {
      success: true,
      output: response.data.stdout || '',
      error: undefined
    };
  }
  
  return {
    success: false,
    output: '',
    error: response.error?.message || 'Unknown error'
  };
}

// Add other handlers as needed...
