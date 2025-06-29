import { spawn, ChildProcess } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
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
  private static instance: ExecuteCodeHandler;
  private replProcess: ChildProcess | null = null;
  private replReady: boolean = false;
  private useNewExecutor: boolean = false; // Feature flag

  private constructor() {}

  static getInstance(): ExecuteCodeHandler {
    if (!ExecuteCodeHandler.instance) {
      ExecuteCodeHandler.instance = new ExecuteCodeHandler();
    }
    return ExecuteCodeHandler.instance;
  }

  /**
   * Execute code using either new CommandExecutor or legacy REPL
   */
  static async handleExecuteCode(args: { code: string; language?: string }): Promise<ExecuteResult> {
    const handler = ExecuteCodeHandler.getInstance();
    
    // Check if we should use new executor for specific patterns
    if (handler.shouldUseNewExecutor(args.code)) {
      return handler.executeWithNewExecutor(args.code);
    }
    
    // Otherwise use legacy REPL
    return handler.executeWithREPL(args);
  }

  /**
   * Determine if code should use new executor
   */
  private shouldUseNewExecutor(code: string): boolean {
    // Never use new executor for direct command imports
    if (code.includes('from commands.') || code.includes('import commands.')) {
      return false;
    }
    
    // Use new executor if feature flag is enabled
    return this.useNewExecutor;
  }

  /**
   * Execute code using new CommandExecutor
   */
  private async executeWithNewExecutor(code: string): Promise<ExecuteResult> {
    const executor = getCommandExecutor();
    const startTime = Date.now();
    
    try {
      const response = await executor.executeCode(code);
      const executionTime = Date.now() - startTime;
      
      if (response.status === 'success' && response.data) {
        return {
          success: true,
          stdout: response.data.stdout || '',
          stderr: response.data.stderr || '',
          executionTime,
          variableCount: 0 // New executor doesn't track variables
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

  /**
   * Execute code using legacy REPL (existing implementation)
   */
  private async executeWithREPL(args: { code: string; language?: string }): Promise<ExecuteResult> {
    const handler = ExecuteCodeHandler.getInstance();
    
    if (!handler.replReady) {
      await handler.initializeREPL();
    }
    
    return handler.executeCode(args.code, args.language);
  }

  // ... (rest of the existing REPL implementation remains unchanged)
  
  private async initializeREPL(): Promise<void> {
    return new Promise((resolve, reject) => {
      const pythonScript = path.join(process.cwd(), 'python', 'json_repl_session.py');
      
      if (!fs.existsSync(pythonScript)) {
        reject(new Error(`Python script not found: ${pythonScript}`));
        return;
      }

      this.replProcess = spawn('python', [pythonScript], {
        stdio: ['pipe', 'pipe', 'pipe'],
        env: { ...process.env, PYTHONUNBUFFERED: '1' }
      });

      this.replProcess.stdout?.once('data', (data) => {
        if (data.toString().includes('__READY__')) {
          this.replReady = true;
          resolve();
        }
      });

      this.replProcess.on('error', (error) => {
        reject(new Error(`Failed to start REPL: ${error.message}`));
      });

      setTimeout(() => {
        if (!this.replReady) {
          reject(new Error('REPL initialization timeout'));
        }
      }, 10000);
    });
  }

  private async executeCode(code: string, language: string = 'python'): Promise<ExecuteResult> {
    if (!this.replProcess || !this.replReady) {
      return {
        success: false,
        error: 'REPL not initialized'
      };
    }

    return new Promise((resolve) => {
      const request = {
        id: Date.now().toString(),
        code,
        language
      };

      let responseData = '';
      
      const handleResponse = (data: Buffer) => {
        responseData += data.toString();
        
        try {
          const response = JSON.parse(responseData);
          if (response.id === request.id) {
            this.replProcess?.stdout?.removeListener('data', handleResponse);
            resolve({
              success: response.success ?? true,
              stdout: response.stdout || '',
              stderr: response.stderr || '',
              error: response.error,
              executionTime: response.execution_time,
              variableCount: response.variable_count
            });
          }
        } catch (e) {
          // Not complete JSON yet, continue accumulating
        }
      };

      this.replProcess.stdout?.on('data', handleResponse);
      this.replProcess.stdin?.write(JSON.stringify(request) + '\n');
    });
  }

  /**
   * Enable or disable new executor
   */
  static setUseNewExecutor(enabled: boolean): void {
    ExecuteCodeHandler.getInstance().useNewExecutor = enabled;
  }
}
