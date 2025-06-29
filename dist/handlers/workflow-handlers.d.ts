/**
 * Workflow Handlers - WorkflowManager 기반
 */
interface McpResponse {
    content: Array<{
        type: string;
        text: string;
    }>;
}
export declare function handleFlowProject(args: any): Promise<McpResponse>;
export declare function handlePlanProject(args: any): Promise<McpResponse>;
export declare function handleTaskManage(args: any): Promise<McpResponse>;
export declare function handleNextTask(args: any): Promise<McpResponse>;
export {};
//# sourceMappingURL=workflow-handlers.d.ts.map