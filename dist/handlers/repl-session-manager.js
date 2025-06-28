"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.REPLSessionManager = void 0;
// repl-session-manager.ts - JSON 프레이밍 기반 REPL 세션
const child_process_1 = require("child_process");
const path = __importStar(require("path"));
const logger_1 = require("../services/logger");
const logger = (0, logger_1.createLogger)('repl-session-manager');
class REPLSessionManager {
    /**
     * 🔗 JSON 프레이밍 기반 Python 세션 초기화
     */
    /**
     * REPL 세션 활성 상태 확인
     */
    static isSessionActive() {
        return !!(this.pythonProcess && !this.pythonProcess.killed && this.sessionId);
    }
    /**
     * REPL 세션 상태 정보 반환
     */
    static getSessionStatus() {
        return {
            active: this.isSessionActive(),
            pid: this.pythonProcess?.pid || null,
            session_id: this.sessionId || null,
            uptime: this.sessionId ? Date.now() - parseInt(this.sessionId.split('_')[1] || '0') : 0
        };
    }
    static async initializeSession() {
        if (this.pythonProcess && !this.pythonProcess.killed) {
            logger.info('REPL 세션이 이미 활성화되어 있습니다');
            return;
        }
        logger.info('🐍 JSON 프레이밍 Python REPL 세션 시작...');
        try {
            // Python 경로 확인 (환경변수 우선, 폴백)
            const pythonPath = process.env['PYTHON_PATH'] ||
                (process.platform === 'win32' ? 'C:\\Users\\Administrator\\miniconda3\\python.exe' : 'python');
            // AI Coding Brain MCP 프로젝트 경로
            const projectPath = process.env['PROJECT_ROOT'] || process.cwd();
            const pythonScriptPath = path.join(projectPath, process.env['PYTHON_SCRIPT_PATH'] || 'python/json_repl_session.py');
            // 초기화 정보 로깅
            logger.info(`📂 프로젝트 경로: ${projectPath}`);
            logger.info(`🐍 Python 실행 파일: ${pythonPath}`);
            logger.info(`📜 Python 스크립트: ${pythonScriptPath}`);
            this.pythonProcess = (0, child_process_1.spawn)(pythonPath, ['-u', pythonScriptPath], {
                stdio: ['pipe', 'pipe', 'pipe'],
                env: {
                    ...process.env,
                    PYTHONUNBUFFERED: '1',
                    PYTHONIOENCODING: 'utf-8' // UTF-8 인코딩 강제
                },
                cwd: projectPath // AI Coding Brain MCP 프로젝트 디렉터리로 설정
            });
            this.sessionId = `session_${Date.now()}`;
            logger.info(`✅ Python 프로세스 시작됨 (PID: ${this.pythonProcess.pid})`);
            logger.info(`🔑 세션 ID: ${this.sessionId}`);
            // 응답 리스너 설정
            this.setupResponseListener();
            // 프로세스 종료 리스너
            this.pythonProcess.on('exit', (code, signal) => {
                logger.warn(`Python REPL 프로세스 종료 (코드: ${code}, 시그널: ${signal})`);
                this.pythonProcess = null;
                this.sessionId = null;
            });
            this.pythonProcess.on('error', (error) => {
                logger.error('Python REPL 프로세스 시작 실패:', error);
                throw new Error(`Python 프로세스 시작 실패: ${error.message}`);
            });
            // 초기화 대기 (stderr과 stdout 모두 확인)
            await new Promise((resolve, reject) => {
                const timeout = setTimeout(() => {
                    const errorMsg = `REPL 초기화 타임아웃 (30초). Python 경로: ${pythonPath}`;
                    logger.error(errorMsg);
                    reject(new Error(errorMsg));
                }, 60000); // 60초로 증가 (복잡한 환경 대응)
                let initialized = false;
                // stderr 메시지 확인
                this.pythonProcess.stderr.on('data', (data) => {
                    const message = data.toString();
                    logger.info(`REPL stderr: ${message.trim()}`);
                    if ((message.includes('[Python] JSON 프레이밍 Python REPL 시작') ||
                        message.includes('[Python] 초기화 완료 - 세션 준비됨')) && !initialized) {
                        initialized = true;
                        clearTimeout(timeout);
                        logger.info('🎉 REPL 초기화 성공! 세션이 준비되었습니다.');
                        resolve();
                    }
                    // 오류 메시지 확인
                    if (message.includes('Error') || message.includes('Exception')) {
                        clearTimeout(timeout);
                        reject(new Error(`Python REPL 시작 오류: ${message.trim()}`));
                    }
                });
                // stdout 메시지도 확인 (혹시 모를 경우)
                this.pythonProcess.stdout.on('data', (data) => {
                    const message = data.toString();
                    logger.info(`REPL stdout: ${message.trim()}`);
                    if ((message.includes('[Python] JSON 프레이밍 Python REPL 시작') ||
                        message.includes('[Python] 초기화 완료 - 세션 준비됨')) && !initialized) {
                        initialized = true;
                        clearTimeout(timeout);
                        logger.info('🎉 REPL 초기화 성공! 세션이 준비되었습니다.');
                        resolve();
                    }
                });
                // 프로세스 종료 시 즉시 오류 처리
                this.pythonProcess.on('exit', (code) => {
                    if (!initialized) {
                        clearTimeout(timeout);
                        reject(new Error(`Python 프로세스가 예기치 않게 종료됨 (종료 코드: ${code})`));
                    }
                });
            });
            logger.info(`✅ REPL 세션 초기화 완료 (ID: ${this.sessionId})`);
        }
        catch (error) {
            logger.error('REPL 세션 초기화 실패:', error);
            throw error;
        }
    }
    /**
     * 📨 JSON 응답 리스너
     */
    static setupResponseListener() {
        if (!this.pythonProcess || !this.pythonProcess.stdout) {
            throw new Error('Python 프로세스가 준비되지 않음');
        }
        let responseBuffer = '';
        this.responseHandler = (data) => {
            responseBuffer += data.toString();
            // EOT로 분리된 응답 처리
            const responses = responseBuffer.split('\x04');
            responseBuffer = responses.pop() || ''; // 마지막 불완전한 부분 유지
            for (const responseStr of responses) {
                if (responseStr.trim()) {
                    try {
                        const response = JSON.parse(responseStr);
                        this.responseBuffer.set(response.id, response);
                        logger.debug(`응답 수신: ${response.id}`);
                    }
                    catch (e) {
                        logger.error('JSON 파싱 실패:', e, responseStr.substring(0, 100));
                    }
                }
            }
        };
        this.pythonProcess.stdout.on('data', this.responseHandler);
    }
    /**
     * 🔒 안전한 코드 실행 (Lock + JSON)
     */
    static async executeCode(code, timeoutMs = 300000) {
        const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        await this.acquireWriteLock();
        try {
            // JSON 요청 생성
            const request = {
                id: requestId,
                command: 'execute',
                code: code
            };
            // 요청 전송 (EOT로 프레이밍)
            const message = JSON.stringify(request) + '\x04';
            if (!this.pythonProcess || !this.pythonProcess.stdin) {
                throw new Error('Python REPL 프로세스가 준비되지 않음');
            }
            this.pythonProcess.stdin.write(message);
            logger.debug(`요청 전송: ${requestId}`);
            // 응답 대기
            return await this.waitForResponse(requestId, timeoutMs);
        }
        finally {
            this.releaseWriteLock();
        }
    }
    /**
     * 📊 변수 스냅샷 조회
     */
    static async getVariableSnapshot() {
        const requestId = `snapshot_${Date.now()}`;
        await this.acquireWriteLock();
        try {
            const request = {
                id: requestId,
                command: 'snapshot'
            };
            const message = JSON.stringify(request) + '\x04';
            if (!this.pythonProcess || !this.pythonProcess.stdin) {
                throw new Error('Python REPL 프로세스가 준비되지 않음');
            }
            this.pythonProcess.stdin.write(message);
            return await this.waitForResponse(requestId, 5000);
        }
        finally {
            this.releaseWriteLock();
        }
    }
    /**
     * 🏥 헬스체크
     */
    static async healthCheck() {
        try {
            const requestId = `health_${Date.now()}`;
            const request = {
                id: requestId,
                command: 'health'
            };
            await this.acquireWriteLock();
            try {
                const message = JSON.stringify(request) + '\x04';
                if (!this.pythonProcess || !this.pythonProcess.stdin) {
                    return false;
                }
                this.pythonProcess.stdin.write(message);
                const response = await this.waitForResponse(requestId, 3000);
                return response.success === true;
            }
            finally {
                this.releaseWriteLock();
            }
        }
        catch {
            return false;
        }
    }
    /**
     * ⏳ 응답 대기
     */
    static async waitForResponse(requestId, timeoutMs) {
        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                reject(new Error(`Request ${requestId} timeout after ${timeoutMs}ms`));
            }, timeoutMs);
            const checkResponse = () => {
                if (this.responseBuffer.has(requestId)) {
                    const response = this.responseBuffer.get(requestId);
                    this.responseBuffer.delete(requestId);
                    clearTimeout(timeout);
                    resolve(response);
                    return;
                }
                setTimeout(checkResponse, 50); // 50ms마다 체크
            };
            checkResponse();
        });
    }
    /**
     * 🔒 Write Lock 관리
     */
    static async acquireWriteLock() {
        while (this.writeLock) {
            await new Promise(resolve => setTimeout(resolve, 10));
        }
        this.writeLock = true;
    }
    static releaseWriteLock() {
        this.writeLock = false;
    }
    /**
     * 🔄 세션 재시작
     */
    static async resetSession() {
        logger.info('REPL 세션 재시작 중...');
        if (this.pythonProcess) {
            this.pythonProcess.kill();
            this.pythonProcess = null;
        }
        this.responseBuffer.clear();
        this.sessionId = null;
        this.writeLock = false;
        await this.initializeSession();
    }
    /**
     * 📊 세션 상태 정보
     */
    /**
     * REPL 세션 정리 및 재시작 준비
     */
    static async cleanup() {
        logger.info('🧹 REPL 세션 정리 중...');
        if (this.pythonProcess && !this.pythonProcess.killed) {
            try {
                this.pythonProcess.kill('SIGTERM');
                // 프로세스 종료 대기 (최대 3초)
                await new Promise(resolve => {
                    const timeout = setTimeout(resolve, 3000);
                    this.pythonProcess?.on('exit', () => {
                        clearTimeout(timeout);
                        resolve(void 0);
                    });
                });
            }
            catch (e) {
                logger.warn('프로세스 종료 중 오류:', e);
            }
        }
        this.pythonProcess = null;
        this.sessionId = null;
        this.pendingResponses.clear();
        logger.info('✅ REPL 세션 정리 완료');
    }
}
exports.REPLSessionManager = REPLSessionManager;
REPLSessionManager.pythonProcess = null;
REPLSessionManager.sessionId = null;
REPLSessionManager.responseBuffer = new Map();
REPLSessionManager.writeLock = false;
REPLSessionManager.responseHandler = null;
REPLSessionManager.pendingResponses = new Map();
//# sourceMappingURL=repl-session-manager.js.map