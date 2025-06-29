import { getCommandExecutor } from '../services/command-executor';

interface ExecuteResult {
  success: boolean;
  stdout?: string;
  stderr?: string;
  error?: string;
  executionTime?: number;
  variableCount?: number;
}

export class ExecuteCodeHandler {
  /**
   * Execute code using the unified CommandExecutor
   */
  static async handleExecuteCode(args: { code: string; language?: string }): Promise<ExecuteResult> {
    const executor = getCommandExecutor();
    const startTime = Date.now();
    
    try {
      const response = await executor.executeCode(args.code);
      const executionTime = Date.now() - startTime;
      
      if (response.status === 'success' && response.data) {
        return {
          success: true,
          stdout: response.data.stdout || '',
          stderr: response.data.stderr || '',
          executionTime,
          variableCount: 0 // Unified executor doesn't track variables
        };
      } else {
        return {
          success: false,
          error: response.error?.message || 'Unknown error',
          stderr: response.error?.details?.stderr || '',
          executionTime
        };
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        executionTime: Date.now() - startTime
      };
    }
  }
}
