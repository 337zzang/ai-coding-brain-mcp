# 파일 디렉토리 구조

> 생성일: 2025-07-25 11:03:54
> 총 파일 수: 704개
> 총 디렉토리 수: 157개

## 📂 디렉토리 트리

```
ai-coding-brain-mcp/
├── 📁 python/                          # Python 백엔드
│   ├── 📁 ai_helpers_new/             # AI 헬퍼 모듈 패키지
│   │   ├── 📄 __init__.py            # 패키지 초기화
│   │   ├── 📄 file.py                # 파일 작업 헬퍼
│   │   ├── 📄 code.py                # 코드 분석/수정 헬퍼
│   │   ├── 📄 search.py              # 검색 헬퍼
│   │   ├── 📄 git.py                 # Git 작업 헬퍼
│   │   ├── 📄 llm.py                 # LLM (o3) 통합 헬퍼
│   │   ├── 📄 project.py             # 프로젝트 관리
│   │   ├── 📄 simple_flow_commands.py # Flow 명령어 시스템
│   │   ├── 📄 ultra_simple_flow_manager.py # Plan/Task 매니저
│   │   ├── 📄 wrappers.py            # 표준화 래퍼
│   │   ├── 📁 domain/                # 도메인 모델
│   │   ├── 📁 repository/            # 저장소 계층
│   │   └── 📁 service/               # 서비스 계층
│   └── 📄 json_repl_session.py       # JSON REPL 세션 (핵심)
├── 📁 src/                            # TypeScript MCP 서버
│   ├── 📄 index.ts                   # MCP 서버 진입점
│   └── 📄 tools.ts                   # MCP 도구 정의
├── 📁 test/                           # 테스트 파일
│   ├── 📄 test_*.py                  # Python 테스트
│   └── 📄 *.test.ts                  # TypeScript 테스트
├── 📁 docs/                           # 문서
├── 📁 backups/                        # 백업 파일
├── 📁 dist/                           # 빌드 출력
├── 📁 logs/                           # 로그 파일
├── 📄 package.json                    # Node.js 프로젝트 설정
├── 📄 tsconfig.json                   # TypeScript 설정
├── 📄 .eslintrc.json                  # ESLint 설정
├── 📄 pyproject.toml                  # Python 프로젝트 설정
├── 📄 pytest.ini                      # pytest 설정
├── 📄 .gitignore                      # Git 제외 파일
├── 📄 readme.md                       # 프로젝트 문서
└── 📄 file_directory.md              # 이 문서

## 📋 파일별 상세 정보

### 🔸 python/json_repl_session.py
- **크기**: 약 10KB (400+ lines)
- **역할**: MCP와 Python 실행 환경을 연결하는 핵심 세션 관리자
- **주요 기능**:
  - JSON-RPC 프로토콜 처리
  - Python 코드 실행 및 결과 반환
  - AI Helpers 자동 로드
  - 영속적 변수 관리
  - 에러 처리 및 보고

### 🔸 python/ai_helpers_new/__init__.py
- **역할**: AI Helpers 패키지 초기화 및 공개 API 정의
- **내보내는 주요 컴포넌트**:
  - Plan, Task, TaskStatus (도메인 모델)
  - UltraSimpleFlowManager
  - flow, wf 명령어 함수
  - 모든 헬퍼 함수들 (file, code, search, git, llm 등)

### 🔸 Python 헬퍼 모듈 분석
  - __init__.py: 1개 함수, 0개 클래스
  - project.py: 11개 함수, 0개 클래스
  - simple_flow_commands.py: 13개 함수, 0개 클래스
  - ultra_simple_flow_manager.py: 0개 함수, 1개 클래스
  - wrappers.py: 3개 함수, 0개 클래스

### 🔸 src/index.ts
- **역할**: MCP 서버 메인 진입점
- **주요 기능**:
  - MCP 프로토콜 구현
  - Python REPL 세션 관리
  - 도구 등록 및 라우팅
  - 에러 처리

### 🔸 package.json
- **프로젝트명**: ai-coding-brain-mcp
- **버전**: 4.2.0
- **주요 스크립트**:
  - `build`: TypeScript 컴파일
  - `start`: MCP 서버 시작
  - `test`: 테스트 실행

## 🔗 모듈 의존성

```
┌─────────────────────────┐
│     MCP Client (AI)     │
└───────────┬─────────────┘
            │ JSON-RPC
┌───────────▼─────────────┐
│    src/index.ts         │
│    (MCP Server)         │
└───────────┬─────────────┘
            │ Process
┌───────────▼─────────────┐
│ json_repl_session.py    │
│   (Python REPL)         │
└───────────┬─────────────┘
            │ Import
┌───────────▼─────────────┐
│   ai_helpers_new/*      │
│  (Helper Functions)     │
└─────────────────────────┘
```

## 📊 코드 통계

| 파일 유형 | 파일 수 | 설명 |
|----------|---------|------|
| Python (.py) | 122 | 백엔드 로직 |
| TypeScript (.ts) | 54 | MCP 서버 |
| Markdown (.md) | 246 | 문서 |
| JSON (.json) | 166 | 설정 파일 |

## 🔍 주요 패턴 및 규칙

### 명명 규칙
- **파일명**: snake_case (예: json_repl_session.py)
- **클래스명**: PascalCase (예: UltraSimpleFlowManager)
- **함수명**: snake_case (예: get_current_project)
- **상수**: UPPER_SNAKE_CASE (예: HELPERS_AVAILABLE)

### 응답 형식
모든 헬퍼 함수는 일관된 딕셔너리 형식 반환:
```python
{'ok': bool, 'data': Any, 'error': Optional[str], ...metadata}
```

### 프로젝트 규칙
- 모든 Python 모듈은 `__init__.py` 포함
- 테스트 파일은 `test_` 접두사 사용
- 백업 파일은 `.backup_{timestamp}` 형식
- Flow 상태는 `.ai-brain/` 폴더에 저장
