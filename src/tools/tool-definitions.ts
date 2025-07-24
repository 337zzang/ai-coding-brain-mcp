import { Tool } from '@modelcontextprotocol/sdk/types';

/**
 * AI Coding Brain MCP - Tool Definitions
 * 
 * 영속적 Python REPL 세션과 프로젝트 관리를 위한 MCP 도구 모음
 * 
 * @version 4.2.0
 * @updated 2025-07-23
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
• AI Helpers v2.0 - 6개 모듈로 구성된 강력한 헬퍼 시스템
• o3 백그라운드 실행 - 비동기 AI 상담 기능
• 정밀 코드 수정 - AST 기반 좌표로 정확한 수정

AI Helpers v2.0 모듈 구조:
• file.py - 파일 작업 (read, write, append, exists, info, read_json, write_json)
• code.py - 코드 분석/수정 (parse, view, replace, insert, functions, classes)
• search.py - 검색 기능 (search_files, search_code, find_function, find_class, grep)
• llm.py - LLM 작업 (ask_o3, ask_o3_async, check_o3_status, show_o3_progress, get_o3_result)
• util.py - 유틸리티 (ok, err, is_ok, get_data, get_error)
• git.py - Git 작업 (status, add, commit, diff, log, branch, push, pull)

사용 예시:
import ai_helpers_new as h

# 파일 작업
content = h.read('file.py')['data']
h.write('output.py', content)
h.append('log.txt', 'new line\\n')

# exists 함수 (v19.0 업데이트 - 이제 dict 반환)
result = h.exists('file.txt')  # {'ok': True, 'data': True/False, 'path': 'file.txt'}

# JSON 작업
data = h.read_json('config.json')['data']
h.write_json('output.json', data)

# 코드 분석
info = h.parse('module.py')
if info['ok']:
    functions = info['data']['functions']
    classes = info['data']['classes']

# 코드 수정
h.replace('file.py', 'old_code', 'new_code')
h.view('file.py', 'function_name')
h.insert('file.py', 'line content', line_number)

# 검색 (v19.0 개선 - 와일드카드 자동 처리)
results = h.search_files('test')  # 자동으로 *test*로 변환
results = h.search_files('*.py')  # 모든 Python 파일
results = h.search_code('pattern', '.')  # 코드 내용 검색
files = h.find_function('main', '.')
classes = h.find_class('MyClass', '.')

# Git 작업
git_result = h.git_status()
if git_result['ok']:
    print(git_result['data'])
h.git_add('.')
h.git_commit('feat: 새 기능 추가')
h.git_push()

# o3 백그라운드 실행 (병렬 처리)
task_id = h.ask_o3_async("복잡한 질문")['data']
status = h.check_o3_status(task_id)
h.show_o3_progress()
result = h.get_o3_result(task_id)

# 에러 처리 패턴
result = h.read('missing.txt')
if not h.is_ok(result):
    print(h.get_error(result))

워크플로우 시스템:
• wf("/status") - 현재 상태 확인
• wf("/task 작업명") - 새 작업 추가
• wf("/next") - 다음 작업으로 이동
• wf("/done") - 현재 작업 완료
• wf("/list") - 전체 작업 목록 보기
• wf("/delete 번호") - 특정 작업 삭제

프로젝트 관리:
• helpers.fp("project-name") - 프로젝트 전환
• helpers.get_current_project() - 현재 프로젝트 확인
• helpers.list_projects() - 모든 프로젝트 목록
• helpers.scan_directory(".", max_depth=2) - 디렉토리 스캔 (v19.0 개선)
• helpers.project_info() - 프로젝트 정보 조회

Flow 시스템 (대화 컨텍스트 관리):
• flow_project("project-name") - Flow 프로젝트로 전환
• flow_list() - 모든 Flow 목록 조회
• flow_save("flow-name", {"key": "value"}) - Flow 데이터 저장
• flow_load("flow-name") - Flow 데이터 로드
• flow_context() - 현재 Flow 컨텍스트 조회

모든 헬퍼 함수는 일관된 dict 형식 반환:
{'ok': bool, 'data': 결과, 'error': 에러메시지(실패시), ...추가정보}`,
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
