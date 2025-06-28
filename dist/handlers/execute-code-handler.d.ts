/**
 * Execute Code 핸들러 - JSON REPL 세션 강제 활성화
 * json_repl_session.py를 무조건 사용하여 변수 지속성 보장
 */
export declare class ExecuteCodeHandler {
    private static replProcess;
    private static replReady;
    private static sessionVariables;
    private static lastActivity;
    private static requestCounter;
    /**
     * 📊 세션 정보 반환
     */
    private static getSessionInfo;
    /**
     * 🚀 JSON REPL 세션 초기화 (json_repl_session.py 직접 실행)
     */
    private static initializeJsonReplSession;
    /**
     * 🎯 JSON REPL 세션으로 코드 실행
     */
    private static executeWithJsonRepl;
    /**
     * 🎛️ 세션 명령어 처리
     */
    private static handleSessionCommand;
    /**
     * stdout에서 불필요한 메시지 필터링
     */
    private static cleanExecutionOutput;
    /**
     * Node.js 실행 파일 찾기
     */
    private static findNodeExecutable;
    /**
     * npm/npx 실행 파일 찾기
     */
    private static findNpmExecutable;
    /**
     * TypeScript 런타임 찾기
     */
    private static findTypeScriptRuntime;
    /**
     * 🎯 메인 execute_code 핸들러
     */
    static handleExecuteCode(args: {
        code: string;
        language?: string;
    }): Promise<{
        content: Array<{
            type: string;
            text: string;
        }>;
    }>;
    /**
     * 🔄 JSON REPL 세션 재시작
     */
    static handleRestartJsonRepl(args: {
        reason?: string;
        keep_helpers?: boolean;
    }): Promise<{
        content: Array<{
            type: string;
            text: string;
        }>;
    }>;
}
//# sourceMappingURL=execute-code-handler.d.ts.map