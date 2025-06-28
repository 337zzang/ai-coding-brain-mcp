interface ToolResponse {
    content: Array<{
        type: string;
        text: string;
    }>;
}
/**
 * 파일 분석 핸들러
 * ProjectAnalyzer를 사용하여 파일을 분석합니다.
 */
export declare function handleFileAnalyze(params: {
    file_path: string;
    update_manifest?: boolean;
}): Promise<ToolResponse>;
export {};
//# sourceMappingURL=file-analyzer-handler.d.ts.map