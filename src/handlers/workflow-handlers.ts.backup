/**
 * Workflow Handlers - WorkflowManager 기반
 */

import { ExecuteCodeHandler } from './execute-code-handler';

interface McpResponse {
  content: Array<{
    type: string;
    text: string;
  }>;
}

export async function handleFlowProject(args: any): Promise<McpResponse> {
  const code = `
from commands.enhanced_flow import flow_project as cmd_flow
result = cmd_flow("${args.project_name}")

# Convert result to JSON string for proper MCP response
import json
print(json.dumps(result))
`;
  
  const execResult = await ExecuteCodeHandler.handleExecuteCode({ code });
  
  // Parse the result from stdout if it's a JSON string
  let resultData;
  try {
    if (execResult?.content?.[0]?.text) {
      const text = execResult.content[0].text;
      const parsedResult = JSON.parse(text);
      
      // Extract stdout and try to parse it as JSON
      if (parsedResult.stdout) {
        const stdoutLines = parsedResult.stdout.split('\n');
        for (let i = stdoutLines.length - 1; i >= 0; i--) {
          const line = stdoutLines[i].trim();
          if (line && line.startsWith('{')) {
            try {
              resultData = JSON.parse(line);
              break;
            } catch (e) {
              // Continue to previous line
            }
          }
        }
      }
    }
  } catch (e) {
    // If parsing fails, return the raw output
  }
  
  if (resultData) {
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(resultData, null, 2)
        }
      ]
    };
  }
  
  return execResult || { content: [{ type: 'text', text: 'No result' }] };
}

export async function handlePlanProject(args: any): Promise<McpResponse> {
  const code = `
from commands.plan import cmd_plan

# 계획 관리
plan_name = "${args.plan_name || ''}"
description = "${args.description || ''}"

if plan_name:
    # 계획 생성
    result = cmd_plan("create", plan_name, description)
else:
    # 계획 표시
    result = cmd_plan("show")

# Convert result to JSON string for proper MCP response
import json
print(json.dumps(result) if result else '{"success": true}')
`;
  
  const execResult = await ExecuteCodeHandler.handleExecuteCode({ code });
  
  // Parse the result from stdout if it's a JSON string
  let resultData;
  try {
    if (execResult?.content?.[0]?.text) {
      const text = execResult.content[0].text;
      const parsedResult = JSON.parse(text);
      
      // Extract stdout and try to parse it as JSON
      if (parsedResult.stdout) {
        const stdoutLines = parsedResult.stdout.split('\n');
        for (let i = stdoutLines.length - 1; i >= 0; i--) {
          const line = stdoutLines[i].trim();
          if (line && line.startsWith('{')) {
            try {
              resultData = JSON.parse(line);
              break;
            } catch (e) {
              // Continue to previous line
            }
          }
        }
      }
    }
  } catch (e) {
    // If parsing fails, return the raw output
  }
  
  if (resultData) {
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(resultData, null, 2)
        }
      ]
    };
  }
  
  return execResult || { content: [{ type: 'text', text: 'No result' }] };
}

export async function handleTaskManage(args: any): Promise<McpResponse> {
  const code = `
from commands.task import cmd_task

# 작업 관리
action = "${args.action || 'list'}"
args_list = ${JSON.stringify(args.args || [])}
result = cmd_task(action, args_list)

# Convert result to JSON string for proper MCP response
import json
print(json.dumps(result) if result else '{"success": true}')
`;
  
  const execResult = await ExecuteCodeHandler.handleExecuteCode({ code });
  
  // Parse the result from stdout if it's a JSON string
  let resultData;
  try {
    if (execResult?.content?.[0]?.text) {
      const text = execResult.content[0].text;
      const parsedResult = JSON.parse(text);
      
      // Extract stdout and try to parse it as JSON
      if (parsedResult.stdout) {
        const stdoutLines = parsedResult.stdout.split('\n');
        for (let i = stdoutLines.length - 1; i >= 0; i--) {
          const line = stdoutLines[i].trim();
          if (line && line.startsWith('{')) {
            try {
              resultData = JSON.parse(line);
              break;
            } catch (e) {
              // Continue to previous line
            }
          }
        }
      }
    }
  } catch (e) {
    // If parsing fails, return the raw output
  }
  
  if (resultData) {
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(resultData, null, 2)
        }
      ]
    };
  }
  
  return execResult || { content: [{ type: 'text', text: 'No result' }] };
}

export async function handleNextTask(args: any): Promise<McpResponse> {
  const code = `
from commands.next import cmd_next

# 다음 작업으로 진행
content = ${args.content ? `"${args.content.replace(/"/g, '\\"')}"` : 'None'}
result = cmd_next(content)

# Convert result to JSON string for proper MCP response
import json
print(json.dumps(result) if result else '{"success": true}')
`;
  
  const execResult = await ExecuteCodeHandler.handleExecuteCode({ code });
  
  // Parse the result from stdout if it's a JSON string
  let resultData;
  try {
    if (execResult?.content?.[0]?.text) {
      const text = execResult.content[0].text;
      const parsedResult = JSON.parse(text);
      
      // Extract stdout and try to parse it as JSON
      if (parsedResult.stdout) {
        const stdoutLines = parsedResult.stdout.split('\n');
        for (let i = stdoutLines.length - 1; i >= 0; i--) {
          const line = stdoutLines[i].trim();
          if (line && line.startsWith('{')) {
            try {
              resultData = JSON.parse(line);
              break;
            } catch (e) {
              // Continue to previous line
            }
          }
        }
      }
    }
  } catch (e) {
    // If parsing fails, return the raw output
  }
  
  if (resultData) {
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(resultData, null, 2)
        }
      ]
    };
  }
  
  return execResult || { content: [{ type: 'text', text: 'No result' }] };
}
