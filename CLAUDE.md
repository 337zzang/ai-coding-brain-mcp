# 🚨 CLAUDE.md - AI Coding Brain MCP 오류 해결 가이드

> 이 문서는 프로젝트에서 자주 발생하는 오류와 해결법을 정리한 가이드입니다.
> 최종 업데이트: 2025-07-13

## 📋 목차
1. [AttributeError 해결법](#1-attributeerror-해결법)
2. [UnicodeDecodeError 해결법](#2-unicodedecodeerror-해결법)
3. [워크플로우 관련 오류](#3-워크플로우-관련-오류)
4. [파일 경로 문제](#4-파일-경로-문제)
5. [SyntaxError - f-string](#5-syntaxerror---f-string)
6. [Import 오류](#6-import-오류)
7. [helpers 모듈 사용법](#7-helpers-모듈-사용법)
8. [JSON REPL 세션 관리](#8-json-repl-세션-관리)
9. [일반적인 베스트 프랙티스](#9-일반적인-베스트-프랙티스)

---

## 1. AttributeError 해결법

### 1.1 메서드 누락 오류
```python
# ❌ 잘못된 예시
helpers.get_workflow_info()  # AttributeError: 'module' has no attribute 'get_workflow_info'
wm.get_current_plan()       # AttributeError: 'WorkflowManager' object has no attribute 'get_current_plan'

# ✅ 올바른 해결법
# 1. 사용 가능한 메서드 확인
print([attr for attr in dir(helpers) if not attr.startswith('_')])
print([attr for attr in dir(wm) if not attr.startswith('_')])

# 2. 올바른 메서드 사용
from python.workflow.manager import WorkflowManager
wm = WorkflowManager("project_name")
status = wm.get_status()  # 올바른 메서드
current_task = wm.get_current_task()  # 올바른 메서드
```

### 1.2 데이터 타입 오류
```python
# ❌ 잘못된 예시
for key, value in data['plans'].items():  # AttributeError: 'list' object has no attribute 'items'
    pass

# ✅ 올바른 해결법
# 1. 데이터 타입 확인
print(f"타입: {type(data['plans'])}")

# 2. 타입에 맞는 처리
if isinstance(data['plans'], list):
    for plan in data['plans']:
        print(plan)
elif isinstance(data['plans'], dict):
    for key, value in data['plans'].items():
        print(key, value)
```

## 2. UnicodeDecodeError 해결법

### Windows 한글 경로 문제
```python
# ❌ 문제 발생 상황
result = subprocess.run(["dir", path], capture_output=True, text=True)
# UnicodeDecodeError: 'utf-8' codec can't decode byte 0xb7...

# ✅ 해결법 1: encoding 지정
result = subprocess.run(["dir", path], capture_output=True, text=True, encoding='cp949')

# ✅ 해결법 2: Desktop Commander 사용 (권장)
# desktop-commander 도구 사용
files = list_directory(path)  # 인코딩 문제 자동 처리

# ✅ 해결법 3: 파일 읽기 시
content = helpers.read_file_safe(path)  # 안전한 읽기 메서드 사용
```

## 3. 워크플로우 관련 오류

### helpers.workflow 명령 무응답
```python
# ❌ 문제 상황
helpers.workflow("/status")  # 출력 없음
helpers.workflow("/focus 1") # 출력 없음
helpers.workflow("/list")    # 출력 없음

# ✅ 해결법 1: WorkflowManager 직접 사용
from python.workflow.manager import WorkflowManager
wm = WorkflowManager("ai-coding-brain-mcp")
status = wm.get_status()
print(status)

# ✅ 해결법 2: process_command 사용
result = wm.process_command("/status")
print(result)

# ✅ 해결법 3: 태스크 직접 제어
current_task = wm.get_current_task()
if current_task:
    wm.complete_task(current_task['id'])
```

## 4. 파일 경로 문제

### 상대 경로 vs 절대 경로
```python
# ❌ 문제가 될 수 있는 상대 경로
content = helpers.read_file("memory/workflow.json")  # 현재 디렉토리에 따라 실패 가능

# ✅ 안전한 절대 경로 사용
import os
project_path = "C:\\Users\\82106\\Desktop\\ai-coding-brain-mcp"
file_path = os.path.join(project_path, "memory", "workflow.json")
content = helpers.read_file_safe(file_path)

# ✅ 프로젝트 내 경로 조합
memory_path = os.path.join(project_path, "memory")
workflow_path = os.path.join(memory_path, "workflow.json")
```

## 5. SyntaxError - f-string

### f-string 내부 특수문자 문제
```python
# ❌ 문제 발생
content = f"# 제목 {value}"  # SyntaxError: f-string expression part cannot include '#'

# ✅ 해결법 1: 일반 문자열 포맷팅
content = "# 제목 {}".format(value)

# ✅ 해결법 2: 문자열 연결
content = "# 제목 " + str(value)

# ✅ 해결법 3: 변수 분리
prefix = "# 제목"
content = f"{prefix} {value}"
```

## 6. Import 오류

### 모듈 찾기 실패 해결
```python
# ❌ 문제 상황
from python.workflow.dispatcher import execute_workflow_command
# ModuleNotFoundError: No module named 'python.workflow.dispatcher'

# ✅ 해결법 1: 올바른 import 경로 사용
from python.workflow.manager import WorkflowManager
from python.workflow.engine import WorkflowEngine

# ✅ 해결법 2: sys.path 추가
import sys
import os
project_path = "C:\\Users\\82106\\Desktop\\ai-coding-brain-mcp"
sys.path.append(project_path)

# ✅ 해결법 3: __init__.py 확인
# 각 디렉토리에 __init__.py 파일이 있는지 확인
```

## 7. helpers 모듈 사용법

### 올바른 helpers 패턴 (v48+)
```python
# 파일 읽기
content = helpers.read_file_safe(path)      # 안전한 읽기 (권장)
lines = helpers.read_file_lines(path)       # 라인 단위 읽기
data = helpers.read_file(path).get_data({}).get('content', '')  # 레거시 방식

# 디렉토리 스캔
scan_result = helpers.scan_directory(path)
files = scan_result.get_data({}).get('files', [])
dirs = scan_result.get_data({}).get('directories', [])

# Git 상태
status = helpers.git_status()  # 직접 dict 반환

# 컨텍스트 업데이트 (중요!)
# ❌ 잘못된 방식
helpers.update_context({"key": "value"})    # 딕셔너리 전달 X

# ✅ 올바른 방식
helpers.update_context("key", "value")      # 키, 값 별도 전달
# 여러 값 업데이트
updates = {"key1": "value1", "key2": "value2"}
for key, value in updates.items():
    helpers.update_context(key, value)
```

## 8. JSON REPL 세션 관리

### 세션 상태 이해
```python
# execute_code 실행 결과 구조
result = {
    "success": true,
    "stdout": "출력 내용",
    "stderr": "에러 내용",
    "variable_count": 45,  # 현재 세션의 변수 개수
    "note": "JSON REPL Session - Variables persist between executions"
}

# 세션 초기화가 필요한 경우
if result['variable_count'] > 100:  # 변수가 너무 많아진 경우
    restart_json_repl()  # 세션 재시작
    
# 특정 변수만 유지하며 재시작
restart_json_repl(keep_helpers=True)  # helpers는 유지
```

## 9. 일반적인 베스트 프랙티스

### 9.1 오류 처리 체크리스트
```python
# 1. 항상 try-except 사용
try:
    result = risky_operation()
except Exception as e:
    print(f"오류 발생: {type(e).__name__}: {e}")
    # 기본값 또는 대체 로직

# 2. 타입 확인
if not isinstance(data, dict):
    data = {}

# 3. 파일 존재 확인
if os.path.exists(file_path):
    content = helpers.read_file_safe(file_path)
else:
    print(f"파일 없음: {file_path}")
    content = ""

# 4. JSON 안전 처리
try:
    data = json.loads(content)
except json.JSONDecodeError:
    data = {}
```

### 9.2 디버깅 팁
```python
# 사용 가능한 속성/메서드 확인
print("=== 사용 가능한 메서드 ===")
print([attr for attr in dir(obj) if not attr.startswith('_')])

# 타입과 구조 확인
print(f"타입: {type(data)}")
print(f"키: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")

# 경로 디버깅
print(f"절대 경로: {os.path.abspath(path)}")
print(f"존재 여부: {os.path.exists(path)}")
print(f"현재 디렉토리: {os.getcwd()}")
```

### 9.3 워크플로우 디버깅
```python
# 워크플로우 상태 완전 확인
from python.workflow.manager import WorkflowManager
wm = WorkflowManager("ai-coding-brain-mcp")

# 상태 확인
status = wm.get_status()
print(f"워크플로우 상태: {status}")

# 직접 파일 확인
workflow_file = os.path.join(project_path, "memory", "workflow.json")
if os.path.exists(workflow_file):
    content = helpers.read_file_safe(workflow_file)
    data = json.loads(content) if content else {}
    print(f"플랜 수: {len(data.get('plans', []))}")
```

---

## 📝 업데이트 이력
- 2025-07-13: 초기 버전 작성 (9가지 주요 오류 패턴 및 해결법 정리)

## 🔗 관련 문서
- [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md) - 프로젝트 구조 및 상태
- [README.md](./README.md) - 프로젝트 개요
- [API_REFERENCE.md](./API_REFERENCE.md) - API 문서 (작성 예정)