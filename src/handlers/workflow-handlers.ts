/**
 * Workflow Handlers - WorkflowManager 기반
 */

export function handleFlowProject(args: any): string {
  const code = `
from commands.enhanced_flow import flow_project as cmd_flow
cmd_flow("${args.project_name}")
`;
  return code;
}

export function handlePlanProject(args: any): string {
  const code = `
from commands.plan import cmd_plan

# 계획 관리
plan_name = "${args.plan_name || ''}"
description = "${args.description || ''}"

if plan_name:
    # 계획 생성
    cmd_plan("create", plan_name, description)
else:
    # 계획 표시
    cmd_plan("show")
`;
  return code;
}

export function handleTaskManage(args: any): string {
  const code = `
from commands.task import cmd_task

# 작업 관리
action = "${args.action || 'list'}"
args_list = ${JSON.stringify(args.args || [])}
cmd_task(action, args_list)
`;
  return code;
}

export function handleNextTask(args: any): string {
  const code = `
from commands.next import cmd_next

# 다음 작업으로 진행
content = ${args.content ? `"${args.content.replace(/"/g, '\\"')}"` : 'None'}
cmd_next(content)
`;
  return code;
}
