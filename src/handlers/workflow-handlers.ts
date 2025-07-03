import { ExecuteCodeHandler } from './execute-code-handler';

// ========== 세션 공유 MCP 도구 핸들러 ==========

interface ToolResponse {
    content: Array<{
        type: string;
        text: string;
    }>;
}

// 글로벌 변수 저장소 키
/**
 * 변수 저장 코드 생성
 * @deprecated 현재 사용하지 않음
 */
/*
function _generateSaveVars(): string {
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
*/

/**
 * 변수 복원 코드 생성
 * @deprecated 현재 사용하지 않음
 */
/*
function _generateLoadVars(): string {
    return `
# 이전 변수 복원
_saved_vars = helpers.get_value('__mcp_shared_vars__', {})
if _saved_vars:
    for k, v in _saved_vars.items():
        globals()[k] = v
    print(f"♻️ {len(_saved_vars)}개 변수 복원됨")
`;
}
*/

/**
 * 개선된 프로젝트 전환 핸들러 (변수 유지)
 */
export async function handleFlowProject(params: { project_name: string }): Promise<ToolResponse> {
    const code = `
# helpers 초기화
import sys
import os

# 프로젝트 경로 설정
project_root = r"C:\\Users\\Administrator\\Desktop\\ai-coding-brain-mcp"
if os.path.exists(project_root):
    os.chdir(project_root)
    sys.path.insert(0, os.path.join(project_root, 'python'))

# helpers 임포트 및 초기화
try:
    # HelpersWrapper 직접 임포트
    from helpers_wrapper import HelpersWrapper
    helpers = HelpersWrapper()
    print("✅ helpers 초기화 성공")
except ImportError:
    # 대체 방법: enhanced_flow 직접 사용
    try:
        from enhanced_flow import cmd_flow_with_context
        print("✅ enhanced_flow 직접 임포트 성공")
        
        # 프로젝트 전환
        project_name = "${params.project_name}"
        result = cmd_flow_with_context(project_name)
        
        if result and isinstance(result, dict):
            print(f"✅ 프로젝트 '{project_name}'로 전환 완료")
            print(f"   경로: {result.get('path', 'N/A')}")
    except Exception as e:
        print(f"❌ 프로젝트 전환 실패: {e}")
        import traceback
        traceback.print_exc()
else:
    # helpers를 통한 프로젝트 전환
    project_name = "${params.project_name}"
    try:
        if hasattr(helpers, 'cmd_flow_with_context'):
            result = helpers.cmd_flow_with_context(project_name)
            
            if result and isinstance(result, dict):
                print(f"✅ 프로젝트 '{project_name}'로 전환되었습니다.")
                project_path = result.get('path', result.get('project_root', 'N/A'))
                print(f"   프로젝트 경로: {project_path}")
            elif result is None:
                print(f"✅ 프로젝트 전환 완료 (상세 정보 없음)")
            else:
                print(f"⚠️ 예상치 못한 반환 타입: {type(result)}")
        else:
            print("❌ cmd_flow_with_context 메서드가 없습니다")
    except Exception as e:
        print(f"❌ 프로젝트 전환 중 예외 발생: {e}")
        import traceback
        traceback.print_exc()
`;
    return ExecuteCodeHandler.handleExecuteCode({ code, language: 'python' });
}

// Removed: handlePlanProject, handleTaskManage, handleNextTask
// These functions are no longer needed as the MCP tools have been removed
