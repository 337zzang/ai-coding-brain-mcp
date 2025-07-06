import { ToolResult } from '../types/tool-interfaces';
import { logger } from '../services/logger';
// import { getActiveReplSession } from './repl-session-manager'; // Not exported

interface FlowProjectResult {
    success: boolean;
    project_name?: string;
    path?: string;
    git_branch?: string;
    workflow_status?: any;
    error?: string;
    details?: any;
}

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
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(1)

    # 3. 프로젝트 전환 실행
    try:
        flow_result = cmd_flow_with_context(project_name)

        if flow_result and isinstance(flow_result, dict):
            result["success"] = True
            result["path"] = flow_result.get("project_path", os.getcwd())
            result["git_branch"] = flow_result.get("git_branch", "unknown")
            result["workflow_status"] = flow_result.get("workflow_status", {})
            result["details"] = flow_result
        else:
            result["error"] = f"예상치 못한 반환값: {type(flow_result)}"
            result["details"]["return_value"] = str(flow_result)

    except Exception as e:
        result["error"] = f"프로젝트 전환 중 오류: {str(e)}"
        result["details"]["traceback"] = traceback.format_exc()
        result["details"]["exception_type"] = type(e).__name__

    # 4. 결과 출력
    print(json.dumps(result, ensure_ascii=False, indent=2))

except Exception as e:
    # 최상위 예외 처리
    result["error"] = f"치명적 오류: {str(e)}"
    result["details"]["fatal_traceback"] = traceback.format_exc()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(1)
`;

    try {
        // ExecuteCodeHandler를 사용하여 Python 코드 실행
        const { ExecuteCodeHandler } = await import('./execute-code-handler');
        const toolResult = await ExecuteCodeHandler.handleExecuteCode({ code, language: 'python' });
        
        // ToolResult를 기존 형식으로 변환
        const execResult: any = {
            success: true,
            stdout: toolResult.content[0]?.text || '',
            stderr: '',
            error: null
        };
        
        // 에러 메시지가 있는지 확인
        if (toolResult.content[0]?.text?.includes('❌') || toolResult.content[0]?.text?.includes('오류')) {
            execResult.success = false;
            execResult.error = toolResult.content[0]?.text;
        }

        // 실행 결과 파싱
        if (!execResult.success) {
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
            // stdout에서 JSON 부분만 추출 (마지막 완전한 JSON 객체)
            const stdout = execResult.stdout || '';
            const jsonMatch = stdout.match(/\{[^{}]*"success"[\s\S]*\}(?!.*\{[^{}]*"success")/);

            if (jsonMatch) {
                result = JSON.parse(jsonMatch[0]);
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

        // 성공 응답
        const successMessage = `✅ 프로젝트 전환 성공: ${result.project_name}\n\n` +
            `📍 경로: ${result.path || 'Unknown'}\n` +
            `🌿 Git 브랜치: ${result.git_branch || 'Unknown'}\n`;

        const workflowInfo = result.workflow_status?.plan ?
            `\n📋 활성 워크플로우: ${result.workflow_status.plan.name}\n` +
            `   진행률: ${result.workflow_status.plan.progress || '0/0'}` :
            '\n⚠️ 활성 워크플로우 없음';

        return {
            content: [{
                type: 'text',
                text: successMessage + workflowInfo
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
