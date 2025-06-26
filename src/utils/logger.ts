/**
 * 간단한 로거 모듈
 */

export function createLogger(name: string) {
  return {
    info: (message: string) => console.log(`[${name}] INFO: ${message}`),
    error: (message: string) => console.error(`[${name}] ERROR: ${message}`),
    warn: (message: string) => console.warn(`[${name}] WARN: ${message}`),
    debug: (message: string) => console.log(`[${name}] DEBUG: ${message}`),
  };
}
