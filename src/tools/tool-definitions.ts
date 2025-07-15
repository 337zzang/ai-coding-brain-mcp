import { Tool } from '@modelcontextprotocol/sdk/types.js';

/**
 * AI Coding Brain MCP - Tool Definitions
 * 
 * 이 MCP 서버는 영속적인 Python REPL 세션을 제공하여
 * AI가 코드를 실행하고 프로젝트를 관리할 수 있도록 합니다.
 */

export const toolDefinitions: Tool[] = [
  {
    name: 'execute_code',
    description: `Python 코드 실행

JSON REPL 세션에서 Python 코드를 실행합니다.
세션 간 변수가 유지되며, 복잡한 작업 수행이 가능합니다.

주요 기능:
- 변수 영속성 (세션 유지)
- 파일 시스템 접근
- 데이터 처리 및 분석
- 프로젝트 관리 작업

사용 가능한 helpers 메서드:
- helpers.scan_directory_dict(path) - 디렉토리 스캔 (딕셔너리 반환)
- helpers.read_file(path) - 파일 읽기
- helpers.create_file(path, content) - 파일 생성/수정
- helpers.search_files_advanced(path, pattern) - 파일명 검색
  예: helpers.search_files_advanced(".", "*.py")
  반환: {'results': [파일정보 리스트]}
- helpers.search_code_content(path, pattern, file_pattern) - 코드 내용 검색
  예: helpers.search_code_content("python", "def", "*.py")
  반환: {'results': [파일별 매치 정보]}
- helpers.replace_block(file, target, new_code) - 코드 블록 교체
- helpers.cmd_flow_with_context(project) - 프로젝트 전환

사용 예:
\`\`\`python
# 디렉토리 구조 파악
files = helpers.scan_directory_dict(".")
print(f"파일: {len(files['files'])}개")
print(f"디렉토리: {len(files['directories'])}개")

# 파일 읽기/쓰기
content = helpers.read_file("config.json")
helpers.create_file("output.txt", content)

# 코드 수정
helpers.replace_block("app.py", "function_name", new_code)
\`\`\``,
    inputSchema: {
      type: 'object',
      properties: {
        code: {
          type: 'string',
          description: '실행할 Python 코드'
        },
        language: {
          type: 'string',
          enum: ['python'],
          default: 'python',
          description: '프로그래밍 언어'
        }
      },
      required: ['code']
    }
  },
  {
    name: 'restart_json_repl',
    description: `JSON REPL 세션 재시작

용도: 메모리 정리, 변수 초기화
기본값: helpers 유지하며 재시작

\`\`\`python
restart_json_repl()  # helpers 유지
restart_json_repl(keep_helpers=False)  # 완전 초기화
\`\`\``,
    inputSchema: {
      type: 'object',
      properties: {
        reason: {
          type: 'string',
          description: '재시작 이유',
          default: '세션 새로고침'
        },
        keep_helpers: {
          type: 'boolean',
          description: 'helpers 객체 유지 여부',
          default: true
        }
      },
      required: []
    }
  }
];
