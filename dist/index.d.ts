/**
 * AI Coding Brain MCP Server v2.0.0
 * Integrated MCP server with 15 tools (1 implemented, 14 pending)
 */
/**
 * AI Coding Brain MCP 서버 클래스 (리팩토링 버전)
 */
declare class AICodingBrainMCP {
    private server;
    private projectPath;
    private backupHandler;
    constructor();
    /**
     * 도구 핸들러 설정
     */
    private setupToolHandlers;
    /**
     * 에러 핸들링 설정
     */
    private setupErrorHandling;
    /**
     * 서버 시작
     */
    start(): Promise<void>;
}
export { AICodingBrainMCP };
//# sourceMappingURL=index.d.ts.map