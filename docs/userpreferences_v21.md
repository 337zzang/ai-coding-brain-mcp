# AI Coding Brain MCP - 유저 프리퍼런스 v21.0 (실제 구현 기준)

## 🎯 핵심 작업 원칙

### 1. **상세 작업 계획 수립 (최우선)**
모든 작업 시작 전 반드시 다음 형식으로 상세 계획 제시:

```markdown
## 📋 작업 제목: [작업명]

### 🔍 현재 상태 분석
- **대상 모듈**: `경로/파일명.py`
- **관련 함수**: `함수명()` (라인 X-Y)
- **현재 코드**:
  ```python
  # 실제 코드 스니펫
  ```
- **문제점**: 구체적인 문제 설명

### 🛠️ 수정 계획
1. **수정할 파일**: 
   - `파일1.py`: 함수A 수정 (라인 10-20)
   - `파일2.py`: 클래스B 추가 (라인 50)

2. **구체적인 변경 내용**:
   ```python
   # 변경 전
   def old_function():
       pass

   # 변경 후
   def new_function():
       # 개선된 로직
   ```

3. **영향 범위**:
   - 이 함수를 사용하는 곳: `module1.py`, `module2.py`
   - 예상 부작용: 없음/있다면 구체적으로

### 📊 테스트 계획
1. 단위 테스트: `test_function()`
2. 통합 테스트: 실제 사용 시나리오
3. 예상 결과:
   ```python
   expected = {'key': 'value'}
   ```

### ⚠️ 위험 요소
- 백업 필요 파일: `file1.py`, `file2.py`
- 롤백 계획: 백업에서 복원

### ❓ 확인 필요 사항
1. [질문1] 이 방식이 맞나요?
2. [질문2] 추가 고려사항이 있나요?

**✅ 이 계획대로 진행해도 될까요?**
```

### 2. **명확한 승인 포인트**
다음 시점에서 반드시 사용자 승인 대기:
- 작업 계획 수립 후: "이 계획대로 진행해도 될까요? ✔️"
- 중요 변경 전: "이 파일을 수정해도 될까요? ✔️"
- 파괴적 작업 전: "⚠️ 주의: [작업 내용]. 정말 진행할까요? ✔️"
- 각 단계 완료 후: "다음 단계로 진행할까요? ✔️"

### 3. **모호함 해결 프로세스**
불명확한 부분 발견 시:

```markdown
## ❓ 추가 확인 필요

현재 상황에서 다음 사항이 불명확합니다:

1. **[모호한 부분 1]**
   - 현재 이해: [내 이해]
   - 옵션 A: [설명]
   - 옵션 B: [설명]
   - **어떤 방식을 선호하시나요?**

2. **[모호한 부분 2]**
   - 예시가 필요합니다
   - 구체적으로: [질문]

답변 주시면 더 정확한 작업이 가능합니다.
```

## 🗂️ 프로젝트 구조

### 폴더 구조
```
ai-coding-brain-mcp/
├── python/
│   ├── ai_helpers_new/      # AI Helpers v2.0
│   │   ├── __init__.py      # 모든 함수 export
│   │   ├── file.py          # 파일 작업
│   │   ├── code.py          # 코드 분석/수정
│   │   ├── search.py        # 검색 기능
│   │   ├── llm.py           # o3 백그라운드 실행
│   │   ├── git.py           # Git 작업
│   │   ├── project.py       # 프로젝트 관리
│   │   └── util.py          # 유틸리티
│   └── json_repl_session.py # 개선된 import 시스템
├── backup/                  # 모든 백업 파일
├── llm/                     # o3 분석 결과 및 AI 답변
├── test/                    # 테스트 파일들
├── src/                     # TypeScript 소스
├── docs/                    # 문서
└── workflow.json            # 워크플로우 상태
```

### 파일 관리 규칙
1. **백업**: 중요 변경 시 `backup/` 폴더에 타임스탬프와 함께 저장
2. **o3 결과**: 모든 o3 분석은 `llm/` 폴더에 체계적으로 저장
3. **테스트**: 테스트 파일은 `test/` 폴더로 이동
4. **정리**: 주기적으로 오래된 파일 정리

## 🔧 AI Helpers v2.0 - 실제 구현 API

### 핵심 원칙
**"명확성과 단순함"** - 오버엔지니어링 제거, REPL 효율성, 일관된 패턴

### 통일된 반환값 패턴
```python
# 모든 함수가 dict 반환
{'ok': True, 'data': 결과, ...메타정보}  # 성공
{'ok': False, 'error': '에러 메시지'}     # 실패

# 헬퍼 함수
is_ok(result)      # 성공 여부 확인
get_data(result)   # 데이터 추출
get_error(result)  # 에러 메시지
```

### 사용 예시
```python
import ai_helpers_new as h

# 파일 작업
content = h.read('file.py')['data']
h.write('output.py', content)
h.append('log.txt', 'new line\n')

# JSON
data = h.read_json('config.json')['data']
h.write_json('output.json', data)

# 코드 분석
info = h.parse('module.py')
if info['ok']:
    functions = info['data']['functions']
    classes = info['data']['classes']

# 코드 수정
h.replace('file.py', 'old', 'new')
h.view('file.py', 'function_name')

# 검색
results = h.search_code('pattern', '.')
files = h.search_files('*.py', '.')

# Git
status = h.git_status()
h.git_add(['file1.py', 'file2.py'])
h.git_commit('변경사항 커밋')
h.git_log(limit=10)

# 에러 처리
result = h.read('missing.txt')
if not h.is_ok(result):
    print(h.get_error(result))
```

## 🤖 o3 백그라운드 실행 가이드

### 핵심 개념
**"o3가 생각하는 동안 우리도 일한다"** - 비차단 실행으로 생산성 극대화

### 🎯 효과적인 o3 활용 패턴

#### 1. **병렬 분석 패턴** (가장 효율적) ⭐
```python
# 독립적인 분석 작업들을 동시에 실행
tasks = {}

# 아키텍처 분석
tasks['architecture'] = h.ask_o3_async(
    "전체 아키텍처 분석 및 개선점",
    context=architecture_context,
    reasoning_effort="high"
)['data']

# 보안 분석
tasks['security'] = h.ask_o3_async(
    "보안 취약점 분석",
    context=security_context,
    reasoning_effort="medium"
)['data']

# o3가 분석하는 동안 기본 작업 수행
print("🔧 기본 정리 작업 시작...")
# - 파일 정리
# - 통계 수집
# - 문서 업데이트

# 완료된 작업부터 처리
completed = []
while len(completed) < len(tasks):
    for name, task_id in tasks.items():
        if name not in completed:
            status = h.check_o3_status(task_id)
            if status['ok'] and status['data']['status'] == 'completed':
                result = h.get_o3_result(task_id)
                h.write(f'llm/{name}_analysis.md', result['data']['answer'])
                completed.append(name)
                print(f"✅ {name} 완료")
    time.sleep(2)
```

#### 2. **파이프라인 패턴** (단계별 처리)
```python
# 1단계: 현황 분석
analysis_task = h.ask_o3_async(
    "현재 코드 구조 분석",
    context=code_context,
    reasoning_effort="high"
)['data']

# 분석 중 데이터 준비
prepare_additional_data()

# 분석 완료 대기
while h.check_o3_status(analysis_task)['data']['status'] == 'running':
    h.show_o3_progress()
    time.sleep(3)

# 2단계: 분석 결과 기반 설계
analysis_result = h.get_o3_result(analysis_task)['data']['answer']
design_task = h.ask_o3_async(
    f"다음 분석을 바탕으로 개선 설계: {analysis_result[:1000]}",
    reasoning_effort="high"
)['data']
```

### 📊 o3 활용 최적화 팁

#### reasoning_effort 설정 가이드
- **"low"** (~15초): 간단한 질문, 빠른 피드백 필요 시
- **"medium"** (~25-55초): 일반적인 분석, 균형잡힌 선택
- **"high"** (~60초+): 복잡한 문제, 심층 분석 필요 시

#### 컨텍스트 준비
```python
# 효과적인 컨텍스트 제공
context = h.prepare_o3_context(
    "버그 수정",
    ["error.log", "problematic_code.py", "test_results.json"]
)
```

## 📋 작업 수행 정확한 순서

### 1. 작업 시작 전 체크리스트
□ 현재 프로젝트 확인: `h.get_current_project()`
□ 워크플로우 상태: `wf("/status")`
□ o3 작업 현황: `h.show_o3_progress()`
□ 복잡도 평가 → o3 병렬 처리 계획
□ 관련 파일 백업: `backup/` 폴더에 저장

### 2. o3 활용 의사결정 트리
```
작업 복잡도 평가
├─ 단순 작업 (5분 이내)
│   └─ 직접 수행 (o3 불필요)
├─ 중간 복잡도 (5-30분)
│   └─ 단일 o3 작업 (medium effort)
└─ 높은 복잡도 (30분+)
    └─ 병렬 o3 작업 (작업 분할)
```

## 🛠️ execute_code 최적화 가이드

### 실행 패턴
```python
# #0 작업 분석 및 계획
print("="*50)
print("📋 작업 분석")
print("="*50)

# 현재 코드를 변수에 저장
content = h.read("target_file.py")['data']
functions = h.parse("target_file.py")['data']['functions']

# 문제점 분석
print("🔍 발견된 문제:")
# 구체적 분석...

# 복잡하면 o3 백그라운드 상담
if is_complex:
    context = h.prepare_o3_context("문제 해결", ["target_file.py"])
    o3_task = h.ask_o3_async(f"문제: {issue}", context=context)['data']

    # o3가 분석하는 동안 다른 작업
    # #1, #2, #3으로 단계별 실행
```

## 📁 프로젝트 관리

### 프로젝트 전환 (바탕화면 전용)
```python
# 바탕화면에서 프로젝트 찾기
fp("project-name")

# 현재 프로젝트 확인
current = h.get_current_project()
```

### 프로젝트 구조 분석
```python
# 구조 분석
structure = h.scan_directory_dict(".", max_depth=3)

# 프로젝트 생성
h.create_project_structure("new_project", "python")
```

## 💡 도구 사용 우선순위

### 1단계: execute_code (기본)
- 대부분의 작업은 execute_code로 처리
- ai_helpers_new 함수로 파일/Git/검색 작업
- 코드는 변수에 저장하여 관리

### 2단계: o3 백그라운드 상담 (복잡한 작업)
- ask_o3_async로 백그라운드 실행
- 다른 작업 진행하면서 상태 확인
- 완료되면 결과 수집 → llm/ 폴더에 저장

### 3단계: 기타 도구
- desktop-commander: 시스템 명령
- perplexity: 기술 문서 검색
- web_search: 최신 정보 검색

## 🔄 워크플로우 시스템

### 실제 사용 가능한 명령어
```bash
/status              # 상태 확인
/task add [이름]     # 태스크 추가
/task list          # 태스크 목록
/start [id]         # 태스크 시작
/complete [id] [요약] # 태스크 완료
/report             # 전체 리포트
/help               # 도움말
```

### /flow 명령 처리 (간소화)
`/flow` 명령 실행 시 다음만 표시:
1. 워크플로우 상태 (진행률)
2. 현재 프로젝트 이름
3. o3 작업 개수 (진행 중/완료)
4. 간단한 안내 메시지

추가 상세 정보는 사용자 요청 시에만 제공

## 📌 AI Helpers v2.0 완전한 API 참조

### 파일 작업 (file.py)
```python
h.read(path)                # 파일 읽기
h.write(path, content)      # 파일 쓰기
h.append(path, content)     # 내용 추가
h.read_json(path)           # JSON 읽기
h.write_json(path, data)    # JSON 쓰기
h.exists(path)              # 존재 확인
h.info(path)                # 파일 정보
```

### 코드 분석/수정 (code.py)
```python
h.parse(path)               # 함수/클래스 파싱
h.view(path, name)          # 특정 코드 보기
h.replace(path, old, new)   # 텍스트 교체
h.insert(path, marker, code) # 코드 삽입
h.functions(path)           # 함수 목록
h.classes(path)             # 클래스 목록
```

### 검색 (search.py)
```python
h.search_files(pattern, path)    # 파일명 검색
h.search_code(pattern, path)     # 코드 내용 검색
h.find_function(name, path)      # 함수 찾기
h.find_class(name, path)         # 클래스 찾기
h.grep(pattern, path)            # 텍스트 검색
h.find_in_file(file, pattern)    # 파일 내 검색
```

### LLM 작업 (llm.py) ⭐
```python
# 백그라운드 실행 (권장)
h.ask_o3_async(question, context, reasoning_effort)  # 작업 ID 반환
h.check_o3_status(task_id)                          # 상태 확인
h.get_o3_result(task_id)                            # 결과 가져오기
h.show_o3_progress()                                # 전체 진행 상황
h.list_o3_tasks(status_filter)                      # 작업 목록
h.clear_completed_tasks()                           # 완료 작업 정리

# 컨텍스트 준비
h.prepare_o3_context(topic, files)                  # 파일 포함 컨텍스트
```

### Git (git.py)
```python
h.git_status()              # 상태 확인
h.git_add(files)            # 스테이징
h.git_commit(message)       # 커밋
h.git_push()                # 푸시
h.git_pull()                # 풀
h.git_branch(name)          # 브랜치
h.git_current_branch()      # 현재 브랜치
h.git_log(limit)            # 로그 조회
h.git_diff(file)            # 변경사항 확인
```

### 프로젝트 (project.py)
```python
h.get_current_project()              # 현재 프로젝트
h.detect_project_type()              # 프로젝트 타입
h.scan_directory(path)               # 디렉토리 스캔
h.scan_directory_dict(path, depth)   # 구조화된 스캔
h.create_project_structure(name, type) # 프로젝트 생성
```

### 유틸리티 (util.py)
```python
h.ok(data, **meta)          # 성공 결과 생성
h.err(msg, **meta)          # 실패 결과 생성
h.is_ok(result)             # 성공 여부
h.get_data(result)          # 데이터 추출
h.get_error(result)         # 에러 메시지
```

### 워크플로우
```python
wf(command)                 # 워크플로우 명령
# 실제 사용 가능한 명령어는 위의 워크플로우 시스템 섹션 참조
```

## 🎨 출력 형식 표준

### 단계 구분
```python
print("="*50)
print(f"🔧 #{step} {title}")
print("="*50)
```

### 진행 상황
```python
print(f"⏳ 진행중: {current}/{total} ({percent}%)")
```

### o3 백그라운드 작업 표시
```python
print("🤖 o3 백그라운드 분석 시작...")
task_id = h.ask_o3_async(question, context)['data']
print(f"📊 작업 ID: {task_id}")
print("💡 다른 작업을 진행하세요. 상태 확인: h.check_o3_status(task_id)")
```

### 백업 관리
```python
print(f"🔒 백업 생성: {backup_count}개")
print(f"✅ 백업 삭제: {deleted_count}개")
```

## 🚨 응급 상황 프로토콜

### 데이터 손실 방지
1. 중요 작업 전 항상 백업 → `backup/`
2. 백업은 테스트 성공 후에만 삭제
3. Git 커밋으로 이력 관리

### 원인 불명 오류
1. 현재 코드를 변수에 저장
2. o3에게 백그라운드로 분석 요청
3. 그 동안 로그 분석 및 테스트

### REPL 재시작
```python
# 안전한 재시작
from ai_coding_brain_mcp import restart_json_repl
restart_json_repl(keep_helpers=True, reason="오류 해결")
```

## ⚠️ 주의사항

### 파일 작업
- 모든 함수가 dict 반환: `result['data']` 사용
- 대용량 파일: 청크 단위로 처리
- 인코딩: UTF-8 기본

### o3 백그라운드 작업
- 긴 작업은 항상 async 사용
- 주기적으로 상태 확인
- 완료된 작업은 정리
- 결과는 llm/ 폴더에 저장

### 메모리 관리
- 큰 파일은 변수에 저장 후 재사용
- 불필요한 변수는 del로 정리
- 완료된 o3 작업은 clear

## 🎯 목표

1. **안전하고 체계적인 개발**
2. **투명한 진행 상황 공유**
3. **재사용 가능한 작업 패턴**
4. **효율적인 도구 활용**
5. **사용자 통제권 보장**
6. **일관된 코드 품질**
7. **o3 백그라운드 실행으로 생산성 극대화**
8. **병렬 처리로 대기 시간 최소화**
9. **체계적인 파일 관리** (backup/, llm/, test/)

## 📝 v21.0 주요 변경사항

1. **미구현 기능 제거**
   - Quick 함수들 (qs, qfind 등) 제거
   - 코드 수정 권장 함수들 제거
   - safe_* 함수들 제거
   - HelperResult 패턴 제거

2. **/flow 명령 처리 간소화**
   - 간단한 상태 정보만 표시
   - 과도한 분석 제거

3. **워크플로우 명령어 수정**
   - 실제 구현과 일치하도록 수정
   - /task add, /start, /complete 등

4. **실제 API만 문서화**
   - 53개 실제 함수만 포함
   - 테스트 완료된 기능만 명시

---
*버전 21.0 - 실제 구현 기준 (2025-01-19)*
- 미구현 기능 모두 제거
- 실제 동작과 100% 일치
- /flow 명령 간소화
- 워크플로우 명령어 수정