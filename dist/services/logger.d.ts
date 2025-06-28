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
export declare class SimpleLogger implements Logger {
    private context;
    constructor(context: string);
    debug(message: string, ...args: any[]): void;
    info(message: string, ...args: any[]): void;
    warn(message: string, ...args: any[]): void;
    error(message: string, ...args: any[]): void;
    private log;
}
export declare const logger: SimpleLogger;
/**
 * Create a logger instance for the given context
 */
export declare function createLogger(context: string): Logger;
declare const _default: {
    createLogger: typeof createLogger;
    SimpleLogger: typeof SimpleLogger;
};
export default _default;
//# sourceMappingURL=logger.d.ts.map