"use strict";
/**
 * Simple Logger Service for AI Coding Brain MCP
 *
 * Provides basic logging functionality with different levels
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.logger = exports.SimpleLogger = void 0;
exports.createLogger = createLogger;
class SimpleLogger {
    constructor(context) {
        this.context = context;
    }
    debug(message, ...args) {
        this.log('DEBUG', message, ...args);
    }
    info(message, ...args) {
        this.log('INFO', message, ...args);
    }
    warn(message, ...args) {
        this.log('WARN', message, ...args);
    }
    error(message, ...args) {
        this.log('ERROR', message, ...args);
    }
    log(level, message, ...args) {
        const timestamp = new Date().toISOString();
        const contextInfo = this.context ? `[${this.context}]` : '';
        // Format: 2025-06-02T05:35:50.743Z [ai-coding-brain-mcp] [info] Message...
        console.error(`${timestamp} ${contextInfo} [${level.toLowerCase()}] ${message}`, ...args);
    }
}
exports.SimpleLogger = SimpleLogger;
// Default logger instance
exports.logger = new SimpleLogger('default');
/**
 * Create a logger instance for the given context
 */
function createLogger(context) {
    return new SimpleLogger(context);
}
exports.default = { createLogger, SimpleLogger };
//# sourceMappingURL=logger.js.map