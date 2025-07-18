import { Tool } from '@modelcontextprotocol/sdk/types';

/**
 * AI Coding Brain MCP - Tool Definitions
 * 
 * 영속적 Python REPL 세션과 프로젝트 관리를 위한 MCP 도구 모음
 * 
 * @version 4.1.0
 * @updated 2025-07-17
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
• 검증된 헬퍼 함수 (20개+) - 파일, JSON, Git, 검색, 디렉토리 작업
• 정밀 코드 수정 - AST 기반 좌표로 정확한 수정 (NEW!)
• HelperResult 패턴 - 표준화된 결과 반환 (NEW!)

권장 헬퍼 함수:
• 파일: read_file, write_file, create_file, append_to_file, file_exists
• JSON: read_json, write_json
• Git: git_status, git_add, git_commit, git_push, git_branch
• 검색: search_files, search_code (SearchResult 반환)
• 분석: parse_file (ParseResult 반환), scan_directory
• 프로젝트: fp(project_name), get_current_project
• AI: ask_o3(prompt) - AI 도우미

NEW! HelperResult 패턴:
• SearchResult - 검색 결과 (count, files(), by_file() 메서드)
• FileResult - 파일 작업 결과 (lines, size 속성)
• ParseResult - 파싱 결과 (functions, classes 속성)

NEW! 안전한 헬퍼 함수:
• safe_search_code() - 예외 없이 SearchResult 반환
• safe_read_file() - 예외 없이 FileResult 반환
• safe_parse_file() - 예외 없이 ParseResult 반환

NEW! Quick 함수 (REPL 친화적):
• qs(pattern) - 코드 검색, SearchResult 반환
• qfind(path, pattern) - 파일 검색, SearchResult 반환
• qc(pattern) - 현재 디렉토리 검색
• qv(file, func) - 함수 코드 보기
• qproj() - 프로젝트 정보 표시

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
export function findToolByName(name: string): Tool | undefined {
  return toolDefinitions.find(tool => tool.name === name);
}

/**
 * 모든 도구 이름 목록을 반환합니다
 * @returns 도구 이름 배열
 */
export function getToolNames(): string[] {
  return toolDefinitions.map(tool => tool.name);
}
