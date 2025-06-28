"use strict";
/**
 * HybridHelperSystem TypeScript 인터페이스
 * ai-coding-brain-mcp 프로젝트용 타입 정의
 *
 * Python HybridHelperSystem과 연동하기 위한 인터페이스
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.HybridHelperSystemManager = void 0;
/**
 * HybridHelperSystem Manager 클래스
 * TypeScript에서 Python HybridHelperSystem과 통신
 */
class HybridHelperSystemManager {
    constructor(executeCodeHandler) {
        this.executeCodeHandler = executeCodeHandler;
    }
    /**
     * Python HybridHelperSystem 상태 확인
     */
    async getSystemStatus() {
        try {
            const result = await this.executeCodeHandler.handleExecuteCode({
                code: 'get_hybrid_system_status()',
                language: 'python'
            });
            const response = JSON.parse(result.content[0].text);
            if (response.success && response.stdout) {
                return JSON.parse(response.stdout);
            }
            return null;
        }
        catch (error) {
            console.error('HybridSystem 상태 확인 실패:', error);
            return null;
        }
    }
    /**
     * 안전한 파일 읽기 (RecursionError 없음)
     */
    async safeReadFile(filepath) {
        try {
            const result = await this.executeCodeHandler.handleExecuteCode({
                code: `read_file(r"${filepath}")`,
                language: 'python'
            });
            const response = JSON.parse(result.content[0].text);
            if (response.success && response.stdout) {
                return response.stdout.trim();
            }
            return null;
        }
        catch (error) {
            console.error('안전한 파일 읽기 실패:', error);
            return null;
        }
    }
    /**
     * 안전한 파일 파싱 (RecursionError 없음)
     */
    async safeParseWithSnippets(filepath, language = 'auto') {
        try {
            const result = await this.executeCodeHandler.handleExecuteCode({
                code: `
import json
result = parse_with_snippets(r"${filepath}", "${language}")
print(json.dumps(result))
`,
                language: 'python'
            });
            const response = JSON.parse(result.content[0].text);
            if (response.success && response.stdout) {
                return JSON.parse(response.stdout.trim());
            }
            return null;
        }
        catch (error) {
            console.error('안전한 파일 파싱 실패:', error);
            return null;
        }
    }
    /**
     * 안전한 파일 백업
     */
    async safeBackupFile(filepath, reason = 'TypeScript backup') {
        try {
            const result = await this.executeCodeHandler.handleExecuteCode({
                code: `backup_file(r"${filepath}", "${reason}")`,
                language: 'python'
            });
            const response = JSON.parse(result.content[0].text);
            if (response.success && response.stdout) {
                return response.stdout.trim();
            }
            return null;
        }
        catch (error) {
            console.error('안전한 파일 백업 실패:', error);
            return null;
        }
    }
    /**
     * 안전한 텍스트 교체
     */
    async safeReplaceText(filepath, oldText, newText) {
        try {
            // 특수 문자 이스케이프
            const escapedOldText = oldText.replace(/"/g, '\\"').replace(/\n/g, '\\n');
            const escapedNewText = newText.replace(/"/g, '\\"').replace(/\n/g, '\\n');
            const result = await this.executeCodeHandler.handleExecuteCode({
                code: `safe_replace(r"${filepath}", "${escapedOldText}", "${escapedNewText}")`,
                language: 'python'
            });
            const response = JSON.parse(result.content[0].text);
            if (response.success && response.stdout) {
                return response.stdout.trim();
            }
            return null;
        }
        catch (error) {
            console.error('안전한 텍스트 교체 실패:', error);
            return null;
        }
    }
    /**
     * 코딩 경험 저장
     */
    async saveCodingExperience(data, techStack = []) {
        try {
            const result = await this.executeCodeHandler.handleExecuteCode({
                code: `
import json
experience_data = ${JSON.stringify(data)}
tech_stack = ${JSON.stringify(techStack)}
result = save_coding_experience(experience_data, project_context, tech_stack)
print(result)
`,
                language: 'python'
            });
            const response = JSON.parse(result.content[0].text);
            if (response.success && response.stdout) {
                return response.stdout.trim();
            }
            return null;
        }
        catch (error) {
            console.error('코딩 경험 저장 실패:', error);
            return null;
        }
    }
    /**
     * HybridHelperSystem 리셋
     */
    async resetSystem() {
        try {
            const result = await this.executeCodeHandler.handleExecuteCode({
                code: 'reset_hybrid_system()',
                language: 'python'
            });
            const response = JSON.parse(result.content[0].text);
            return response.success && response.stdout?.includes('재설정 완료');
        }
        catch (error) {
            console.error('HybridSystem 리셋 실패:', error);
            return false;
        }
    }
    /**
     * 시스템 로그 조회
     */
    async getSystemLogs(level) {
        try {
            const levelParam = level ? `"${level}"` : 'None';
            const result = await this.executeCodeHandler.handleExecuteCode({
                code: `
import json
if '__hybrid_system__' in globals():
    logs = __hybrid_system__.get_logs(${levelParam})
    print(json.dumps(logs))
else:
    print("[]")
`,
                language: 'python'
            });
            const response = JSON.parse(result.content[0].text);
            if (response.success && response.stdout) {
                return JSON.parse(response.stdout.trim());
            }
            return null;
        }
        catch (error) {
            console.error('시스템 로그 조회 실패:', error);
            return null;
        }
    }
    /**
     * 전체 시스템 상태 보고서 생성
     */
    async generateStatusReport() {
        try {
            const status = await this.getSystemStatus();
            const logs = await this.getSystemLogs();
            if (!status) {
                return 'HybridHelperSystem 상태를 확인할 수 없습니다.';
            }
            let report = `📊 HybridHelperSystem 상태 보고서\n`;
            report += `${'='.repeat(50)}\n\n`;
            report += `🔧 시스템 정보:\n`;
            report += `  • 등록된 안전 함수: ${status.enhanced}개\n`;
            report += `  • 백업된 원본 함수: ${status.originals}개\n`;
            report += `  • 수집된 로그: ${status.logs_count}개\n\n`;
            report += `📈 사용 통계:\n`;
            report += `  • 총 호출 횟수: ${status.stats.calls}회\n`;
            report += `  • 오류 발생: ${status.stats.errors}회\n`;
            report += `  • 수정 작업: ${status.stats.fixes}회\n`;
            report += `  • 생성된 파일: ${status.stats.created_files}개\n`;
            report += `  • 백업 파일: ${status.stats.backup_files}개\n\n`;
            const successRate = status.stats.calls > 0
                ? ((status.stats.calls - status.stats.errors) / status.stats.calls * 100).toFixed(1)
                : '100.0';
            report += `✅ 성공률: ${successRate}%\n\n`;
            report += `🖥️ 환경 정보:\n`;
            report += `  • Python: ${status.system_info.python_version}\n`;
            report += `  • 플랫폼: ${status.system_info.platform}\n\n`;
            if (logs && logs.length > 0) {
                report += `📋 최근 로그 (최대 5개):\n`;
                const recentLogs = logs.slice(-5);
                for (const log of recentLogs) {
                    const time = new Date(log.timestamp).toLocaleTimeString();
                    report += `  ${time} [${log.level}] ${log.message}\n`;
                }
            }
            return report;
        }
        catch (error) {
            return `상태 보고서 생성 실패: ${error}`;
        }
    }
}
exports.HybridHelperSystemManager = HybridHelperSystemManager;
exports.default = HybridHelperSystemManager;
//# sourceMappingURL=hybrid-helper-system.js.map