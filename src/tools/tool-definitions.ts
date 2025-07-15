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
    description: `Python 코드 실행 - 영속적 세션과 프로젝트 관리 도구

🔄 **세션 특징**
- 모든 변수가 execute_code 호출 간에 유지됩니다
- 세션이 재시작되어도 파일로 저장된 데이터는 보존됩니다
- 각 프로젝트별로 독립적인 메모리 구조를 가집니다

📁 **프로젝트 관리**
\`\`\`python
# 프로젝트 생성/전환 (바탕화면에 생성)
flow_project("프로젝트명")  # 또는 fp("프로젝트명")

# 프로젝트 목록 보기
list_projects()  # 또는 lp()

# 프로젝트 정보 확인
project_info()  # 또는 pi()
\`\`\`

📋 **워크플로우 명령어** (프로젝트별 독립)
\`\`\`python
# 기본 명령
workflow('/start 작업명')  # 또는 wf('/s 작업명')
workflow('/task 태스크명')  # 또는 wf('/t 태스크명')
workflow('/list')          # 태스크 목록
workflow('/status')        # 현재 상태
workflow('/complete 메모') # 또는 wf('/c 메모')
workflow('/next')          # 다음 태스크로

# 태스크 제어
workflow('/focus 번호')    # 특정 태스크 시작
workflow('/pause 이유')    # 일시 중지
workflow('/continue')      # 재개
workflow('/skip 이유')     # 건너뛰기
workflow('/error 메시지')  # 에러 보고
workflow('/reset')         # 초기화
workflow('/help')          # 도움말
\`\`\`

🧠 **AI Coding Brain 영속적 헬퍼 함수**
\`\`\`python
# 세션 관리
init_session()  # 세션 시작/확인
save_checkpoint("이름", 데이터)  # 상태 저장
loaded = load_checkpoint("이름")  # 상태 로드
show_history(5)  # 최근 작업 히스토리
add_to_history("작업명", {"데이터": "값"})  # 히스토리 추가

# 캐싱 (토큰 절약)
result = cached_operation("키", expensive_func)  # 결과 캐싱
clear_cache("키")  # 특정 캐시 삭제
clear_cache()  # 전체 캐시 삭제

# 워크플로우
show_plan(tasks)  # 작업 계획 표시 ([USER_CONFIRMATION_REQUIRED])
update_progress("작업명", 50)  # 진행률 표시
request_feedback("메시지", ["옵션1", "옵션2"])  # 피드백 요청

# 대용량 처리
results = chunk_processor(data, func, chunk_size=100)  # 청크 단위 처리
result = safe_execute(risky_func)  # 안전한 실행 (오류 처리)
result = try_execute_or_recover(func)  # 실패시 Desktop Commander 제안
with measure_time("작업명"):  # 시간 측정
    # 작업 수행
    pass

# 헬퍼 도움말
help_quick()  # 빠른 참조
show_helpers()  # 전체 헬퍼 함수 목록
show_helpers('cache')  # 특정 카테고리만
search_helper('search')  # 헬퍼 검색
show_session_summary()  # 세션 요약 통계
\`\`\`

📚 **헬퍼 함수** (helpers 객체로 접근)
\`\`\`python
# 파일 작업
content = helpers.read_file("파일경로")
helpers.create_file("파일경로", "내용")
helpers.write_file("파일경로", "내용")  # create_file과 동일
helpers.append_to_file("파일경로", "추가내용")
exists = helpers.file_exists("파일경로")

# JSON 작업
data = helpers.read_json("파일.json")
helpers.write_json("파일.json", data)

# 디렉토리 스캔
files = helpers.scan_directory_dict("경로")
# 반환: {'files': [파일정보], 'directories': [디렉토리명]}

# 코드 검색
# 1. 파일명으로 검색
results = helpers.search_files("경로", "*.py")
# 반환: ['파일경로1', '파일경로2', ...]

# 2. 코드 내용으로 검색
results = helpers.search_code("경로", "def", "*.py")
# 반환: [{'file': '파일', 'line_number': 줄, 'line': '내용', 'context': [주변]}, ...]
results = helpers.grep("경로", "패턴")

# 3. AI 친화적 구조화된 검색 (권장)
results = search_files_advanced("경로", "*.py")
# 반환: {'results': [{'path': '전체경로', 'name': '파일명', 'size': 크기}, ...]}

results = search_code_content("경로", "검색어", "*.py")
# 반환: {'results': [{'file': '파일경로', 'matches': [{'line': 줄번호, 'content': '내용'}, ...]}, ...]}
func_info = helpers.find_function("함수명", "*.py")
class_info = helpers.find_class("클래스명", "*.py")

# 코드 수정
helpers.replace_block("파일.py", "기존코드", "새코드")
helpers.insert_block("파일.py", "위치표시", "삽입할코드", position="after")

# Git 작업
status = helpers.git_status()
helpers.git_add("파일경로")
helpers.git_commit("커밋 메시지")
helpers.git_push()
helpers.git_pull()
branch_info = helpers.git_branch()

# 프로젝트 구조 생성
structure = {
    "프로젝트명": {
        "src": {},
        "tests": {},
        "docs": {"README.md": "# 프로젝트"}
    }
}
helpers.create_project_structure("경로", structure)

# 유틸리티
metrics = helpers.get_metrics()  # 코드 통계
helpers.clear_cache()  # 캐시 정리
history = helpers.get_execution_history()  # 실행 기록
\`\`\`

📜 **히스토리 관리** (프로젝트별 독립)
\`\`\`python
# 히스토리 보기
show_history()  # 또는 show_history(10)

# 히스토리에 수동 추가
add_history("작업명", "설명", {"데이터": "값"})

# 마지막 작업에서 이어가기
data = continue_from_last()
\`\`\`

💾 **파일 구조**
각 프로젝트는 독립적인 memory/ 폴더를 가집니다:
\`\`\`
Desktop/프로젝트명/
└── memory/
    ├── workflow.json         # 워크플로우 상태
    ├── workflow_history.json # 작업 히스토리
    ├── checkpoints/          # 상태 스냅샷
    └── project.json          # 프로젝트 메타데이터
\`\`\`

🔥 **자주 사용하는 패턴**
\`\`\`python
# 1. 새 프로젝트 시작
fp("my-project")
wf('/start 웹 개발')
wf('/task 프론트엔드 구현')
wf('/task 백엔드 API')

# 2. 파일 작업
files = helpers.scan_directory_dict(".")
for file in files['files']:
    if file['name'].endswith('.py'):
        content = helpers.read_file(file['path'])
        # 처리...

# 3. 코드 검색 및 수정
results = helpers.search_code(".", "TODO", "*.py")
for result in results['results']:
    print(f"{result['file']}: {result['matches']} matches")

# 4. Git 작업
helpers.git_add(".")
helpers.git_commit("feat: 새 기능 추가")
helpers.git_push()
\`\`\`

⚡ **팁**
- 모든 작업은 현재 프로젝트의 memory/에 자동 저장됩니다
- 프로젝트를 통째로 이동/백업할 수 있습니다
- 세션이 재시작되어도 continue_from_last()로 이어갈 수 있습니다`,
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

메모리 변수를 초기화하고 세션을 새로 시작합니다.
파일로 저장된 데이터(워크플로우, 히스토리)는 유지됩니다.

\`\`\`python
# 기본 사용 (helpers 유지)
restart_json_repl()

# 완전 초기화
restart_json_repl(keep_helpers=False)

# 이유 명시
restart_json_repl(reason="메모리 정리")
\`\`\`

재시작 후에도:
- 프로젝트별 memory/ 폴더의 데이터는 유지됩니다
- continue_from_last()로 이전 작업을 복원할 수 있습니다
- 워크플로우 상태는 파일에서 자동 로드됩니다`,
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