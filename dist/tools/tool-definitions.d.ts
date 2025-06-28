/**
 * AI Coding Brain MCP - Tool Definitions v8.0
 * 핵심 워크플로우 유지, 중복만 제거
 *
 * 작성일: 2025-06-16
 */
interface ToolDefinition {
    name: string;
    description: string;
    inputSchema: {
        type: string;
        properties: Record<string, any>;
        required?: string[];
    };
}
export declare const toolDefinitions: ToolDefinition[];
export {};
//# sourceMappingURL=tool-definitions.d.ts.map