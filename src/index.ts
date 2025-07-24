#!/usr/bin/env node
/**
 * AI Coding Brain MCP Server v4.2.0 - Enhanced Edition
 * Python REPL with persistent helpers and improved tool definitions
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import { createLogger } from './services/logger';
import { defaultRepositoryFactory } from './core/infrastructure/index';
import { toolDefinitions } from './tools/tool-definitions';

// 핸들러 클래스들 import
import { ExecuteCodeHandler } from './handlers/execute-code-handler';

const logger = createLogger('main');

/**
 * AI Coding Brain MCP 서버
 * 영속적인 Python REPL 세션을 제공하는 간소화된 MCP 서버
 */
class AICodingBrainMCP {
  private server: Server;
  private projectPath: string;

  constructor() {
    this.projectPath = process.cwd();

    // 서버 초기화
    this.server = new Server(
      {
        name: 'ai-coding-brain-mcp',
        version: '4.2.0',
        description: 'AI Coding Brain MCP - Simplified Python REPL with persistent helpers'
      },
      {
        capabilities: {
          tools: {},
          resources: {}
        }
      }
    );

    this.setupToolHandlers();
    this.setupListToolsHandler();
  }

  private setupToolHandlers(): void {
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        logger.info(`Processing tool request: ${name}`);

        // execute_code와 restart_json_repl만 처리
        if (name === 'execute_code') {
          return await ExecuteCodeHandler.handleExecuteCode(args as { code: string; language?: string });
        } else if (name === 'restart_json_repl') {
          return await ExecuteCodeHandler.handleRestartJsonRepl(args as { reason?: string; keep_helpers?: boolean });
        } else {
          throw new McpError(
            ErrorCode.MethodNotFound,
            `Unknown tool: ${name}`
          );
        }
      } catch (error: any) {
        logger.error(`Tool execution error for ${name}:`, error);
        if (error instanceof McpError) {
          throw error;
        }
        throw new McpError(
          ErrorCode.InternalError,
          `Tool execution failed: ${error.message}`
        );
      }
    });
  }

  private setupListToolsHandler(): void {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      logger.info('Handling list_tools request');
      return {
        tools: toolDefinitions.map(tool => ({
          name: tool.name,
          description: tool.description,
          inputSchema: tool.inputSchema
        }))
      };
    });
  }

  /**
   * 서버 시작
   */
  async start(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);

    logger.info('AI Coding Brain MCP v4.2.0 - Enhanced Edition');
    logger.info('2 tools loaded: execute_code, restart_json_repl');
    logger.info('Python REPL session with persistent helpers ready');
  }
}

/**
 * 메인 함수
 */
async function main(): Promise<void> {
  try {
    const aiCodingBrain = new AICodingBrainMCP();
    await aiCodingBrain.start();
  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
}

// 시작
if (require.main === module) {
  main().catch((error) => {
    logger.error('Unhandled error:', error);
    process.exit(1);
  });
}
