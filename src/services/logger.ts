/**
 * Simple Logger Service for AI Coding Brain MCP
 * 
 * Provides basic logging functionality with different levels
 */

export interface Logger {
  debug(message: string, ...args: any[]): void;
  info(message: string, ...args: any[]): void;
  warn(message: string, ...args: any[]): void;
  error(message: string, ...args: any[]): void;
}

export class SimpleLogger implements Logger {
  constructor(private context: string) {}

  debug(message: string, ...args: any[]): void {
    this.log('DEBUG', message, ...args);
  }

  info(message: string, ...args: any[]): void {
    this.log('INFO', message, ...args);
  }

  warn(message: string, ...args: any[]): void {
    this.log('WARN', message, ...args);
  }

  error(message: string, ...args: any[]): void {
    this.log('ERROR', message, ...args);
  }

  private log(level: string, message: string, ...args: any[]): void {
    const timestamp = new Date().toISOString();
    const contextInfo = this.context ? `[${this.context}]` : '';
    
    // Format: 2025-06-02T05:35:50.743Z [ai-coding-brain-mcp] [info] Message...
    console.error(`${timestamp} ${contextInfo} [${level.toLowerCase()}] ${message}`, ...args);
  }
}

// Default logger instance
export const logger = new SimpleLogger('default');


/**
 * Create a logger instance for the given context
 */
export function createLogger(context: string): Logger {
  return new SimpleLogger(context);
}

export default { createLogger, SimpleLogger };
