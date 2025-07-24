/**
 * Execute Code 핸들러 - JSON REPL 세션 강제 활성화
 * json_repl_session.py를 무조건 사용하여 변수 지속성 보장
 */

import { createLogger } from '../services/logger';
import { spawn, ChildProcess, execFile } from 'child_process';
import { promisify } from 'util';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { fixPythonIndent, detectIndentationIssues, processMagicCommands } from '../utils/indent-helper';

const logger = createLogger('execute-code-handler');
const execFileAsync = promisify(execFile);

export class ExecuteCodeHandler {
  // 🚀 JSON REPL 세션 관리
  private static replProcess: ChildProcess | null = null;
  private static replReady: boolean = false;
  private static sessionVariables: Set<string> = new Set();
  private static lastActivity: Date | null = null;
  private static requestCounter: number = 0;

  /**
   * 📊 세션 정보 반환
   */
  private static getSessionInfo(): any {
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
  private static async initializeJsonReplSession(): Promise<boolean> {
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
      this.replProcess = spawn(pythonPath, ['-u', '-X', 'utf8', replScript], {
        stdio: ['pipe', 'pipe', 'pipe'],
        env: {
          ...process.env,
          PYTHONIOENCODING: 'utf-8',
          PYTHONUTF8: '1',
          PYTHONUNBUFFERED: '1',
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

        this.replProcess!.stdout!.on('data', (data) => {
          initBuffer += data.toString();
          if (initBuffer.includes('__READY__')) {
            clearTimeout(timeout);
            this.replReady = true;
            logger.info('✅ JSON REPL 세션 준비 완료');
            resolve(true);
          }
        });

        this.replProcess!.stderr!.on('data', (data) => {
          const errorOutput = data.toString();
          logger.info(`JSON REPL stderr: ${errorOutput}`);
        });

        this.replProcess!.on('error', (error) => {
          clearTimeout(timeout);
          logger.error('JSON REPL 프로세스 오류:', error);
          resolve(false);
        });

        this.replProcess!.on('exit', (code) => {
          logger.warn(`JSON REPL 프로세스 종료: 코드 ${code}`);
          this.replProcess = null;
          this.replReady = false;
        });
      });
    } catch (error) {
      logger.error('JSON REPL 세션 초기화 실패:', error);
      return false;
    }
  }

  /**
   * 🎯 JSON REPL 세션으로 코드 실행
   */
  private static async executeWithJsonRepl(code: string): Promise<any> {
    if (!this.replProcess || !this.replReady) {
      const initialized = await this.initializeJsonReplSession();
      if (!initialized) {
        throw new Error('JSON REPL 세션 초기화 실패');
      }
    }

    return new Promise((resolve, reject) => {
      const requestId = `req_${++this.requestCounter}_${Date.now()}`;
      const request = {
        jsonrpc: '2.0',
        id: requestId,
        method: 'execute',
        params: {
          code: code
        }
      };

      let responseBuffer = '';
      let timeout: NodeJS.Timeout;

      const cleanup = () => {
        if (timeout) clearTimeout(timeout);
        if (this.replProcess && this.replProcess.stdout) {
          this.replProcess.stdout.removeAllListeners('data');
        }
      };

      // JSON 프레이밍 응답 파싱 (프로토콜 태그 우선, 그 다음 가장 마지막 {...} 블록)
      const extractLastJson = (text: string): any | null => {
        // 1. 프로토콜 태그로 감싸진 JSON 찾기
        const startTag = '__JSON_START__';
        const endTag = '__JSON_END__';
        const startIdx = text.lastIndexOf(startTag);
        const endIdx = text.lastIndexOf(endTag);
        
        if (startIdx !== -1 && endIdx !== -1 && startIdx < endIdx) {
          const jsonContent = text.slice(startIdx + startTag.length, endIdx);
          try {
            return JSON.parse(jsonContent);
          } catch (e) {
            logger.warn('프로토콜 태그 JSON 파싱 실패:', e);
            // 프로토콜 태그 파싱 실패 시 아래 로직으로 fallback
          }
        }
        
        // 2. 프로토콜 태그가 없으면 가장 마지막 완전한 {...} 블록 찾기
        let lastValidJson: any = null;
        const stack: number[] = [];
        
        for (let i = 0; i < text.length; i++) {
          if (text[i] === '{') {
            stack.push(i);
          } else if (text[i] === '}' && stack.length > 0) {
            const start = stack.pop()!;
            
            // 모든 괄호가 닫혔을 때만 파싱 시도
            if (stack.length === 0) {
              const candidate = text.slice(start, i + 1);
              try {
                const parsed = JSON.parse(candidate);
                // 유효한 JSON이면 저장 (가장 마지막 것이 저장됨)
                lastValidJson = parsed;
              } catch {
                // 파싱 실패는 무시하고 계속
              }
            }
          }
        }
        
        return lastValidJson;
      };

      // 응답 대기 - 라인 기반 처리
      const dataHandler = (data: Buffer) => {
        responseBuffer += data.toString();
        
        // 줄바꿈으로 구분된 완전한 라인들 처리
        const lines = responseBuffer.split('\n');
        responseBuffer = lines.pop() || ''; // 마지막 불완전한 라인은 버퍼에 유지
        
        for (const line of lines) {
          if (!line.trim()) continue;
          
          try {
            const parsed = JSON.parse(line);
            
            // JSON-RPC 응답인지 확인
            if (parsed.jsonrpc === '2.0' && parsed.id === requestId) {
              cleanup();
              this.lastActivity = new Date();
              
              // result가 있으면 성공, error가 있으면 에러
              if (parsed.result) {
                resolve(parsed.result);
              } else if (parsed.error) {
                reject(new Error(parsed.error.message || 'JSON-RPC error'));
              } else {
                reject(new Error('Invalid JSON-RPC response'));
              }
              return;
            }
          } catch (e) {
            // JSON 파싱 실패는 무시 (stderr 출력 등일 수 있음)
            logger.debug('Non-JSON line ignored:', line);
          }
        }
      };

      this.replProcess!.stdout!.on('data', dataHandler);

      // 타임아웃 설정
      timeout = setTimeout(() => {
        cleanup();
        reject(new Error('JSON REPL 응답 타임아웃'));
      }, 300000); // 300초 (5분) - 증가됨

      // 요청 전송
      const requestJson = JSON.stringify(request);
      this.replProcess!.stdin!.write(requestJson + '\n', 'utf8');
    });
  }

  /**
   * 🎛️ 세션 명령어 처리
   */
  private static async handleSessionCommand(command: string): Promise<any> {
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
          } catch (error) {
            return {
              success: false,
              error: `변수 조회 실패: ${error}`,
              timestamp: new Date().toISOString()
            };
          }
        } else {
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
          } catch (error) {
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
  private static cleanExecutionOutput(output: string, isStderr: boolean = false): string {
    if (isStderr) {
      // stderr 처리 - IndentationError를 간결하게
      if (/IndentationError/.test(output)) {
        const lines = output.split('\n');
        // 마지막 몇 줄만 반환 (핵심 오류 메시지)
        const relevantLines = lines.filter(line => 
          line.includes('IndentationError') || 
          line.includes('line') ||
          line.includes('File')
        ).slice(-3);
        return relevantLines.join('\n');
      }
      
      // 기타 Python 오류도 간결하게
      if (/File ".*", line \d+/.test(output)) {
        const lines = output.split('\n');
        // 오류 타입과 메시지만 추출
        const errorLines = lines.filter(line => 
          /^\w+Error:/.test(line) || 
          /File ".*", line \d+/.test(line)
        ).slice(-3);
        return errorLines.join('\n');
      }
      
      return output;
    }
    
    // stdout 처리 - 기존 로직
    const linesToFilter = [
      '__READY__',
      '[Python] JSON 프레이밍 Python REPL 시작',
      '[Python] 초기화 완료 - 세션 준비됨',
      '[OK] AI 헬퍼 함수 6개 로드 완료'
    ];

    return output
      .split('\n')
      .filter((line: string) => !linesToFilter.some(filter => line.includes(filter)))
      .join('\n')
      .trim();
  }

  /**
   * Node.js 실행 파일 찾기
   */
  private static async findNodeExecutable(): Promise<string> {
    const candidates = [
      'node',  // PATH에 있는 경우
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
      } catch {
        // Try next candidate
      }
    }

    throw new Error('Node.js not found. Please install Node.js or add it to PATH.');
  }

  /**
   * npm/npx 실행 파일 찾기
   */
  private static async findNpmExecutable(command: 'npm' | 'npx'): Promise<string> {
    const candidates = [
      command,  // PATH에 있는 경우
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
      } catch {
        // Try next candidate
      }
    }

    throw new Error(`${command} not found. Please install Node.js or add it to PATH.`);
  }

  /**
   * TypeScript 런타임 찾기
   */
  private static async findTypeScriptRuntime(): Promise<string | null> {
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
          if (parts[0]) await execFileAsync(parts[0], [...parts.slice(1), '--version']);
        } else {
          await execFileAsync(candidate, ['--version']);
        }
        logger.info(`TypeScript runtime found: ${candidate}`);
        return candidate;
      } catch {
        // Try next candidate
      }
    }

    return null;
  }

  /**
   * 🎯 메인 execute_code 핸들러
   */
  static async handleExecuteCode(args: { code: string; language?: string }): Promise<{ content: Array<{ type: string; text: string }> }> {
    const DEBUG_MODE = true;
    logger.info('🚀 JSON REPL 강제 활성화 모드 - execute_code 핸들러');
    
    // arguments 검증
    if (!args || typeof args !== 'object') {
      logger.error('Invalid arguments received:', args);
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            success: false,
            error: 'Invalid arguments: args object is required',
            timestamp: new Date().toISOString()
          }, null, 2)
        }]
      };
    }
    
    if (!args.code) {
      logger.error('Missing code parameter:', args);
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            success: false,
            error: 'Missing required parameter: code',
            timestamp: new Date().toISOString()
          }, null, 2)
        }]
      };
    }

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

    let language: 'python' | 'javascript' | 'typescript';
    if (args.language) {
      language = args.language as 'python' | 'javascript' | 'typescript';
    } else {
      if (hasStrongPython) {
        language = 'python';
      } else if (hasStrongTs && !hasStrongPython) {
        language = 'typescript';
      } else if (hasStrongJs && !hasStrongPython) {
        language = 'javascript';
      } else {
        language = 'python'; // 기본값은 Python (JSON REPL 사용)
      }
    }

    // 🚀 Python 코드는 무조건 JSON REPL 세션으로 실행
    if (language === 'python') {
      try {
        logger.info('🚀 JSON REPL 세션으로 Python 코드 실행');
        // console.log('[DEBUG] Original code:', args.code.substring(0, 50) + '...');

        // 매직 커맨드 처리 (%%py 등)
        let cleanedCode = processMagicCommands(args.code);
        // console.log('[DEBUG] After processMagicCommands:', cleanedCode.substring(0, 50) + '...');
        
        // 들여쓰기 문제 감지
        const indentIssues = detectIndentationIssues(cleanedCode);
        if (indentIssues.issues.length > 0) {
          logger.warn('들여쓰기 문제 감지:', indentIssues.issues);
        }
        
        // 들여쓰기 자동 정리
        cleanedCode = fixPythonIndent(cleanedCode);
        // console.log('[DEBUG] After fixPythonIndent:', cleanedCode.substring(0, 50) + '...');
        logger.debug('들여쓰기 정리 완료');

        const result = await this.executeWithJsonRepl(cleanedCode);

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                success: result.success || true,
                language: 'python',
                session_mode: 'JSON_REPL',
                stdout: this.cleanExecutionOutput(result.stdout || ''),
                stderr: this.cleanExecutionOutput(result.stderr || '', true),
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
      } catch (error) {
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

      let tempFile: string;
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
          } else {
            const { stdout: out, stderr: err } = await execFileAsync(tsRuntime, [tempFile]);
            stdout = out;
            stderr = err;
          }
        } else {
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
      } else {
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
    } catch (error) {
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
  static async handleRestartJsonRepl(args: { reason?: string; keep_helpers?: boolean }): Promise<{ content: Array<{ type: string; text: string }> }> {
    // arguments 검증
    const validArgs = args && typeof args === 'object' ? args : {};
    const reason = validArgs.reason || '세션 새로고침';
    const keepHelpers = validArgs.keep_helpers !== false; // 기본값 true
    
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
      
    } catch (error) {
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
