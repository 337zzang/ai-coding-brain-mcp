"use strict";
/**
 * AI Coding Brain MCP Server v2.0.0
 * Integrated MCP server with 15 tools (1 implemented, 14 pending)
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.AICodingBrainMCP = void 0;
const index_js_1 = require("@modelcontextprotocol/sdk/server/index.js");
const stdio_js_1 = require("@modelcontextprotocol/sdk/server/stdio.js");
const types_js_1 = require("@modelcontextprotocol/sdk/types.js");
const logger_1 = require("./services/logger");
const index_1 = require("./core/infrastructure/index");
const tool_definitions_1 = require("./tools/tool-definitions");
// 핸들러 클래스들 import
const execute_code_handler_1 = require("./handlers/execute-code-handler");
const workflow_handlers_1 = require("./handlers/workflow-handlers");
const wisdom_handlers_1 = require("./handlers/wisdom-handlers");
const backup_handler_1 = require("./handlers/backup-handler");
const file_analyzer_handler_1 = require("./handlers/file-analyzer-handler");
const git_handlers_1 = require("./handlers/git-handlers");
const gitignore_handlers_1 = require("./handlers/gitignore-handlers");
const project_handlers_1 = require("./handlers/project-handlers");
const api_toggle_handler_1 = require("./handlers/api-toggle-handler");
// 로거 초기화
const logger = (0, logger_1.createLogger)('ai-coding-brain-mcp');
/**
 * AI Coding Brain MCP 서버 클래스 (리팩토링 버전)
 */
class AICodingBrainMCP {
    constructor() {
        this.projectPath = process.cwd();
        this.backupHandler = new backup_handler_1.BackupHandler(this.projectPath);
        this.server = new index_js_1.Server({
            name: 'ai-coding-brain-mcp',
            version: '2.0.0',
        }, {
            capabilities: {
                tools: {},
            },
        });
        this.setupToolHandlers();
        this.setupErrorHandling();
    }
    /**
     * 도구 핸들러 설정
     */
    setupToolHandlers() {
        // 도구 목록 제공
        this.server.setRequestHandler(types_js_1.ListToolsRequestSchema, async () => {
            return {
                tools: tool_definitions_1.toolDefinitions,
            };
        });
        // 도구 실행 핸들러 (간소화된 라우팅)
        this.server.setRequestHandler(types_js_1.CallToolRequestSchema, async (request) => {
            const { name, arguments: args } = request.params;
            try {
                // 도구별 처리
                if (name === 'execute_code') {
                    return await execute_code_handler_1.ExecuteCodeHandler.handleExecuteCode(args);
                }
                else if (name === 'restart_json_repl') {
                    return await execute_code_handler_1.ExecuteCodeHandler.handleRestartJsonRepl(args);
                }
                else if (name === 'backup_file') {
                    const { filepath, reason } = args;
                    const backupPath = await this.backupHandler.createBackup(filepath, reason);
                    return {
                        content: [
                            {
                                type: 'text',
                                text: `Backup created: ${backupPath}`
                            }
                        ]
                    };
                }
                else if (name === 'restore_backup') {
                    const { backup_path } = args;
                    const restoredPath = await this.backupHandler.restoreBackup(backup_path);
                    return {
                        content: [
                            {
                                type: 'text',
                                text: `File restored to: ${restoredPath}`
                            }
                        ]
                    };
                }
                else if (name === 'list_backups') {
                    const { filename } = args;
                    const backups = await this.backupHandler.listBackups(filename);
                    return {
                        content: [
                            {
                                type: 'text',
                                text: JSON.stringify(backups, null, 2)
                            }
                        ]
                    };
                }
                else if (name === 'flow_project') {
                    return await (0, workflow_handlers_1.handleFlowProject)(args);
                }
                else if (name === 'plan_project') {
                    return await (0, workflow_handlers_1.handlePlanProject)(args);
                }
                else if (name === 'task_manage') {
                    return await (0, workflow_handlers_1.handleTaskManage)(args);
                }
                else if (name === 'next_task') {
                    return await (0, workflow_handlers_1.handleNextTask)(args);
                }
                else if (name === 'file_analyze') {
                    return await (0, file_analyzer_handler_1.handleFileAnalyze)(args);
                }
                else if (name === 'wisdom_stats') {
                    return await (0, wisdom_handlers_1.handleWisdomStats)();
                }
                else if (name === 'track_mistake') {
                    return await (0, wisdom_handlers_1.handleTrackMistake)(args);
                }
                else if (name === 'add_best_practice') {
                    return await (0, wisdom_handlers_1.handleAddBestPractice)(args);
                }
                else if (name === 'git_status') {
                    return await (0, git_handlers_1.handleGitStatus)(args);
                }
                else if (name === 'git_commit_smart') {
                    return await (0, git_handlers_1.handleGitCommitSmart)(args);
                }
                else if (name === 'git_branch_smart') {
                    return await (0, git_handlers_1.handleGitBranchSmart)(args);
                }
                else if (name === 'git_rollback_smart') {
                    return await (0, git_handlers_1.handleGitRollbackSmart)(args);
                }
                else if (name === 'git_push') {
                    return await (0, git_handlers_1.handleGitPush)(args);
                }
                else if (name === 'gitignore_analyze') {
                    return await (0, gitignore_handlers_1.handleGitignoreAnalyze)();
                }
                else if (name === 'gitignore_update') {
                    return await (0, gitignore_handlers_1.handleGitignoreUpdate)(args);
                }
                else if (name === 'gitignore_create') {
                    return await (0, gitignore_handlers_1.handleGitignoreCreate)(args);
                }
                else if (name === 'toggle_api') {
                    return await api_toggle_handler_1.apiToggleHandler.execute(args);
                }
                else if (name === 'list_apis') {
                    return await api_toggle_handler_1.listApisHandler.execute(args);
                }
                else if (name === 'build_project_context') {
                    return await (0, project_handlers_1.handleBuildProjectContext)(args);
                }
                else if (name === 'wisdom_analyze') {
                    return await (0, wisdom_handlers_1.handleWisdomAnalyze)(args);
                }
                else if (name === 'wisdom_analyze_file') {
                    return await (0, wisdom_handlers_1.handleWisdomAnalyzeFile)(args);
                }
                else if (name === 'wisdom_report') {
                    return await (0, wisdom_handlers_1.handleWisdomReport)(args);
                }
                else {
                    // TODO: Implement remaining tools
                    throw new types_js_1.McpError(types_js_1.ErrorCode.MethodNotFound, `Tool \'${name}\' not implemented yet.`);
                }
            }
            catch (error) {
                if (error instanceof types_js_1.McpError) {
                    throw error;
                }
                throw new types_js_1.McpError(types_js_1.ErrorCode.InternalError, `Tool execution failed: ${error instanceof Error ? error.message : String(error)}`);
            }
        });
    }
    /**
     * 에러 핸들링 설정
     */
    setupErrorHandling() {
        this.server.onerror = (error) => {
            logger.error('MCP Server error:', error);
        };
        process.on('SIGINT', async () => {
            logger.info('Shutting down AI Coding Brain MCP server...');
            await this.server.close();
            process.exit(0);
        });
    }
    /**
     * 서버 시작
     */
    async start() {
        const transport = new stdio_js_1.StdioServerTransport();
        await this.server.connect(transport);
        // Repository 헬스 체크 (로깅 최소화)
        const healthCheck = await index_1.defaultRepositoryFactory.healthCheck();
        if (healthCheck.status === 'unhealthy') {
            logger.error(`Repository health check failed: ${healthCheck.rootDir}`);
        }
        logger.info('AI Coding Brain MCP server v2.0.0 started successfully');
        logger.info('12 tools loaded: execute_code, restart_json_repl, backup_file, restore_backup, list_backups, flow_project, plan_project, task_manage, next_task, file_analyze, toggle_api, list_apis');
    }
}
exports.AICodingBrainMCP = AICodingBrainMCP;
/**
 * 메인 실행 함수
 */
async function main() {
    try {
        const mcpServer = new AICodingBrainMCP();
        await mcpServer.start();
    }
    catch (error) {
        logger.error('Failed to start MCP server:', error);
        process.exit(1);
    }
}
// 서버 시작
if (require.main === module) {
    main().catch((error) => {
        console.error('Fatal error:', error);
        process.exit(1);
    });
}
//# sourceMappingURL=index.js.map