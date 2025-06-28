/**
 * Wisdom System Handlers
 */
/**
 * Wisdom stats handler - 통계 정보
 */
export declare function handleWisdomStats(): Promise<{
    content: Array<{
        type: string;
        text: string;
    }>;
}>;
/**
 * Track mistake handler
 */
export declare function handleTrackMistake(args: {
    mistake_type: string;
    context?: string;
}): Promise<{
    content: Array<{
        type: string;
        text: string;
    }>;
}>;
/**
 * Add best practice handler
 */
export declare function handleAddBestPractice(args: {
    practice: string;
    category?: string;
}): Promise<{
    content: Array<{
        type: string;
        text: string;
    }>;
}>;
/**
 * Wisdom analyze handler - 코드 분석
 */
export declare function handleWisdomAnalyze(args: {
    code: string;
    filename?: string;
    auto_fix?: boolean;
}): Promise<{
    content: Array<{
        type: string;
        text: string;
    }>;
}>;
/**
 * Wisdom analyze file handler
 */
export declare function handleWisdomAnalyzeFile(args: {
    filepath: string;
}): Promise<{
    content: Array<{
        type: string;
        text: string;
    }>;
}>;
/**
 * Wisdom report handler
 */
export declare function handleWisdomReport(args: {
    output_file?: string;
}): Promise<{
    content: Array<{
        type: string;
        text: string;
    }>;
}>;
//# sourceMappingURL=wisdom-handlers.d.ts.map