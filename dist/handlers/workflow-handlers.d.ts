interface ToolResponse {
    content: Array<{
        type: string;
        text: string;
    }>;
}
/**
 * 개선된 프로젝트 전환 핸들러 (변수 유지)
 */
export declare function handleFlowProject(params: {
    project_name: string;
}): Promise<ToolResponse>;
/**
 * 개선된 계획 수립 핸들러 (변수 유지)
 */
export declare function handlePlanProject(params: {
    plan_name?: string;
    description?: string;
    reset?: boolean;
}): Promise<ToolResponse>;
export {};
//# sourceMappingURL=workflow-handlers.d.ts.map