import { spawn } from 'child_process';
import * as path from 'path';

export interface CommandRequest {
  command: string;
  action: string;
  payload: Record<string, any>;
}

export interface CommandResponse {
  status: 'success' | 'error';
  data?: Record<string, any>;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
}

export class CommandExecutor {
  private pythonPath: string;
  private executorPath: string;

  constructor() {
    this.pythonPath = process.platform === 'win32' ? 'python' : 'python3';
    // Use unified command_executor.py
    this.executorPath = path.join(process.cwd(), 'python', 'command_executor.py');
  }

  /**
   * Execute a command through the unified JSON protocol
   */
  async execute(request: CommandRequest): Promise<CommandResponse> {
    return new Promise((resolve) => {
      const child = spawn(this.pythonPath, [this.executorPath], {
        stdio: ['pipe', 'pipe', 'pipe'],
        env: { ...process.env, PYTHONUNBUFFERED: '1' }
      });

      let stdout = '';
      let stderr = '';

      child.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      child.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      child.on('error', (error) => {
        resolve({
          status: 'error',
          error: {
            code: 'SPAWN_ERROR',
            message: `Failed to spawn Python process: ${error.message}`,
            details: { error: error.toString() }
          }
        });
      });

      child.on('close', (code) => {
        if (code !== 0) {
          resolve({
            status: 'error',
            error: {
              code: 'PROCESS_ERROR',
              message: `Process exited with code ${code}`,
              details: { stdout, stderr, exitCode: code }
            }
          });
          return;
        }

        try {
          const response = JSON.parse(stdout.trim());
          resolve(response);
        } catch (e) {
          resolve({
            status: 'error',
            error: {
              code: 'PARSE_ERROR',
              message: 'Failed to parse response',
              details: { stdout, stderr, parseError: e?.toString() }
            }
          });
        }
      });

      // Send request
      child.stdin.write(JSON.stringify(request));
      child.stdin.end();
    });
  }

  /**
   * Execute legacy code (backward compatibility)
   */
  async executeCode(code: string): Promise<CommandResponse> {
    return this.execute({
      command: 'execute',
      action: 'code',
      payload: { code }
    });
  }
}

// Singleton instance
let commandExecutor: CommandExecutor | null = null;

export function getCommandExecutor(): CommandExecutor {
  if (!commandExecutor) {
    commandExecutor = new CommandExecutor();
  }
  return commandExecutor;
}
