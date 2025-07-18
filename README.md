# AI Coding Brain MCP v3.0.0 - Simplified Edition

영속적인 Python REPL 세션을 제공하는 간소화된 MCP 서버입니다.

## 🚀 주요 특징

- **영속적 Python 세션**: 변수와 상태가 세션 전체에서 유지됩니다
- **내장 헬퍼 함수**: 파일 조작, 디렉토리 스캔, 코드 검색 등의 헬퍼 제공
- **간소화된 구조**: 핵심 기능만 유지하여 안정성과 성능 향상


## 🎯 워크플로우 명령어

프로젝트 작업을 체계적으로 관리하는 6개의 명령어가 추가되었습니다:

### 1. `/start [프로젝트명]`
새 프로젝트를 시작합니다.
```python
workflow("/start AI 도구 개발")
# ✅ 'AI 도구 개발' 시작됨
```

### 2. `/plan [단계1] [단계2] ...`
작업 단계를 설정하거나 조회합니다.
```python
workflow("/plan")                    # 현재 단계 조회
workflow("/plan 기획 개발 테스트")   # 단계 설정
```

### 3. `/task [add|list|del]`
작업을 관리합니다.
```python
workflow("/task add API 설계")       # 작업 추가
workflow("/task list")               # 작업 목록
workflow("/task del 1")              # 1번 작업 삭제
```

### 4. `/next`
다음 작업을 진행 상태로 변경합니다.
```python
workflow("/next")
# ▶️ 진행: API 설계
```

### 5. `/status`
프로젝트 현황을 확인합니다.
```python
workflow("/status")
# 📊 AI 도구 개발
# 작업: 3개 (완료: 1개)
# 진행률: 33%
```

### 6. `/focus [내용]`
현재 집중할 사항을 설정합니다.
```python
workflow("/focus 성능 최적화")       # 포커스 설정
workflow("/focus")                   # 현재 포커스 확인
```

## 📦 설치

```bash
npm install
npm run build
```

## 🛠️ 제공 도구

### 1. execute_code
Python 코드를 실행합니다. 세션 간 변수가 유지되며, 다양한 헬퍼 함수를 사용할 수 있습니다.

**사용 가능한 helpers 메서드:**
- `helpers.scan_directory_dict(path)` - 디렉토리 스캔
- `helpers.read_file(path)` - 파일 읽기
- `helpers.create_file(path, content)` - 파일 생성/수정
- `helpers.search_files_advanced(path, pattern)` - 파일명 검색
- `helpers.search_code_content(path, pattern, file_pattern)` - 코드 내용 검색
- `helpers.replace_block(file, target, new_code)` - 코드 블록 교체

### 2. restart_json_repl
JSON REPL 세션을 재시작합니다. `keep_helpers=True`(기본값)로 헬퍼를 유지할 수 있습니다.

## 📝 사용 예시

```python
# 디렉토리 구조 파악
files = helpers.scan_directory_dict(".")
print(f"파일: {len(files['files'])}개")

# 파일 읽기/쓰기
content = helpers.read_file("config.json")
helpers.create_file("output.txt", content)

# 코드 검색
results = helpers.search_code_content("src", "function", "*.ts")
```

## 🏗️ 프로젝트 구조

```
ai-coding-brain-mcp/
├── src/
│   ├── handlers/
│   │   └── execute-code-handler.ts  # 핵심 실행 핸들러
│   ├── tools/
│   │   └── tool-definitions.ts      # 도구 정의
│   └── index.ts                     # 메인 서버
├── python/
│   ├── json_repl_session.py        # Python REPL 세션
│   └── helpers_wrapper.py          # 헬퍼 함수들
└── package.json
```

## 📄 라이선스

MIT

## 🔄 변경 이력

### v3.0.0 (2025-07-15)
- 코드베이스 대폭 간소화
- 불필요한 핸들러 6개 제거
- Python 관련 파일 5개 제거
- 핵심 기능 2개만 유지 (execute_code, restart_json_repl)
- 안정성과 성능 향상
