/**
 * Git Handlers - AI Coding Brain MCP
 * Git 관련 MCP 도구 핸들러
 */
/**
 * Git 상태 확인
 */
export declare function handleGitStatus(_args: any): Promise<{
    content: Array<{
        type: string;
        text: string;
    }>;
}>;
/**
 * Git 스마트 커밋
 */
export declare function handleGitCommitSmart(args: {
    message?: string;
    auto_add?: boolean;
}): Promise<{
    content: Array<{
        type: string;
        text: string;
    }>;
}>;
/**
 * Git 스마트 브랜치
 */
export declare function handleGitBranchSmart(args: {
    branch_name?: string;
    base_branch?: string;
}): Promise<{
    content: Array<{
        type: string;
        text: string;
    }>;
}>;
/**
 * Git 스마트 롤백
 */
export declare function handleGitRollbackSmart(args: {
    target?: string;
    safe_mode?: boolean;
}): Promise<{
    content: Array<{
        type: string;
        text: string;
    }>;
}>;
/**
 * Git 푸시
 */
export declare function handleGitPush(args: {
    remote?: string;
    branch?: string;
}): Promise<{
    content: Array<{
        type: string;
        text: string;
    }>;
}>;
//# sourceMappingURL=git-handlers.d.ts.map