import { Tool } from '@modelcontextprotocol/sdk/types';

/**
 * AI Coding Brain MCP - Tool Definitions
 * 
 * 영속적 Python REPL 세션과 프로젝트 관리를 위한 MCP 도구 모음
 * 
 * @version 4.0.0
 * @updated 2025-07-16
 * @author AI Coding Brain Team
 */

// Tool schemas
import { executeCodeSchema } from './schemas/execute-code';
import { restartReplSchema } from './schemas/restart-repl';

/**
 * MCP 도구 정의 배열
 * 각 도구는 name, description, inputSchema를 포함합니다.
 */
export const toolDefinitions: Tool[] = [
  {
    name: 'execute_code',
    description: `Python 코드를 영속적 REPL 세션에서 실행합니다.

핵심 기능:
• 세션 간 변수 유지 - 모든 변수와 상태가 호출 간에 보존됩니다
• 프로젝트별 격리 - 각 프로젝트는 독립적인 실행 환경을 가집니다
• 검증된 헬퍼 함수 (20개) - 파일, JSON, Git, 검색, 디렉토리 작업
• 정밀 코드 수정 - AST 기반 좌표로 정확한 수정 (NEW!)

권장 헬퍼 함수:
• 파일: read_file, write_file, create_file, append_to_file
• JSON: read_json, write_json
• Git: git_status, git_add, git_commit, git_push
• 검색: search_files, search_code
• 분석: parse_file (함수/클래스 위치 정보 제공)

코드 수정 권장 방법 (NEW!):
• replace_function(filepath, func_name, new_code) - 함수 정밀 교체
• replace_method(filepath, class_name, method_name, new_code) - 메서드 정밀 교체
• extract_code_elements(filepath) - 정확한 좌표와 함께 코드 요소 추출
• 기존 replace_block도 사용 가능 (레거시 호환)

주의: 이제 중복 코드가 있어도 정확한 위치를 찾아 수정합니다!`,
    inputSchema: executeCodeSchema
  },
  {
    name: 'restart_json_repl',
    description: `Python REPL 세션을 재시작합니다.

주요 특징:
• 메모리 초기화 - 누적된 변수와 상태를 정리합니다
• 선택적 보존 - helpers 객체는 선택적으로 유지 가능합니다
• 파일 데이터 유지 - 디스크에 저장된 데이터는 영향받지 않습니다
• 프로젝트 컨텍스트 유지 - 현재 프로젝트 설정은 보존됩니다

사용 시나리오:
- 메모리 부족 시 정리
- 새로운 작업 시작 전 환경 초기화
- 오류 상태에서 복구
- 테스트를 위한 깨끗한 환경 준비`,
    inputSchema: restartReplSchema
  }
];

/**
 * 도구 이름으로 도구 정의를 찾습니다
 * @param name 도구 이름
 * @returns 도구 정의 또는 undefined
 */
export function getToolByName(name: string): Tool | undefined {
  return toolDefinitions.find(tool => tool.name === name);
}

/**
 * 모든 도구 이름 목록을 반환합니다
 * @returns 도구 이름 배열
 */
export function getToolNames(): string[] {
  return toolDefinitions.map(tool => tool.name);
}

/**
 * 도구 정의를 검증합니다
 * @param tool 검증할 도구
 * @returns 유효성 여부
 */
export function validateTool(tool: Tool): boolean {
  return !!(
    tool.name &&
    tool.description &&
    tool.inputSchema &&
    typeof tool.inputSchema === 'object'
  );
}

// Type exports for use in handlers
export type ToolName = 'execute_code' | 'restart_json_repl';
export type ToolDefinition = typeof toolDefinitions[number];
