# 프로젝트 컨텍스트: ai-coding-brain-mcp

> 이 문서는 프로젝트의 상세 컨텍스트와 구조를 설명합니다.
> 최종 업데이트: 2025-07-14 23:29:53

## 🎯 프로젝트 개요

**프로젝트명**: ai-coding-brain-mcp  
**설명**: 통합 AI 코딩 브레인 MCP - Memory Bank, Desktop Commander, Notebook, Claude Memory 통합  
**버전**: 1.0.0  
**주요 언어**: TypeScript/JavaScript

## 🏗️ 아키텍처

### 기술 스택
- **백엔드/스크립트**: Python
- **프론트엔드/서버**: TypeScript
- **스크립트**: JavaScript

### 주요 디렉토리 구조

| 디렉토리 | 설명 |
|---------|------|
| `.pytest_cache/` | 프로젝트 관련 파일 |
| `backup_deleted_modules/` | 프로젝트 관련 파일 |
| `backup_workflow_20250713_114703/` | 프로젝트 관련 파일 |
| `backup_workflow_cleanup_20250714_090616/` | 프로젝트 관련 파일 |
| `backup_workflow_legacy_20250713/` | 프로젝트 관련 파일 |
| `docs/` | 문서 |
| `examples/` | 프로젝트 관련 파일 |
| `generated_scripts/` | 프로젝트 관련 파일 |
| `logs/` | 프로젝트 관련 파일 |
| `memory/` | 캐시 및 상태 저장 |

## 📦 의존성

### 주요 의존성
- `@modelcontextprotocol/sdk`: ^1.8.0
- `async-lock`: ^1.4.1
- `chalk`: ^4.1.2
- `fs-extra`: ^11.2.0
- `uuid`: ^9.0.1
- `winston`: ^3.11.0
- `@types/fs-extra`: ^11.0.4
- `@types/jest`: ^29.5.8
- `@types/node`: ^20.17.51
- `@types/uuid`: ^9.0.7
- `@typescript-eslint/eslint-plugin`: ^6.14.0
- `@typescript-eslint/parser`: ^6.14.0
- `esbuild-register`: ^3.6.0
- `eslint`: ^8.55.0
- `jest`: ^29.7.0
- ... 외 4개

## 🔧 설정 파일

### 주요 설정 파일 목록

## 📂 디렉토리 트리 구조

```
ai-coding-brain-mcp/
├── .pytest_cache/
│   ├── README.md
├── backup_deleted_modules/
│   ├── events_backup_20250713_105544/
│   │   ├── enhanced_event_bus.py
│   │   ├── event_bus.py
│   │   ├── event_bus_events.py
│   │   └── ... (3 more files)
│   ├── hooks_backup_20250713_110813/
│   │   ├── git-security.js
│   │   ├── git-tracker.js
│   │   ├── mcp-context-manager.js
│   └── workflow_logging_backup_20250713_111213/
│       └── workflow_logging/
│           ├── __init__.py
│           ├── decorators.py
│           ├── logger.py
│   ├── build.py
│   ├── code_unified.py
│   ├── compile.py
│   └── ... (4 more files)
├── backup_workflow_20250713_114703/
│   └── v3/
│       ├── api/
│       │   ├── __init__.py
│       │   ├── decorators.py
│       │   ├── internal_api.py
│       │   └── ... (1 more files)
│       ├── commands/
│       │   ├── __init__.py
│       │   ├── auto_executor.py
│       ├── listeners/
│       │   ├── __init__.py
│       │   ├── ai_instruction_base.py
│       │   ├── automation_listeners.py
│       │   └── ... (11 more files)
│       └── tests/
│           ├── test_event_publishing.py
│       ├── __init__.py
│       ├── ai_instruction_executor.py
│       ├── code_integration.py
│       └── ... (17 more files)
│   ├── __init__.py
├── backup_workflow_cleanup_20250714_090616/
│   └── projects_backup/
│       └── ai-coding-brain-mcp/
│           └── workflow_data/
│   ├── workflow_ai_state.json
│   ├── workflow_backup_20250714_070008.json
├── backup_workflow_legacy_20250713/
│   └── python/
│       └── workflow/
│           ├── ai_automation/
│           ├── core/
│           └── messaging/
│           ├── errors.py
│           ├── manager.py
├── docs/
│   ├── design/
│   │   ├── python_helpers_validation_task03_code_analysis_design_20250714.md
│   ├── error/
│   ├── report/
│   │   ├── git_add_error_fix_report_20250714.md
│   │   ├── git_module_cleanup_report_20250714.md
│   │   ├── system_efficiency_evaluation_20250714.md
│   ├── tasks/
│   │   ├── 20250713_task_1b12e231.md
│   │   ├── 20250713_task_21dfb9f3.md
│   │   ├── 20250713_task_23799501.md
│   │   └── ... (9 more files)
│   └── workflow_reports/
│       ├── ai-coding-brain-mcp_commands_implementation_report_20250714_004244.md
│       ├── ai-coding-brain-mcp_error_analysis_20250714_003640.md
│       ├── ai-coding-brain-mcp_filesystem_test_report_20250714.md
│       └── ... (9 more files)
│   ├── AI_HELPERS_GUIDE.md
│   ├── event_system_analysis.json
│   ├── execute_code_advanced_guide.md
│   └── ... (23 more files)
├── examples/
│   ├── test_async_web.py
│   ├── web_automation_recording_examples.py
├── generated_scripts/
│   ├── naver_allstar_search_manual.py
│   ├── naver_simple.py
│   ├── README.md
│   └── ... (2 more files)
└── ... (6 more directories)
├── .ai-brain.config.json
├── .eslintrc.json
├── ai-coding-brain-mcp_7490a912_design_v2.md
└── ... (9 more files)
```
- `.ai-brain.config.json`: AI Coding Brain 설정
- `package.json`: Node.js 프로젝트 설정
- `tsconfig.json`: TypeScript 설정
- `.env`: 환경 변수
- `.gitignore`: Git 무시 파일

## 📊 프로젝트 통계

- **전체 파일 수**: 312개
- **디렉토리 수**: 80개
- **파일 타입 분포**:
  - `.py`: 161개 (51.6%)
  - `.md`: 66개 (21.2%)
  - `.json`: 35개 (11.2%)
  - `.ts`: 28개 (9.0%)
  - `.png`: 4개 (1.3%)

## 🚀 빠른 시작

1. **프로젝트 클론**
   ```bash
   git clone [repository-url]
   cd ai-coding-brain-mcp
   ```

2. **의존성 설치**
   ```bash
   npm install
   ```

3. **환경 설정**
   - `.env.example`을 `.env`로 복사하고 필요한 값 설정
   - 필요한 API 키와 설정 구성

4. **실행**
   - 프로젝트별 실행 명령어 참조

## 🔍 추가 정보

- 상세한 파일 구조는 [file_directory.md](./file_directory.md) 참조
- API 문서는 [API_REFERENCE.md](./API_REFERENCE.md) 참조 (생성 예정)

---
*이 문서는 /build 명령으로 자동 생성되었습니다.*
