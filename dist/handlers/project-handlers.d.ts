/**
 * Project Context Handlers
 */
/**
 * Build project context handler
 */
export declare function handleBuildProjectContext(args: {
    update_readme?: boolean;
    update_context?: boolean;
    include_stats?: boolean;
    include_file_directory?: boolean;
}): Promise<{
    content: Array<{
        type: string;
        text: string;
    }>;
}>;
//# sourceMappingURL=project-handlers.d.ts.map