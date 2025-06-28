/**
 * Gitignore 관련 핸들러
 */
/**
 * 프로젝트 분석하여 .gitignore 제안
 */
export declare function handleGitignoreAnalyze(): Promise<{
    content: Array<{
        type: string;
        text: string;
    }>;
}>;
/**
 * .gitignore 파일 업데이트
 */
export declare function handleGitignoreUpdate(args: {
    patterns: string[];
    category?: string;
}): Promise<{
    content: Array<{
        type: string;
        text: string;
    }>;
}>;
/**
 * 새로운 .gitignore 파일 생성
 */
export declare function handleGitignoreCreate(args: {
    categories?: string[];
}): Promise<{
    content: Array<{
        type: string;
        text: string;
    }>;
}>;
//# sourceMappingURL=gitignore-handlers.d.ts.map