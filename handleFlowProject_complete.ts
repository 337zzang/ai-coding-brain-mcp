export async function handleFlowProject(params: { project_name: string }): Promise<ToolResult> {
    const code = `
# 개선된 flow_project 핸들러 - 명시적 에러 처리
import sys
import os
import json
import traceback
from pathlib import Path

project_name = "${params.project_name}"
result = {
    "success": False,
    "project_name": project_name,
    "error": None,
    "details": {}
}

# 로그 출력을 억제하기 위한 설정
import logging
logging.getLogger().setLevel(logging.CRITICAL)

# stdout 캡처를 위한 설정
from io import StringIO
captured_output = StringIO()

try:
    # 1. Python 경로 설정
    current_dir = Path.cwd()
    python_dir = current_dir / 'python'
    if python_dir.exists() and str(python_dir) not in sys.path:
        sys.path.insert(0, str(python_dir))

    # 2. enhanced_flow import
    try:
        from enhanced_flow import cmd_flow_with_context
    except ImportError as e:
        result["error"] = f"enhanced_flow 모듈 import 실패: {str(e)}"
        result["details"]["import_error"] = traceback.format_exc()
        print(f"JSON_RESULT_START{json.dumps(result, ensure_ascii=False)}JSON_RESULT_END")
        sys.exit(1)

    # 3. stdout 리다이렉트
    original_stdout = sys.stdout
    sys.stdout = captured_output
    
    try:
        # 4. 프로젝트 전환 실행
        flow_result = cmd_flow_with_context(project_name)

        if flow_result and isinstance(flow_result, dict):
            result["success"] = True
            result["path"] = flow_result.get("context", {}).get("project_path", os.getcwd())
            result["git_branch"] = flow_result.get("context", {}).get("git", {}).get("branch", "unknown")
            result["workflow_status"] = flow_result.get("workflow_status", {})
            result["details"] = flow_result
        else:
            result["error"] = f"예상치 못한 반환값: {type(flow_result)}"
            result["details"]["return_value"] = str(flow_result)

    except Exception as e:
        result["error"] = f"프로젝트 전환 중 오류: {str(e)}"
        result["details"]["traceback"] = traceback.format_exc()
        result["details"]["exception_type"] = type(e).__name__
    finally:
        # stdout 복원
        sys.stdout = original_stdout
        captured_logs = captured_output.getvalue()
        result["details"]["logs"] = captured_logs

    # 5. 결과 출력 (JSON만 출력)
    print(f"JSON_RESULT_START{json.dumps(result, ensure_ascii=False)}JSON_RESULT_END")

except Exception as e:
    # 최상위 예외 처리
    result["error"] = f"치명적 오류: {str(e)}"
    result["details"]["fatal_traceback"] = traceback.format_exc()
    print(f"JSON_RESULT_START{json.dumps(result, ensure_ascii=False)}JSON_RESULT_END")
    sys.exit(1)
`;

    try {
        // ExecuteCodeHandler를 사용하여 Python 코드 실행
        const { ExecuteCodeHandler } = await import('./execute-code-handler');
        const toolResult = await ExecuteCodeHandler.handleExecuteCode({ code, language: 'python' });
        
        // ToolResult에서 실제 결과 추출
        let execResult: any;
        try {
            // toolResult.content[0].text는 JSON 문자열
            const resultText = toolResult.content[0]?.text || '';
            execResult = JSON.parse(resultText);
        } catch (e) {
            logger.error('Failed to parse ExecuteCodeHandler result:', e);
            return {
                content: [{
                    type: 'text',
                    text: `❌ 결과 형식 오류\n\n${toolResult.content[0]?.text || ''}`
                }]
            };
        }
        
        // 에러 확인
        if (!execResult.success || execResult.error) {
            logger.error('Python execution failed:', execResult.error);
            return {
                content: [{
                    type: 'text',
                    text: `❌ Python 실행 실패\n\n에러: ${execResult.error || 'Unknown error'}\n\n${execResult.stderr || ''}`
                }]
            };
        }

        // stdout에서 JSON 결과 추출
        let result: FlowProjectResult;
        try {
            // stdout에서 JSON_RESULT_START와 JSON_RESULT_END 마커로 감싸진 JSON 추출
            const stdout = execResult.stdout || '';
            const jsonMatch = stdout.match(/JSON_RESULT_START(.+?)JSON_RESULT_END/s);

            if (jsonMatch && jsonMatch[1]) {
                result = JSON.parse(jsonMatch[1]);
            } else {
                throw new Error('No valid JSON found in output');
            }
        } catch (parseError) {
            logger.error('Failed to parse result:', parseError);
            return {
                content: [{
                    type: 'text',
                    text: `❌ 결과 파싱 실패\n\n출력:\n${execResult.stdout}\n\n에러:\n${execResult.stderr}`
                }]
            };
        }

        // 결과 처리
        if (!result.success) {
            logger.error('Flow project failed:', result.error);
            return {
                content: [{
                    type: 'text',
                    text: `❌ 프로젝트 전환 실패: ${params.project_name}\n\n에러: ${result.error}\n\n${result.details?.traceback ? '\n스택 트레이스:\n' + result.details.traceback : ''}`
                }]
            };
        }

        // 성공 응답 - 실제 데이터를 포함하여 반환
        const successMessage = `✅ 프로젝트 전환 성공: ${result.project_name}`;
        
        // 전체 결과 데이터 구성
        const responseData = {
            success: true,
            project_name: result.project_name,
            path: result.path || 'Unknown',
            git_branch: result.git_branch || 'Unknown',
            context: result.details?.context || {},
            workflow_status: result.workflow_status || {},
            message: successMessage
        };

        // Python의 flat 구조를 처리하도록 수정
        const workflowInfo = result.workflow_status?.status === 'active' ?
            `\n📋 활성 워크플로우: ${result.workflow_status.plan_name || 'Unknown'}\n` +
            `   진행률: ${result.workflow_status.completed_tasks || 0}/${result.workflow_status.total_tasks || 0}` :
            '\n⚠️ 활성 워크플로우 없음';

        return {
            content: [{
                type: 'text',
                text: successMessage + '\n\n' + 
                      `📍 경로: ${responseData.path}\n` +
                      `🌿 Git 브랜치: ${responseData.git_branch}` +
                      workflowInfo
            }, {
                type: 'text',
                text: '```json\n' + JSON.stringify(responseData, null, 2) + '\n```'
            }]
        };

    } catch (error) {
        logger.error('handleFlowProject error:', error);
        return {
            content: [{
                type: 'text',
                text: `❌ 핸들러 오류\n\n${error instanceof Error ? error.message : String(error)}`
            }]
        };
    }
}

// 기타 워크플로우 관련 핸들러들...
