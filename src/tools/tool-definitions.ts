import { Tool } from '@modelcontextprotocol/sdk/types';

/**
 * MCP 도구 정의
 * execute_code와 restart_json_repl 도구를 정의합니다.
 */

export interface Tool {
  name: string;
  description: string;
  inputSchema: {
    type: 'object';
    properties: Record<string, any>;
    required?: string[];
  };
}

export const toolDefinitions: Tool[] = [
  {
    name: 'execute_code',
    description: `Python 코드 실행 - 영속적 세션과 프로젝트 관리 도구

🔄 **세션 특징**
- 모든 변수가 execute_code 호출 간에 유지됩니다
- 세션이 재시작되어도 파일로 저장된 데이터는 보존됩니다
- 각 프로젝트별로 독립적인 메모리 구조를 가집니다

🚀 **부트스트랩 모듈 (자동 로드)**
\`\`\`python
# 날짜/시간 - import 없이 바로 사용
datetime.now(), date.today(), timedelta(days=1)

# 파일 시스템 - 직접 사용
join('folder', 'file.txt')  # os.path.join 대신
exists('file.txt'), makedirs('dir'), basename('path')
isfile('test.py'), isdir('folder')

# 정규표현식, 파일 패턴, 유틸리티
re.search(r'패턴', '텍스트')
glob.glob('*.py')
shutil.copy('src', 'dst')
random.randint(1, 10)
Counter(['a', 'b', 'a'])
\`\`\`

🎯 **핵심 헬퍼 함수 (안전한 버전 - 모든 반환값이 dict/list[dict])**
\`\`\`python
# 1. 코드 분석 - AST 기반 (가장 강력)
result = parse_file("file.py")
# 반환: {'success': bool, 'functions': [], 'classes': [], 'methods': []}

# 2. 코드 검색
results = search_code(".", "TODO", "*.py")
# 반환: [{'file': str, 'line': int, 'text': str, 'context': []}]

# 3. 코드 수정 - 안전한 블록 교체
result = replace_block("file.py", old_code, new_code)
# 반환: {'success': bool, 'file': str, 'backup': str, 'changes': int}

# 4. Git 작업
status = git_status()
# 반환: {'success': bool, 'is_clean': bool, 'modified': [], 'untracked': []}

# 5. 디렉토리 스캔
scan = scan_directory(".")
# 반환: {'files': [], 'dirs': [], 'total_files': int, 'total_dirs': int}
\`\`\`

📁 **프로젝트 관리**
\`\`\`python
flow_project("프로젝트명")  # 또는 fp("프로젝트명")
list_projects()  # 또는 lp()
project_info()   # 또는 pi()
\`\`\`

📋 **워크플로우**
\`\`\`python
workflow('/start 작업명')
workflow('/task 세부작업')
workflow('/complete 메모')
\`\`\`

⚡ **최적 사용 패턴**
1. **parse_file + replace_block 콤보**
   \`\`\`python
   parsed = parse_file("main.py")
   for func in parsed['functions']:
       if 'TODO' in func['code']:
           replace_block("main.py", func['code'], new_code)
   \`\`\`

2. **변수로 상태 유지**
   \`\`\`python
   task_context = {'phase': 1, 'files': [], 'results': []}
   # 다음 execute_code에서도 task_context 사용 가능
   \`\`\`

3. **stdout 기반 작업 체인**
   \`\`\`python
   print("[NEXT_ACTION]: ANALYZE_CODE")
   print("[CONTEXT]: task_context 변수 참조")
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

세션에 문제가 발생했거나 초기화가 필요할 때 사용합니다.
파일로 저장된 데이터(워크플로우, 히스토리)는 유지됩니다.

\`\`\`python
restart_json_repl()              # 기본 사용 (helpers 유지)
restart_json_repl(keep_helpers=False)  # 완전 초기화
restart_json_repl(reason="메모리 정리")  # 이유 명시
\`\`\`

재시작 후에도:
- 프로젝트별 memory/ 폴더의 데이터는 유지됩니다
- continue_from_last()로 이전 작업을 복원할 수 있습니다`,
    inputSchema: {
      type: 'object',
      properties: {
        keep_helpers: {
          type: 'boolean',
          default: true,
          description: 'helpers 객체 유지 여부'
        },
        reason: {
          type: 'string',
          default: '세션 새로고침',
          description: '재시작 이유'
        }
      },
      required: []
    }
  }
];