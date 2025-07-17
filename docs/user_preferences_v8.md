# AI Coding Brain MCP - 유저 프리퍼런스 v8

## 🚨 중요 변경사항 (v8)

### Deprecated 함수 안내
다음 함수들은 deprecated되었습니다. 대체 함수를 사용하세요:
- ❌ `search_in_files()` → ✅ `search_code()`
- ❌ `flow_project()` → ✅ `fp()`
- ❌ `ez_parse()` → ✅ `parse_file()`
- ❌ `explain_error()` → ✅ `ask_o3()`
- ❌ `generate_docstring()` → ✅ `ask_o3()` 또는 직접 작성

## 🎯 execute_code 최적화 가이드

### 🔄 연속 실행 패턴 (Sequential Execution Pattern)
execute_code 사용 시 항상 작은 단위로 나누어 순차적으로 실행하세요:

```python
#1 초기 설정 및 데이터 로드
#2 데이터 탐색 및 분석
#3 결과 검증 및 저장
```

각 단계는 다음 원칙을 따릅니다:
- 한 번에 하나의 목적만 수행
- 이전 단계의 변수를 활용
- 결과를 즉시 확인하고 다음 단계 결정

### 📝 코드 작성 템플릿

#### 단계별 실행 템플릿
```python
# #1 초기화 및 설정
print("🔧 #1 초기화 단계")
# 필요한 import
# 기본 변수 설정
# 결과 출력

# #2 데이터 처리
print("\n📊 #2 데이터 처리")
# 이전 변수 활용
# 처리 로직
# 중간 결과 확인

# #3 결과 저장
print("\n💾 #3 결과 저장")
# 최종 처리
# 저장 또는 출력
# 다음 작업 준비
```

## 🔧 핵심 헬퍼 함수 가이드 (v8 업데이트)

### 📁 파일 작업
```python
# 읽기/쓰기
content = helpers.read_file('file.py')
helpers.write_file('file.py', content)
helpers.create_file('new.py', '# 새 파일')
helpers.append_to_file('log.txt', '추가 내용')

# 파일 존재 확인
if helpers.file_exists('config.json'):
    config = helpers.read_json('config.json')
```

### 🔍 검색 작업
```python
# 파일명 검색
files = helpers.search_files('.', '*.py')

# 코드 내용 검색 (search_in_files 대신 사용!)
matches = helpers.search_code('.', 'def function')
matches = helpers.search_code('./src', 'TODO|FIXME')  # 정규식 지원
```

### 📦 Git 작업
```python
# 상태 확인
status = helpers.git_status()
# 반환값: {'success': bool, 'modified': list, 'untracked': list, 'staged': list, 'clean': bool}

# 기본 작업
helpers.git_add('.')
helpers.git_commit('feat: 새 기능')
helpers.git_push()

# 브랜치 작업
helpers.git_branch('feature/new-feature')
```

### 🔧 코드 수정
```python
# 안전한 블록 교체 (권장)
helpers.replace_block('file.py', old_code, new_code)

# 함수 전체 교체
helpers.replace_function('file.py', 'func_name', new_code)

# 클래스 메서드 교체
helpers.replace_method('file.py', 'ClassName', 'method_name', new_code)
```

### 📂 프로젝트 관리
```python
# 프로젝트 전환 (flow_project 대신!)
fp('프로젝트명')

# 현재 프로젝트 확인
current = helpers.get_current_project()

# 워크플로우 명령
helpers.workflow('/start 새 작업')
helpers.workflow('/status')
helpers.workflow('/complete')
```

### 🤖 AI 도우미
```python
# 코드 설명 (explain_error 대체)
result = helpers.ask_o3("이 에러를 해결하는 방법: " + error_msg)

# 문서 생성 (generate_docstring 대체)
result = helpers.ask_o3("다음 함수에 docstring 작성: " + code)

# 일반 질문
result = helpers.ask_o3("Python에서 데코레이터는 어떻게 작동하나요?")
```

### 📊 코드 분석
```python
# 파일 구조 분석 (ez_parse 대신!)
parsed = helpers.parse_file('module.py')
# 반환값: 함수, 클래스, 메서드 정보

# 디렉토리 스캔
files = helpers.scan_directory('./src')
```

## 💡 q함수 빠른 참조

q함수는 즉시 출력이 필요할 때 사용:

```python
# 파일 내용 즉시 출력
qf('config.py')

# 검색 결과 즉시 출력
qs('TODO')

# Git 상태 즉시 확인
qg()

# 빠른 커밋
qc('fix: 버그 수정')

# 커밋 + push
qpush('feat: 새 기능')

# 프로젝트 정보/전환
qproj()  # 현재 프로젝트
qproj('새프로젝트')  # 전환
```

## 🆕 워크플로우 명령어 (v8)

### 프로젝트 관리
```python
# 프로젝트 전환 (읽기 전용)
fp("프로젝트명")  # 또는
helpers.workflow('/flow 프로젝트명')

# 프로젝트 분석 (구조만)
helpers.workflow('/a')
```

### 작업 관리
```python
# 워크플로우 시작
helpers.workflow("/start 작업명")

# 태스크 추가
helpers.workflow("/task 할 일")

# 상태 확인
helpers.workflow("/status")

# 완료
helpers.workflow("/complete")
```

## 🚀 권장 작업 패턴

### 1. 프로젝트 시작 패턴
```python
# 프로젝트 전환
fp('my-project')

# 구조 분석 (필요시)
helpers.workflow('/a')

# 워크플로우 시작
helpers.workflow('/start 기능 구현')

# Git 상태 확인
status = helpers.git_status()
if status['modified']:
    print(f"수정된 파일: {len(status['modified'])}개")
```

### 2. 코드 수정 패턴
```python
# 백업
helpers.git_commit('backup: 수정 전')

# 파일 분석
parsed = helpers.parse_file('target.py')

# 수정
helpers.replace_function('target.py', 'old_func', new_implementation)

# 검증
content = helpers.read_file('target.py')
if 'expected_code' in content:
    print("✅ 수정 성공")
    helpers.git_commit('feat: 함수 개선')
```

### 3. 검색 및 일괄 수정 패턴
```python
# deprecated 함수 찾기
results = helpers.search_code('.', 'search_in_files')

# 각 파일 수정
for result in results:
    filepath = result['file']
    helpers.replace_block(
        filepath,
        'search_in_files',
        'search_code'
    )

# 결과 커밋
helpers.git_commit('refactor: deprecated 함수 교체')
```

## ⚠️ 주의사항 및 팁

### 피해야 할 패턴
```python
# ❌ 잘못된 예
helpers.search_in_files(...)  # deprecated!
helpers.flow_project(...)     # deprecated!
helpers.ez_parse(...)         # deprecated!

# ✅ 올바른 예
helpers.search_code(...)
fp(...)
helpers.parse_file(...)
```

### 성능 최적화
1. 대량 검색은 디렉토리 범위 제한: `search_code('./src', pattern)`
2. 큰 파일은 단계별 처리: `read_file` → 처리 → `write_file`
3. Git 작업은 의미 있는 단위로 묶어서 커밋

### 디버깅 팁
```python
# 함수 존재 여부 확인
if hasattr(helpers, 'function_name'):
    helpers.function_name()
else:
    print("함수가 없습니다")

# 반환값 구조 확인
result = helpers.some_function()
print(f"타입: {type(result)}")
if isinstance(result, dict):
    print(f"키: {list(result.keys())}")
```

## 📌 요약 - 꼭 기억할 것들

### v8에서 변경된 것
1. **삭제된 함수들**: search_in_files, flow_project, ez_parse, explain_error, generate_docstring
2. **대체 함수들**: search_code, fp, parse_file, ask_o3
3. **개선된 문서**: Git 반환값 구조, 워크플로우 명령어

### 핵심 함수 15개
- **파일**: read_file, write_file, create_file, file_exists
- **검색**: search_code, search_files
- **Git**: git_status, git_commit, git_add
- **수정**: replace_block, replace_function
- **분석**: parse_file, scan_directory
- **프로젝트**: fp, workflow
- **AI**: ask_o3

### 작업 흐름
1. `fp(프로젝트)` → 프로젝트 전환
2. `workflow('/start')` → 작업 시작
3. 코드 수정 → `replace_block` 사용
4. `git_commit` → 변경사항 저장
5. `workflow('/complete')` → 작업 완료

---
업데이트: 2025-01-17 | 버전: v8