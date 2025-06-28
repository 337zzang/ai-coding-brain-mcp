/**
 * HybridHelperSystem TypeScript 인터페이스
 * ai-coding-brain-mcp 프로젝트용 타입 정의
 *
 * Python HybridHelperSystem과 연동하기 위한 인터페이스
 */
export interface HybridSystemStats {
    calls: number;
    errors: number;
    fixes: number;
    created_files: number;
    backup_files: number;
}
export interface HybridSystemStatus {
    originals: number;
    enhanced: number;
    stats: HybridSystemStats;
    logs_count: number;
    system_info: {
        python_version: string;
        platform: string;
    };
}
export interface HybridSystemLog {
    timestamp: string;
    level: 'INFO' | 'ERROR' | 'WARNING';
    message: string;
    extra?: Record<string, any>;
}
export interface ParseResult {
    parsing_success: boolean;
    file_path: string;
    language?: string;
    total_lines?: number;
    functions?: Array<{
        name: string;
        line_start: number;
        line_end: number;
        parameters: string[];
    }>;
    classes?: Array<{
        name: string;
        line_start: number;
        methods: string[];
    }>;
    imports?: Array<{
        name: string;
        line: number;
        type: string;
    }>;
    error?: string;
}
export interface CodingExperience {
    data: Record<string, any>;
    tech_stack: string[];
    timestamp: string;
    importance: number;
    system: string;
}
/**
 * HybridHelperSystem Manager 클래스
 * TypeScript에서 Python HybridHelperSystem과 통신
 */
export declare class HybridHelperSystemManager {
    private executeCodeHandler;
    constructor(executeCodeHandler: any);
    /**
     * Python HybridHelperSystem 상태 확인
     */
    getSystemStatus(): Promise<HybridSystemStatus | null>;
    /**
     * 안전한 파일 읽기 (RecursionError 없음)
     */
    safeReadFile(filepath: string): Promise<string | null>;
    /**
     * 안전한 파일 파싱 (RecursionError 없음)
     */
    safeParseWithSnippets(filepath: string, language?: string): Promise<ParseResult | null>;
    /**
     * 안전한 파일 백업
     */
    safeBackupFile(filepath: string, reason?: string): Promise<string | null>;
    /**
     * 안전한 텍스트 교체
     */
    safeReplaceText(filepath: string, oldText: string, newText: string): Promise<string | null>;
    /**
     * 코딩 경험 저장
     */
    saveCodingExperience(data: Record<string, any>, techStack?: string[]): Promise<string | null>;
    /**
     * HybridHelperSystem 리셋
     */
    resetSystem(): Promise<boolean>;
    /**
     * 시스템 로그 조회
     */
    getSystemLogs(level?: 'INFO' | 'ERROR' | 'WARNING'): Promise<HybridSystemLog[] | null>;
    /**
     * 전체 시스템 상태 보고서 생성
     */
    generateStatusReport(): Promise<string>;
}
export default HybridHelperSystemManager;
//# sourceMappingURL=hybrid-helper-system.d.ts.map