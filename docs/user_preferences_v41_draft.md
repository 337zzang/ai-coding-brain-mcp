# AI Coding Brain MCP - 유저프리퍼런스 v41.0

## 🚀 빠른 시작 가이드

### 핵심 명령어 (가장 자주 사용)
```bash
# Flow 명령어 (AI가 자동 변환)
/flow                    # 현재 상태
/flow list               # Plan 목록
/flow project my-app     # 프로젝트 전환
/flow create 새작업      # Plan 생성
/flow task add 내용      # Task 추가

# 프로젝트 분석
/a                       # 프로젝트 분석 및 문서 생성

# 웹 자동화 (v41.0 신규)
web_start()              # 브라우저 시작
web_goto("url")          # 페이지 이동
web_click("button")      # 요소 클릭
web_extract()            # 데이터 추출
web_generate_script()    # 스크립트 생성
```

### 작업 시작 템플릿
```python
# 1. 프로젝트 전환
/flow project my-project

# 2. 새 작업 생성
/flow create 기능 구현

# 3. Task 추가
/flow task add 1. 분석 및 설계
/flow task add 2. 구현
/flow task add 3. 테스트

# 4. 작업 시작
/flow task
/flow task progress task_id
```

## 🎯 핵심 작업 원칙 (3가지만 기억)

1. **설계 우선**: 모든 작업은 상세 설계 → 승인 → 실행
2. **TODO 단위 실행**: Task를 5-7개 TODO로 분할하여 순차 실행
3. **오류 즉시 대응**: 실패 시 자동 복구 모드 전환

## 📁 프로젝트 구조

모든 프로젝트는 **바탕화면**에 위치:
```
C:\Users\{username}\Desktop\
├── project-1\
├── project-2\
└── ai-coding-brain-mcp\
```

## 🔧 헬퍼 함수 카테고리

### 1. 파일 작업 (file.py)
- read, write, append, exists, read_json, write_json

### 2. 코드 분석 (code.py)
- parse, view, replace, insert, functions, classes

### 3. 검색 (search.py)
- search_files, search_code, find_function, find_class, grep

### 4. Git (git.py)
- git_status, git_add, git_commit, git_push, git_pull

### 5. 웹 자동화 (web.py) 🆕
- web_start, web_stop, web_goto, web_click, web_type
- web_screenshot, web_extract, web_wait, web_scroll
- web_get_data, web_generate_script, web_status

### 6. AI 모델 (llm.py)
- ask_o3_async (reasoning_effort: "high")

### 7. 작업 관리 (flow)
- flow 명령어 시스템, TaskLogger

## 🌐 웹 자동화 사용법 (v41.0 신규)

### 기본 워크플로우
```python
# 1. 브라우저 시작
web_start()

# 2. 페이지 이동
web_goto("https://example.com")

# 3. 요소 상호작용
web_click("button.submit")
web_type("input#search", "검색어")

# 4. 데이터 추출
data = web_extract()
table_data = web_extract_table("table.results")

# 5. 스크립트 생성 (레코딩 기반)
script = web_generate_script()

# 6. 종료
web_stop()
```

### 고급 기능
- 자동 액션 레코딩
- Playwright 스크립트 생성
- 스크린샷 및 대기 기능

## 📝 TaskLogger 사용법

### 기본 사용
```python
# 초기화
logger = h.TaskLogger(plan_id, task_num, "task_name")

# 작업 기록
logger.task_info("제목", priority="high")
logger.todo(["할일1", "할일2"])
logger.analyze("file.py", "분석 결과")
logger.code("modify", "file.py", "변경 요약")

# 오류 기록
logger.blocker("문제 설명", severity="high", solution="해결책")

# 완료
logger.complete("작업 완료")
```

## 🚨 오류 복구 프로세스

1. 오류 감지 → 자동으로 복구 모드 전환
2. 복구 계획 제시 → 사용자 승인 대기
3. 승인 후 복구 실행

## 💡 주요 개선사항 (v41.0)

1. **웹 자동화 통합**: 12개 web_* 헬퍼 함수 추가
2. **문서 간소화**: 핵심 내용만 유지, 중복 제거
3. **빠른 참조**: 자주 쓰는 명령어 최상단 배치
