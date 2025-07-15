/**
 * AI Coding Brain MCP - Tool Definitions v8.0
 * 핵심 워크플로우 유지, 중복만 제거
 * 
 * 작성일: 2025-06-16
 */

// 도구 정의 타입
interface ToolDefinition {
    name: string;
    description: string;
    inputSchema: {
        type: string;
        properties: Record<string, any>;
        required?: string[];
    };
}

export const toolDefinitions: ToolDefinition[] = [
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
                    description: '프로그래밍 언어',
                    enum: ['python'],
                    default: 'python'
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
    },

    // ========== 프로젝트 관리 도구 ==========
    // ========== API 관리 도구 ==========
    {
        name: 'toggle_api',
        description: 'API를 활성화하거나 비활성화합니다. 이미지 생성(image), 웹 자동화(web_automation) 등 특수 기능 API를 on/off 할 수 있습니다.',
        inputSchema: {
            type: 'object',
            properties: {
                api_name: {
                    type: 'string',
                    description: 'API 이름 (예: image, web_automation 등)'
                },
                enabled: {
                    type: 'boolean',
                    description: '활성화 여부 (기본값: true)',
                    default: true
                }
            },
            required: ['api_name']
        }
    },

    {
        name: 'list_apis',
        description: '사용 가능한 특수 기능 API 목록과 활성화 상태를 조회합니다. (image, web_automation)',
        inputSchema: {
            type: 'object',
            properties: {},
            required: []
        }
    }
];
