"use strict";
/**
 * Workflow Handlers - WorkflowManager 기반
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.handleFlowProject = handleFlowProject;
exports.handlePlanProject = handlePlanProject;
exports.handleTaskManage = handleTaskManage;
exports.handleNextTask = handleNextTask;
function handleFlowProject(args) {
    const code = `
from commands.enhanced_flow import flow_project as cmd_flow
cmd_flow("${args.project_name}")
`;
    return code;
}
function handlePlanProject(args) {
    const code = `
from commands.plan import cmd_plan

# 계획 관리
if "${args.plan_name || ''}":
    # 계획 생성
    cmd_plan("create", "${args.plan_name || ''}", "${args.description || ''}")
else:
    # 계획 표시
    cmd_plan("show")
`;
    return code;
}
function handleTaskManage(args) {
    const code = `
from commands.task import cmd_task

# 작업 관리
action = "${args.action || 'list'}"
args_list = ${JSON.stringify(args.args || [])}
cmd_task(action, args_list)
`;
    return code;
}
function handleNextTask(args) {
    const code = `
from commands.next import cmd_next

# 다음 작업으로 진행
content = ${args.content ? `"${args.content.replace(/"/g, '\\"')}"` : 'None'}
cmd_next(content)
`;
    return code;
}
//# sourceMappingURL=workflow-handlers.js.map