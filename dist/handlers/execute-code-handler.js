"use strict";
/**
 * Execute Code 핸들러 - JSON REPL 세션 강제 활성화
 * json_repl_session.py를 무조건 사용하여 변수 지속성 보장
 */
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
exports.ExecuteCodeHandler = void 0;
const logger_1 = require("../services/logger");
const child_process_1 = require("child_process");
const util_1 = require("util");
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const os = __importStar(require("os"));
const logger = (0, logger_1.createLogger)('execute-code-handler');
const execFileAsync = (0, util_1.promisify)(child_process_1.execFile);
class ExecuteCodeHandler {
    /**
     * 📊 세션 정보 반환
     */
    static getSessionInfo() {
        return {
            session_active: this.replProcess !== null && !this.replProcess.killed,
            repl_ready: this.replReady,
            variables_count: this.sessionVariables.size,
            last_activity: this.lastActivity?.toISOString(),
            session_mode: 'JSON_REPL'
        };
    }
    /**
     * 🚀 JSON REPL 세션 초기화 (json_repl_session.py 직접 실행)
     */
    static async initializeJsonReplSession() {
        if (this.replProcess && !this.replProcess.killed) {
            logger.info('JSON REPL 세션이 이미 활성화되어 있습니다');
            return true;
        }
        try {
            const projectRoot = path.join(__dirname, '..', '..');
            const replScript = path.join(projectRoot, 'python', 'json_repl_session.py');
            logger.info(`🚀 JSON REPL 세션 시작: ${replScript}`);
            // json_repl_session.py 직접 실행
            const pythonPath = process.env['PYTHON_PATH'] ||
                (process.platform === 'win32' ? 'C:\\Users\\Administrator\\miniconda3\\python.exe' : 'python');
            this.replProcess = (0, child_process_1.spawn)(pythonPath, ['-X', 'utf8', replScript], {
                stdio: ['pipe', 'pipe', 'pipe'],
                env: {
                    ...process.env,
                    PYTHONIOENCODING: 'utf-8',
                    PYTHONUTF8: '1',
                    PYTHON_SCRIPT_PATH: 'python\\json_repl_session.py'
                }
            });
            // 준비 신호 대기
            return new Promise((resolve) => {
                let initBuffer = '';
                const timeout = setTimeout(() => {
                    logger.error('JSON REPL 초기화 타임아웃');
                    resolve(false);
                }, 10000);
                this.replProcess.stdout.on('data', (data) => {
                    initBuffer += data.toString();
                    if (initBuffer.includes('__READY__')) {
                        clearTimeout(timeout);
                        this.replReady = true;
                        logger.info('✅ JSON REPL 세션 준비 완료');
                        resolve(true);
                    }
                });
                this.replProcess.stderr.on('data', (data) => {
                    const errorOutput = data.toString();
                    logger.info(`JSON REPL stderr: ${errorOutput}`);
                });
                this.replProcess.on('error', (error) => {
                    clearTimeout(timeout);
                    logger.error('JSON REPL 프로세스 오류:', error);
                    resolve(false);
                });
                this.replProcess.on('exit', (code) => {
                    logger.warn(`JSON REPL 프로세스 종료: 코드 ${code}`);
                    this.replProcess = null;
                    this.replReady = false;
                });
            });
        }
        catch (error) {
            logger.error('JSON REPL 세션 초기화 실패:', error);
            return false;
        }
    }
    /**
     * 🎯 JSON REPL 세션으로 코드 실행
     */
    static async executeWithJsonRepl(code) {
        if (!this.replProcess || !this.replReady) {
            const initialized = await this.initializeJsonReplSession();
            if (!initialized) {
                throw new Error('JSON REPL 세션 초기화 실패');
            }
        }
        return new Promise((resolve, reject) => {
            const requestId = `req_${++this.requestCounter}_${Date.now()}`;
            const request = {
                id: requestId,
                command: 'execute',
                code: code
            };
            let responseBuffer = '';
            let timeout;
            const cleanup = () => {
                if (timeout)
                    clearTimeout(timeout);
                this.replProcess.stdout.removeAllListeners('data');
            };
            // 응답 대기
            const dataHandler = (data) => {
                responseBuffer += data.toString();
                // EOT 문자로 응답 완료 감지
                const eotIndex = responseBuffer.indexOf('\x04');
                if (eotIndex !== -1) {
                    cleanup();
                    const responseData = responseBuffer.substring(0, eotIndex);
                    try {
                        // JSON 형식이 아닌 출력을 필터링
                        // 첫 번째 '{' 문자부터 시작하는 JSON 데이터만 파싱
                        const jsonStartIndex = responseData.indexOf('{');
                        if (jsonStartIndex === -1) {
                            throw new Error('JSON 데이터를 찾을 수 없습니다');
                        }
                        const jsonData = responseData.substring(jsonStartIndex);
                        const response = JSON.parse(jsonData);
                        if (response.id === requestId) {
                            this.lastActivity = new Date();
                            resolve(response);
                        }
                        else {
                            reject(new Error(`응답 ID 불일치: 예상=${requestId}, 실제=${response.id}`));
                        }
                    }
                    catch (parseError) {
                        // 디버깅을 위해 처리
                        reject(new Error(`JSON 파싱 실패: ${parseError}, 데이터: ${responseData}`));
                    }
                }
            };
            this.replProcess.stdout.on('data', dataHandler);
            // 타임아웃 설정
            timeout = setTimeout(() => {
                cleanup();
                reject(new Error('JSON REPL 응답 타임아웃'));
            }, 300000); // 300초 (5분) - 증가됨
            // 요청 전송
            const requestJson = JSON.stringify(request);
            this.replProcess.stdin.write(requestJson + '\x04', 'utf8');
        });
    }
    /**
     * 🎛️ 세션 명령어 처리
     */
    static async handleSessionCommand(command) {
        const cmd = command.toLowerCase().trim();
        switch (cmd) {
            case '/vars':
                if (this.replReady && this.replProcess) {
                    try {
                        const result = await this.executeWithJsonRepl('print("📊 세션 변수 목록:")\\nfor k, v in locals().items():\\n    if not k.startswith("_"):\\n        print(f"  {k}: {type(v).__name__}")');
                        return {
                            success: true,
                            stdout: result.stdout || '세션 변수가 없습니다',
                            note: 'JSON REPL Session Variables',
                            timestamp: new Date().toISOString()
                        };
                    }
                    catch (error) {
                        return {
                            success: false,
                            error: `변수 조회 실패: ${error}`,
                            timestamp: new Date().toISOString()
                        };
                    }
                }
                else {
                    return {
                        success: true,
                        stdout: '❌ JSON REPL 세션이 활성화되지 않았습니다',
                        note: 'Session not active',
                        timestamp: new Date().toISOString()
                    };
                }
            case '/clear':
                if (this.replReady && this.replProcess) {
                    try {
                        await this.executeWithJsonRepl('locals().clear()\\nprint("🧹 세션 변수 초기화 완료")');
                        this.sessionVariables.clear();
                        return {
                            success: true,
                            stdout: '🧹 JSON REPL 세션 변수 초기화 완료',
                            note: 'Session variables cleared',
                            timestamp: new Date().toISOString()
                        };
                    }
                    catch (error) {
                        return {
                            success: false,
                            error: `세션 초기화 실패: ${error}`,
                            timestamp: new Date().toISOString()
                        };
                    }
                }
                break;
            case '/reset':
                // REPL 프로세스 종료 후 재시작
                if (this.replProcess) {
                    this.replProcess.kill();
                    this.replProcess = null;
                    this.replReady = false;
                }
                this.sessionVariables.clear();
                this.lastActivity = null;
                const restarted = await this.initializeJsonReplSession();
                return {
                    success: restarted,
                    stdout: restarted ? '🔄 JSON REPL 세션 재시작 완료' : '❌ 세션 재시작 실패',
                    note: 'Session restart attempt',
                    timestamp: new Date().toISOString()
                };
            case '/memory':
                let output = '💾 JSON REPL 세션 상태:\\n\\n';
                output += `🔧 실행 모드: JSON REPL (json_repl_session.py)\\n`;
                output += `📊 변수 지속성: ✅ 완전 지원\\n`;
                output += `🚀 AI 헬퍼 함수: ✅ 백그라운드 로드\\n`;
                output += `⚡ 실행 방식: JSON 프레이밍 통신\\n`;
                output += `🔄 세션 상태: ${this.replReady ? '활성' : '비활성'}\\n`;
                output += `📈 프로세스 ID: ${this.replProcess?.pid || 'N/A'}\\n`;
                return {
                    success: true,
                    stdout: output,
                    note: 'JSON REPL Session Status',
                    timestamp: new Date().toISOString()
                };
            case '/help':
                const help = `
🚀 JSON REPL 세션 명령어:

📊 /vars    - 현재 세션 변수 목록
🧹 /clear   - 세션 변수 초기화  
🔄 /reset   - REPL 세션 재시작
💾 /memory  - 세션 상태 확인
❓ /help    - 이 도움말 표시

⚡ 현재 모드: JSON REPL (json_repl_session.py)
• 변수와 함수가 실행 간 유지됩니다
• AI 헬퍼 함수가 자동으로 로드됩니다
• InteractiveConsole 기반 세션 관리
• JSON 프레이밍으로 안정적 통신
`;
                return {
                    success: true,
                    stdout: help,
                    note: 'JSON REPL Session Help',
                    timestamp: new Date().toISOString()
                };
            default:
                return {
                    success: false,
                    error: `Unknown session command: ${command}`,
                    note: 'Available: /vars, /clear, /reset, /memory, /help',
                    timestamp: new Date().toISOString()
                };
        }
    }
    /**
     * stdout에서 불필요한 메시지 필터링
     */
    static cleanExecutionOutput(stdout) {
        const linesToFilter = [
            '__READY__',
            '[Python] JSON 프레이밍 Python REPL 시작',
            '[Python] 초기화 완료 - 세션 준비됨',
            '[OK] AI 헬퍼 함수 6개 로드 완료'
        ];
        return stdout
            .split('\n')
            .filter(line => !linesToFilter.some(filter => line.includes(filter)))
            .join('\n')
            .trim();
    }
    /**
     * Node.js 실행 파일 찾기
     */
    static async findNodeExecutable() {
        const candidates = [
            'node', // PATH에 있는 경우
            'C:\\Program Files\\nodejs\\node.exe',
            'C:\\Program Files (x86)\\nodejs\\node.exe',
            path.join(process.env['ProgramFiles'] || '', 'nodejs', 'node.exe'),
            path.join(process.env['ProgramFiles(x86)'] || '', 'nodejs', 'node.exe'),
        ];
        for (const candidate of candidates) {
            try {
                await execFileAsync(candidate, ['--version']);
                logger.info(`Node.js found: ${candidate}`);
                return candidate;
            }
            catch {
                // Try next candidate
            }
        }
        throw new Error('Node.js not found. Please install Node.js or add it to PATH.');
    }
    /**
     * npm/npx 실행 파일 찾기
     */
    static async findNpmExecutable(command) {
        const candidates = [
            command, // PATH에 있는 경우
            `C:\\Program Files\\nodejs\\${command}.cmd`,
            `C:\\Program Files\\nodejs\\${command}`,
            `C:\\Program Files (x86)\\nodejs\\${command}.cmd`,
            path.join(process.env['ProgramFiles'] || '', 'nodejs', `${command}.cmd`),
            path.join(process.env['ProgramFiles(x86)'] || '', 'nodejs', `${command}.cmd`),
            path.join(process.env['APPDATA'] || '', 'npm', `${command}.cmd`),
        ];
        for (const candidate of candidates) {
            try {
                await execFileAsync(candidate, ['--version']);
                logger.info(`${command} found: ${candidate}`);
                return candidate;
            }
            catch {
                // Try next candidate
            }
        }
        throw new Error(`${command} not found. Please install Node.js or add it to PATH.`);
    }
    /**
     * TypeScript 런타임 찾기
     */
    static async findTypeScriptRuntime() {
        const candidates = [
            'npx tsx',
            'npx ts-node',
            path.join(process.cwd(), 'node_modules/.bin/tsx'),
            path.join(process.cwd(), 'node_modules/.bin/ts-node'),
            'tsx',
            'ts-node'
        ];
        for (const candidate of candidates) {
            try {
                if (candidate.includes(' ')) {
                    const parts = candidate.split(' ');
                    if (parts[0])
                        await execFileAsync(parts[0], [...parts.slice(1), '--version']);
                }
                else {
                    await execFileAsync(candidate, ['--version']);
                }
                logger.info(`TypeScript runtime found: ${candidate}`);
                return candidate;
            }
            catch {
                // Try next candidate
            }
        }
        return null;
    }
    /**
     * 🎯 메인 execute_code 핸들러
     */
    static async handleExecuteCode(args) {
        const DEBUG_MODE = true;
        logger.info('🚀 JSON REPL 강제 활성화 모드 - execute_code 핸들러');
        // 세션 명령어 처리
        if (args.code.startsWith('/')) {
            logger.info(`🎛️ Processing session command: ${args.code}`);
            const result = await this.handleSessionCommand(args.code);
            return {
                content: [
                    {
                        type: 'text',
                        text: JSON.stringify({
                            ...result,
                            session_info: this.getSessionInfo(),
                            ai_helpers_enabled: true,
                            language: 'session'
                        }, null, 2),
                    },
                ],
            };
        }
        // 언어 감지
        const codeContent = args.code.toLowerCase();
        const strongPythonIndicators = [
            'import ', 'print(', 'def ', 'backup_file', 'safe_replace',
            'from ', 'if __name__', 'elif ', 'with open(', 'r"', "r'", '"""', "'''"
        ];
        const strongJsIndicators = [
            'console.log', 'const ', 'let ', 'var ', 'require(', 'module.exports',
            'function(', '=>', 'document.', 'window.'
        ];
        const strongTsIndicators = [
            'interface ', 'type ', ': string', ': number', ': boolean', ': void',
            'implements ', 'extends ', 'public ', 'private ', 'protected ',
            'enum ', '<T>', 'Generic', 'readonly ', '?: '
        ];
        const hasStrongPython = strongPythonIndicators.some(indicator => codeContent.includes(indicator));
        const hasStrongJs = strongJsIndicators.some(indicator => codeContent.includes(indicator));
        const hasStrongTs = strongTsIndicators.some(indicator => codeContent.includes(indicator));
        let language;
        if (args.language) {
            language = args.language;
        }
        else {
            if (hasStrongPython) {
                language = 'python';
            }
            else if (hasStrongTs && !hasStrongPython) {
                language = 'typescript';
            }
            else if (hasStrongJs && !hasStrongPython) {
                language = 'javascript';
            }
            else {
                language = 'python'; // 기본값은 Python (JSON REPL 사용)
            }
        }
        // 🚀 Python 코드는 무조건 JSON REPL 세션으로 실행
        if (language === 'python') {
            try {
                logger.info('🚀 JSON REPL 세션으로 Python 코드 실행');
                const result = await this.executeWithJsonRepl(args.code);
                return {
                    content: [
                        {
                            type: 'text',
                            text: JSON.stringify({
                                success: result.success || true,
                                language: 'python',
                                session_mode: 'JSON_REPL',
                                stdout: this.cleanExecutionOutput(result.stdout || ''),
                                stderr: result.stderr || '',
                                variable_count: result.variable_count,
                                note: 'JSON REPL Session - Variables persist between executions',
                                debug_info: DEBUG_MODE ? {
                                    repl_process_active: this.replProcess !== null,
                                    repl_ready: this.replReady,
                                    execution: 'success'
                                } : undefined,
                                timestamp: new Date().toISOString()
                            }, null, 2),
                        },
                    ],
                };
            }
            catch (error) {
                logger.error('JSON REPL 실행 실패:', error);
                return {
                    content: [
                        {
                            type: 'text',
                            text: JSON.stringify({
                                success: false,
                                language: 'python',
                                session_mode: 'JSON_REPL_ERROR',
                                error: error instanceof Error ? error.message : String(error),
                                note: 'JSON REPL Session execution failed',
                                debug_info: DEBUG_MODE ? {
                                    repl_process_active: this.replProcess !== null,
                                    repl_ready: this.replReady,
                                    error_type: error instanceof Error ? error.constructor.name : 'Unknown'
                                } : undefined,
                                timestamp: new Date().toISOString()
                            }, null, 2),
                        },
                    ],
                };
            }
        }
        // TypeScript/JavaScript는 기존 execFile 방식 유지
        try {
            this.lastActivity = new Date();
            let tempFile;
            const tempDir = os.tmpdir();
            const timestamp = Date.now();
            if (language === 'typescript') {
                tempFile = path.join(tempDir, `execute_code_${timestamp}.ts`);
                fs.writeFileSync(tempFile, args.code, 'utf8');
                const tsRuntime = await this.findTypeScriptRuntime();
                let stdout = '';
                let stderr = '';
                if (tsRuntime) {
                    if (tsRuntime.includes(' ')) {
                        const parts = tsRuntime.split(' ');
                        if (parts[0]) {
                            const { stdout: out, stderr: err } = await execFileAsync(parts[0], [...parts.slice(1), tempFile]);
                            stdout = out;
                            stderr = err;
                        }
                    }
                    else {
                        const { stdout: out, stderr: err } = await execFileAsync(tsRuntime, [tempFile]);
                        stdout = out;
                        stderr = err;
                    }
                }
                else {
                    const npxExe = await this.findNpmExecutable('npx');
                    const { stdout: out, stderr: err } = await execFileAsync(npxExe, ['--yes', 'tsx@latest', tempFile]);
                    stdout = out;
                    stderr = err;
                }
                fs.unlinkSync(tempFile);
                return {
                    content: [
                        {
                            type: 'text',
                            text: JSON.stringify({
                                success: true,
                                language: 'typescript',
                                execution_method: 'execFile',
                                stdout: (stdout || '').trim(),
                                stderr: (stderr || '').trim(),
                                note: 'TypeScript execution with execFile',
                                timestamp: new Date().toISOString()
                            }, null, 2),
                        },
                    ],
                };
            }
            else {
                // JavaScript
                tempFile = path.join(tempDir, `execute_code_${timestamp}.js`);
                fs.writeFileSync(tempFile, args.code, 'utf8');
                const nodeExe = await this.findNodeExecutable();
                const { stdout, stderr } = await execFileAsync(nodeExe, [tempFile]);
                fs.unlinkSync(tempFile);
                return {
                    content: [
                        {
                            type: 'text',
                            text: JSON.stringify({
                                success: true,
                                language: 'javascript',
                                execution_method: 'execFile',
                                stdout: (stdout || '').trim(),
                                stderr: (stderr || '').trim(),
                                note: 'JavaScript execution with execFile',
                                timestamp: new Date().toISOString()
                            }, null, 2),
                        },
                    ],
                };
            }
        }
        catch (error) {
            let errorMessage = error instanceof Error ? error.message : String(error);
            if (errorMessage.includes('Traceback')) {
                const lines = errorMessage.split('\\n');
                const errorLine = lines[lines.length - 1] || lines[lines.length - 2];
                if (errorLine && errorLine.includes('Error:')) {
                    errorMessage = errorLine.trim();
                }
            }
            return {
                content: [
                    {
                        type: 'text',
                        text: JSON.stringify({
                            success: false,
                            error: errorMessage,
                            note: 'Execution failed',
                            timestamp: new Date().toISOString()
                        }, null, 2),
                    },
                ],
            };
        }
    }
    /**
     * 🔄 JSON REPL 세션 재시작
     */
    static async handleRestartJsonRepl(args) {
        const reason = args.reason || '세션 새로고침';
        const keepHelpers = args.keep_helpers !== false; // 기본값 true
        logger.info(`🔄 JSON REPL 세션 재시작 요청: ${reason} (헬퍼 유지: ${keepHelpers})`);
        try {
            // 현재 세션 정보 저장
            const sessionInfo = this.getSessionInfo();
            const wasActive = sessionInfo.session_active;
            // 기존 세션 종료
            if (this.replProcess) {
                logger.info('기존 JSON REPL 세션 종료 중...');
                this.replProcess.kill();
                this.replProcess = null;
                this.replReady = false;
                this.sessionVariables.clear();
                this.lastActivity = null;
                // 프로세스 종료 대기
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
            // 새 세션 시작
            logger.info('새 JSON REPL 세션 시작 중...');
            const initialized = await this.initializeJsonReplSession();
            if (!initialized) {
                throw new Error('JSON REPL 세션 재시작 실패');
            }
            // 헬퍼 함수 재로드 여부 확인
            let helpersLoaded = false;
            if (keepHelpers) {
                // json_repl_session.py에서 헬퍼 함수가 자동으로 로드됨
                logger.info('AI 헬퍼 함수 자동 로드됨');
                helpersLoaded = true;
            }
            const result = {
                success: true,
                reason: reason,
                previous_state: wasActive ? 'active' : 'inactive',
                new_state: 'active',
                keep_helpers: keepHelpers,
                helpers_loaded: helpersLoaded,
                session_info: this.getSessionInfo(),
                note: keepHelpers ? 'Session restarted with AI helpers preserved' : 'Clean session restart',
                timestamp: new Date().toISOString()
            };
            return {
                content: [
                    {
                        type: 'text',
                        text: JSON.stringify(result, null, 2)
                    }
                ]
            };
        }
        catch (error) {
            logger.error('JSON REPL 재시작 중 오류:', error);
            return {
                content: [
                    {
                        type: 'text',
                        text: JSON.stringify({
                            success: false,
                            error: error instanceof Error ? error.message : String(error),
                            reason: reason,
                            timestamp: new Date().toISOString()
                        }, null, 2)
                    }
                ]
            };
        }
    }
}
exports.ExecuteCodeHandler = ExecuteCodeHandler;
// 🚀 JSON REPL 세션 관리
ExecuteCodeHandler.replProcess = null;
ExecuteCodeHandler.replReady = false;
ExecuteCodeHandler.sessionVariables = new Set();
ExecuteCodeHandler.lastActivity = null;
ExecuteCodeHandler.requestCounter = 0;
//# sourceMappingURL=execute-code-handler.js.map