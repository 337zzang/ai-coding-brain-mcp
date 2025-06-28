"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.handleFlowProject = handleFlowProject;
exports.handlePlanProject = handlePlanProject;
exports.handleTaskManage = handleTaskManage;
exports.handleNextTask = handleNextTask;
const execute_code_handler_1 = require("./execute-code-handler");
// 글로벌 변수 저장소 키
/**
 * 변수 저장 코드 생성
 */
function generateSaveVars() {
    return `
# 사용자 정의 변수 저장
_user_vars = {}
for k, v in list(globals().items()):
    if not k.startswith('_') and k not in ['helpers', 'context', 'os', 'sys', 'json', 'datetime']:
        try:
            # JSON 직렬화 가능한 것만 저장
            import json
            json.dumps(v)
            _user_vars[k] = v
        except:
            pass
            
if _user_vars:
    helpers.update_cache('__mcp_shared_vars__', _user_vars)
    print(f"💾 {len(_user_vars)}개 변수 저장됨")
`;
}
/**
 * 변수 복원 코드 생성
 */
function generateLoadVars() {
    return `
# 이전 변수 복원
_saved_vars = helpers.get_value('__mcp_shared_vars__', {})
if _saved_vars:
    for k, v in _saved_vars.items():
        globals()[k] = v
    print(f"♻️ {len(_saved_vars)}개 변수 복원됨")
`;
}
/**
 * 개선된 프로젝트 전환 핸들러 (변수 유지)
 */
async function handleFlowProject(params) {
    const code = `
${generateLoadVars()}

# 프로젝트 전환 (cmd_flow_with_context 사용)
project_name = "${params.project_name}"
result = helpers.cmd_flow_with_context(project_name)

# 결과 처리
if result.get('success'):
    context = result.get('context')
    print(f"✅ 프로젝트 '{project_name}'로 전환되었습니다.")
else:
    print(f"❌ 프로젝트 전환 실패: {result.get('error', '알 수 없는 오류')}")

${generateSaveVars()}
`;
    return execute_code_handler_1.ExecuteCodeHandler.handleExecuteCode({ code, language: 'python' });
}
/**
 * 개선된 계획 수립 핸들러 (변수 유지)
 */
async function handlePlanProject(params) {
    const code = params.reset
        ? `
${generateLoadVars()}

# 계획 수립 또는 리셋
result = helpers.cmd_plan(reset=True)
print(result)

${generateSaveVars()}
`
        : `
${generateLoadVars()}

# 계획 수립
result = helpers.cmd_plan(${params.plan_name ? `"${params.plan_name}"` : 'None'}, ${params.description ? `"${params.description}"` : 'None'})
print(result)

${generateSaveVars()}
`;
    return execute_code_handler_1.ExecuteCodeHandler.handleExecuteCode({ code, language: 'python' });
}
/**
 * 개선된 작업 관리 핸들러 (변수 유지)
 */
async function handleTaskManage(params) {
    const argsStr = params.args ? params.args.map(arg => `"${arg}"`).join(', ') : '';
    const code = `
${generateLoadVars()}

# 작업 관리
helpers.cmd_task("${params.action}"${argsStr ? ', ' + argsStr : ''})

${generateSaveVars()}
`;
    return execute_code_handler_1.ExecuteCodeHandler.handleExecuteCode({ code, language: 'python' });
}
/**
 * 개선된 다음 작업 핸들러 (변수 유지)
 */
async function handleNextTask(_params) {
    const code = `
${generateLoadVars()}

# 다음 작업 진행
helpers.cmd_next()

${generateSaveVars()}
`;
    return execute_code_handler_1.ExecuteCodeHandler.handleExecuteCode({ code, language: 'python' });
}
//# sourceMappingURL=workflow-handlers.js.map