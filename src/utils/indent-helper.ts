/**
 * Python 코드 들여쓰기 정리 유틸리티
 */

import { createLogger } from '../services/logger';

const logger = createLogger('indent-helper');

/**
 * Python 코드의 들여쓰기를 정리합니다.
 * - CRLF → LF 통일
 * - 탭 → 4 스페이스 변환
 * - 공통 선행 공백 제거 (dedent)
 */
export function fixPythonIndent(src: string): string {
    logger.debug('fixPythonIndent called with:', src.substring(0, 50) + '...');
    
    // CRLF → LF 통일, 탭 → 4 스페이스
    const lines = src.replace(/\r\n/g, '\n')
                     .replace(/\t/g, '    ')
                     .split('\n');
    
    // 빈 줄이 아닌 줄들의 최소 들여쓰기 찾기
    const nonEmptyLines = lines.filter(line => line.trim().length > 0);
    if (nonEmptyLines.length === 0) {
        return src;
    }
    
    // 각 줄의 선행 공백 수 계산
    const indentLevels = nonEmptyLines.map(line => {
        const match = line.match(/^ */);
        return match ? match[0].length : 0;
    });
    
    // 최소 들여쓰기 수준 찾기
    const minIndent = Math.min(...indentLevels);
    
    // 모든 줄에서 최소 들여쓰기만큼 제거
    const dedentedLines = lines.map(line => {
        // 빈 줄은 그대로 유지
        if (line.trim().length === 0) {
            return '';
        }
        // 최소 들여쓰기만큼 제거
        return line.slice(minIndent);
    });
    
    return dedentedLines.join('\n');
}

/**
 * Python 코드에서 흔한 들여쓰기 문제를 감지합니다.
 */
export function detectIndentationIssues(code: string): {
    hasMixedIndentation: boolean;
    hasTabIndentation: boolean;
    hasTrailingWhitespace: boolean;
    issues: string[];
} {
    const lines = code.split('\n');
    const issues: string[] = [];
    let hasMixedIndentation = false;
    let hasTabIndentation = false;
    let hasTrailingWhitespace = false;
    
    lines.forEach((line, index) => {
        // 탭 감지
        if (line.includes('\t')) {
            hasTabIndentation = true;
            issues.push(`Line ${index + 1}: Contains tab characters`);
        }
        
        // 탭과 스페이스 혼용 감지
        if (line.match(/^[ \t]*\t[ \t]*/) && line.match(/^[ \t]* [ \t]*/)) {
            hasMixedIndentation = true;
            issues.push(`Line ${index + 1}: Mixed tabs and spaces`);
        }
        
        // 후행 공백 감지
        if (line.match(/\s+$/)) {
            hasTrailingWhitespace = true;
            issues.push(`Line ${index + 1}: Trailing whitespace`);
        }
    });
    
    return {
        hasMixedIndentation,
        hasTabIndentation,
        hasTrailingWhitespace,
        issues
    };
}

/**
 * 매직 커맨드 처리 (%%py 등)
 */
export function processMagicCommands(code: string): string {
    logger.debug('processMagicCommands called, starts with %%py?', code.trimStart().startsWith('%%py'));
    
    // %%py로 시작하는 경우 첫 줄 제거
    if (code.trimStart().startsWith('%%py')) {
        const lines = code.split('\n');
        lines.shift(); // 첫 줄 제거
        const result = lines.join('\n');
        logger.debug('Magic command processed, result:', result.substring(0, 50) + '...');
        return result;
    }
    return code;
}
