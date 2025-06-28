"use strict";
/**
 * 간단한 로거 모듈
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.logger = void 0;
exports.createLogger = createLogger;
function createLogger(name) {
    return {
        info: (message, ...args) => console.log(`[${name}] INFO: ${message}`, ...args),
        error: (message, ...args) => console.error(`[${name}] ERROR: ${message}`, ...args),
        warn: (message, ...args) => console.warn(`[${name}] WARN: ${message}`, ...args),
        debug: (message, ...args) => console.log(`[${name}] DEBUG: ${message}`, ...args),
    };
}
// 기본 logger 인스턴스 export
exports.logger = createLogger('ai-coding-brain-mcp');
//# sourceMappingURL=logger.js.map