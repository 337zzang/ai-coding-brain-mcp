/**
 * AI Coding Brain MCP Server v2.0.0
 * Integrated MCP server with 15 tools (1 implemented, 14 pending)
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { 
  CallToolRequestSchema, 
  ErrorCode, 
  ListToolsRequestSchema, 
  McpError 
} from '@modelcontextprotocol/sdk/types.js';

import { createLogger } from './services/logger';
import { defaultRepositoryFactory } from './core/infrastructure/index';
import { toolDefinitions } from './tools/tool-definitions';

// 핸들러 클래스들 import
import { ExecuteCodeHandler } from './handlers/execute-code-handler';
import { handleFlowProject, handlePlanProject, handleTaskManage, handleNextTask } from './handlers/workflow-handlers.js';
import { handleWisdomStats, handleTrackMistake, handleAddBestPractice } from './handlers/wisdom-handlers';
import { BackupHandler } from './handlers/backup-handler';
import { handleFileAnalyze } from './handlers/file-analyzer-handler';
import { handleGitStatus, handleGitCommitSmart, handleGitBranchSmart, handleGitRollbackSmart, handleGitPush } from './handlers/git-handlers';
import { handleGitignoreAnalyze, handleGitignoreUpdate, handleGitignoreCreate } from './handlers/gitignore-handlers';

import { generateAiImage, listAiImages, searchAiImages } from './handlers/image-generator-handler';
// 로거 초기화
const logger = createLogger('ai-coding-brain-mcp');

/**
 * AI Coding Brain MCP 서버 클래스 (리팩토링 버전)
 */
class AICodingBrainMCP {
  private server: Server;
  private projectPath: string;
  private backupHandler: BackupHandler;

  constructor() {
    this.projectPath = process.cwd();
    this.backupHandler = new BackupHandler(this.projectPath);
    
    this.server = new Server(
      {
        name: 'ai-coding-brain-mcp',
        version: '2.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
    this.setupErrorHandling();
  }

  /**
   * 도구 핸들러 설정
   */
  private setupToolHandlers(): void {
    // 도구 목록 제공
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: toolDefinitions,
      };
    });

    // 도구 실행 핸들러 (간소화된 라우팅)
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        // 도구별 처리
        if (name === 'execute_code') {
          return await ExecuteCodeHandler.handleExecuteCode(args as { code: string; language?: string });
        } else if (name === 'restart_json_repl') {
          return await ExecuteCodeHandler.handleRestartJsonRepl(args as { reason?: string; keep_helpers?: boolean });
        } else if (name === 'backup_file') {
          const { filepath, reason } = args as { filepath: string; reason?: string };
          const backupPath = await this.backupHandler.createBackup(filepath, reason);
          return {
            content: [
              {
                type: 'text',
                text: `Backup created: ${backupPath}`
              }
            ]
          };
        } else if (name === 'restore_backup') {
          const { backup_path } = args as { backup_path: string };
          const restoredPath = await this.backupHandler.restoreBackup(backup_path);
          return {
            content: [
              {
                type: 'text',
                text: `File restored to: ${restoredPath}`
              }
            ]
          };
        } else if (name === 'list_backups') {
          const { filename } = args as { filename?: string };
          const backups = await this.backupHandler.listBackups(filename);
          return {
            content: [
              {
                type: 'text',
                text: JSON.stringify(backups, null, 2)
              }
            ]
          };
        } else if (name === 'flow_project') {
          return await handleFlowProject(args as { project_name: string });
        } else if (name === 'plan_project') {
          return await handlePlanProject(args as { plan_name?: string; description?: string });
        } else if (name === 'task_manage') {
          return await handleTaskManage(args as { action: string; args?: string[] });
        } else if (name === 'next_task') {
          return await handleNextTask(args as {});
        } else if (name === 'file_analyze') {
          return await handleFileAnalyze(args as { file_path: string; update_manifest?: boolean });
        } else if (name === 'wisdom_stats') {
          return await handleWisdomStats(args as {});
        } else if (name === 'track_mistake') {
          return await handleTrackMistake(args as { mistake_type: string; context?: string });
        } else if (name === 'add_best_practice') {
          return await handleAddBestPractice(args as { practice: string; category?: string });
        } else if (name === 'git_status') {
          return await handleGitStatus(args);
        } else if (name === 'git_commit_smart') {
          return await handleGitCommitSmart(args as { message?: string; auto_add?: boolean });
        } else if (name === 'git_branch_smart') {
          return await handleGitBranchSmart(args as { branch_name?: string; base_branch?: string });
        } else if (name === 'git_rollback_smart') {
          return await handleGitRollbackSmart(args as { target?: string; safe_mode?: boolean });
        } else if (name === 'git_push') {
          return await handleGitPush(args as { remote?: string; branch?: string });
        } else if (name === 'gitignore_analyze') {
          return await handleGitignoreAnalyze();
        } else if (name === 'gitignore_update') {
          return await handleGitignoreUpdate(args as { patterns: string[]; category?: string });
        } else if (name === 'gitignore_create') {
          return await handleGitignoreCreate(args as { categories?: string[] } else if (name === 'generate_ai_image') {
          return await generateAiImage(args);
        } else if (name === 'list_ai_images') {
          return await listAiImages();
        } else if (name === 'search_ai_images') {
          return await searchAiImages(args);
        });
        }

        // TODO: Implement remaining tools
        throw new McpError(
          ErrorCode.MethodNotFound,
          `Tool '${name}' not implemented yet.`
        );
      } catch (error) {
        logger.error(`Tool execution error [${name}]:`, error);
        
        if (error instanceof McpError) {
          throw error;
        }
        
        throw new McpError(
          ErrorCode.InternalError,
          `Tool execution failed: ${error instanceof Error ? error.message : String(error)}`
        );
      }
    });
  }

  /**
   * 에러 핸들링 설정
   */
  private setupErrorHandling(): void {
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
  public async start(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    
    // Repository 헬스 체크 (로깅 최소화)
    const healthCheck = await defaultRepositoryFactory.healthCheck();
    if (healthCheck.status === 'unhealthy') {
      logger.error(`Repository health check failed: ${healthCheck.rootDir}`);
    }
    
    logger.info('AI Coding Brain MCP server v2.0.0 started successfully');
    logger.info('13 tools loaded: execute_code, restart_json_repl, backup_file, restore_backup, list_backups, flow_project, plan_project, task_manage, next_task, file_analyze, generate_ai_image, list_ai_images, search_ai_images');
  }
}

/**
 * 메인 실행 함수
 */
async function main(): Promise<void> {
  try {
    const mcpServer = new AICodingBrainMCP();
    await mcpServer.start();
  } catch (error) {
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

export { AICodingBrainMCP };
