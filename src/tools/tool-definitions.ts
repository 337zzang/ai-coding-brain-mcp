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

🚀 **부트스트랩 모듈 (세션 시작 시 자동 로드)**
\`\`\`python
# 날짜/시간 - import 없이 바로 사용
datetime.now()              # from datetime import datetime 불필요
date.today()               # from datetime import date 불필요
timedelta(days=1)          # from datetime import timedelta 불필요

# 파일 시스템 - os.path.* 함수들을 직접 사용
join('folder', 'file.txt')  # os.path.join 대신
exists('file.txt')         # os.path.exists 대신
makedirs('new_folder')     # os.makedirs 대신
basename('/path/file.txt') # os.path.basename 대신
isfile('test.py')         # os.path.isfile 대신
isdir('folder')           # os.path.isdir 대신

# 정규표현식 - import re 없이
re.search(r'패턴', '텍스트')
re.findall(r'\d+', '123abc456')
re.compile(r'[a-z]+')

# 파일 패턴 매칭 - import glob 없이
glob.glob('*.py')
glob.glob('**/*.txt', recursive=True)

# 파일 작업 - import shutil 없이
shutil.copy('src.txt', 'dst.txt')
shutil.move('old.txt', 'new.txt')
copy('file1', 'file2')  # shutil.copy 직접 사용

# 데이터 구조 - from collections import 없이
Counter(['a', 'b', 'a'])
defaultdict(list)

# 기타 유용한 모듈
random.randint(1, 10)      # import random 없이
subprocess.run(['ls'])     # import subprocess 없이
itertools.chain([1], [2])  # import itertools 없이

# 이미 로드된 모듈: os, sys, json, time, Path, np (numpy), pd (pandas)
\`\`\`

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
# 반환: List[str] - 파일 경로들의 리스트
# 예시: ['.\\test.py', '.\\src\\main.py', ...]

# 2. 코드 내용으로 검색
results = helpers.search_code("경로", "def", "*.py")
# 반환: List[Dict] - 각 매치에 대한 상세 정보
# 각 요소: {'file': '파일경로', 'line_number': 줄번호, 'line': '매치된 라인', 'context': ['주변', '라인들']}
results = helpers.grep("패턴", "경로", "*")  # grep(패턴, 경로, 파일패턴) 순서 주의!

# 3. 함수/클래스 찾기 (매개변수 순서 주의!)
func_info = helpers.find_function("경로", "함수명")  # find_function(디렉토리, 함수명)
class_info = helpers.find_class("경로", "클래스명")  # find_class(디렉토리, 클래스명)
# 반환: search_code와 동일한 구조 (List[Dict])
# 특수문자가 있는 함수명/클래스명도 자동으로 이스케이프 처리됨

# 코드 수정
helpers.replace_block("파일.py", "기존코드", "새코드")
helpers.insert_block("파일.py", "위치표시", "삽입할코드", position="after")

# 고급 코드 작업
# find_code_position - 코드 위치 찾기 (3개 매개변수 필요)
position = helpers.find_code_position("파일.py", "검색할 텍스트", 시작위치)  # 시작위치는 보통 0
# update_file_directory - 파일 디렉토리 업데이트
helpers.update_file_directory("프로젝트경로")  # 프로젝트 경로 필수
# find_fuzzy_match - 퍼지 매칭 (두 번째 매개변수는 문자열!)
result = helpers.find_fuzzy_match("검색할 내용", "대상 텍스트")  # 리스트 X, 문자열 O
# 반환: {'found': bool, 'matched_code': str, 'similarity': float, 'suggestion': str}

# Git 작업
status = helpers.git_status()
# 반환: {'success': bool, 'modified': [파일들], 'untracked': [파일들], 'staged': [파일들], 'clean': bool}
helpers.git_add("파일경로")  # 또는 "." 로 전체 추가
helpers.git_commit("커밋 메시지")
helpers.git_push()
helpers.git_pull()
branch_info = helpers.git_branch()
# 반환: {'current': '현재브랜치', 'branches': ['브랜치1', '브랜치2', ...]}

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
# 3-1. TODO 항목 찾기
results = helpers.search_code(".", "TODO", "*.py")
for result in results:
    print(f"{result['file']}:{result['line_number']} - {result['line']}")

# 3-2. 특정 함수 찾아서 수정
func_results = helpers.find_function(".", "old_function")
if func_results:
    file_path = func_results[0]['file']
    old_code = func_results[0]['line']
    # 함수 시그니처 변경
    helpers.replace_block(file_path, old_code, "def new_function():")

# 3-3. 클래스 찾기 (특수문자 있어도 OK)
class_results = helpers.find_class(".", "MyAPI++Handler")
for result in class_results:
    print(f"Found class in: {result['file']}")

# 3-4. 파일 검색 후 내용 확인
py_files = helpers.search_files(".", "test_*.py")
for file in py_files[:5]:  # 처음 5개만
    content = helpers.read_file(file)
    print(f"File: {file}, Lines: {len(content.splitlines())}")

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