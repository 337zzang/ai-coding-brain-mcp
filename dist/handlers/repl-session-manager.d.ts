interface REPLResponse {
    id: string;
    success: boolean;
    stdout?: string;
    stderr?: string;
    error?: string;
    traceback?: string;
    needs_more?: boolean;
    variable_count?: number;
    variables?: any;
    total_count?: number;
    status?: string;
}
export declare class REPLSessionManager {
    private static pythonProcess;
    private static sessionId;
    private static responseBuffer;
    private static writeLock;
    private static responseHandler;
    private static pendingResponses;
    /**
     * 🔗 JSON 프레이밍 기반 Python 세션 초기화
     */
    /**
     * REPL 세션 활성 상태 확인
     */
    static isSessionActive(): boolean;
    /**
     * REPL 세션 상태 정보 반환
     */
    static getSessionStatus(): any;
    static initializeSession(): Promise<void>;
    /**
     * 📨 JSON 응답 리스너
     */
    private static setupResponseListener;
    /**
     * 🔒 안전한 코드 실행 (Lock + JSON)
     */
    static executeCode(code: string, timeoutMs?: number): Promise<REPLResponse>;
    /**
     * 📊 변수 스냅샷 조회
     */
    static getVariableSnapshot(): Promise<REPLResponse>;
    /**
     * 🏥 헬스체크
     */
    static healthCheck(): Promise<boolean>;
    /**
     * ⏳ 응답 대기
     */
    private static waitForResponse;
    /**
     * 🔒 Write Lock 관리
     */
    private static acquireWriteLock;
    private static releaseWriteLock;
    /**
     * 🔄 세션 재시작
     */
    static resetSession(): Promise<void>;
    /**
     * 📊 세션 상태 정보
     */
    /**
     * REPL 세션 정리 및 재시작 준비
     */
    static cleanup(): Promise<void>;
}
export {};
//# sourceMappingURL=repl-session-manager.d.ts.map