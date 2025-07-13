# 프로젝트 컨텍스트: ai-coding-brain-mcp

> 이 문서는 프로젝트의 상세 컨텍스트와 구조를 설명합니다.
> 최종 업데이트: 2025-07-13 11:31:47

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
| `docs/` | 문서 |
| `logs/` | 프로젝트 관련 파일 |
| `memory/` | 캐시 및 상태 저장 |
| `python/` | Python 스크립트 및 유틸리티 |
| `src/` | 소스 코드 |

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
├── docs/
│   ├── examples/
│   │   ├── event_bus_example.py
│   │   ├── workflow_context_bridge_example.py
│   ├── tasks/
│   └── workflow_v2/
│       ├── README.md
│   ├── event_system_analysis.json
├── logs/
│   ├── file/
│   ├── git/
│   ├── system/
│   └── workflow/
│   ├── active_ai_instruction.json
│   ├── active_errors.json
│   ├── ai_instructions.json
│   └── ... (4 more files)
├── memory/
│   ├── backup/
│   │   ├── active_backup_20250710_171855/
│   │   │   ├── context.json
│   │   │   ├── session_info.json
│   │   │   ├── task_context.json
│   │   ├── ai-coding-brain-mcp_20250704_195124/
│   │   │   ├── context.json
│   │   ├── ai-coding-brain-mcp_20250705_120052/
│   │   │   ├── context.json
│   │   │   ├── workflow_data.json
│   │   ├── legacy_final_backup_20250710_095949/
│   │   └── old_workflows/
│   │       ├── workflow_before_cleanup_20250707_155640.json
│   │   ├── context_ai-coding-brain-mcp_20250704_195124.json
│   │   ├── context_ai-coding-brain-mcp_20250705_120052.json
│   │   ├── unified_final_20250710_171104.json
│   │   └── ... (1 more files)
│   ├── backups/
│   │   └── contexts/
│   │       ├── ai-coding-brain-mcp_context_removed.json
│   ├── cache/
│   │   ├── cache_manifest.json
│   │   ├── cache_metadata.json
│   │   ├── file_directory.json
│   ├── deprecated/
│   │   ├── active_backup_20250710_180947/
│   │   │   ├── context.json
│   │   │   ├── session_info.json
│   │   │   ├── task_context.json
│   │   └── cleanup_20250710_182629/
│   │       └── active/
│   ├── projects/
│   │   ├── ai-coding-brain-mcp/
│   │   │   └── workflow_v3/
│   │   ├── project-alpha/
│   │   │   ├── context.json
│   │   │   ├── workflow.json
│   │   ├── project-beta/
│   │   │   ├── context.json
│   │   │   ├── workflow.json
│   │   └── project-gamma/
│   │       ├── context.json
│   │       ├── workflow.json
│   └── task_context_archive/
│   ├── ai_instructions.json
│   ├── ai_instructions_mcp.json
│   ├── context.json
│   └── ... (8 more files)
├── python/
│   ├── ai_helpers/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── image.py
│   │   │   ├── manager.py
│   │   │   └── ... (2 more files)
│   │   ├── removed/
│   │   └── search/
│   │       ├── __init__.py
│   │       ├── code_search.py
│   │       ├── core.py
│   │       └── ... (3 more files)
│   │   ├── __init__.py
│   │   ├── base_api.py
│   │   ├── code.py
│   │   └── ... (9 more files)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── image_generator.py
│   │   ├── public.py
│   │   └── ... (3 more files)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── cache_manager.py
│   │   ├── context_manager.py
│   │   └── ... (3 more files)
│   ├── events/
│   │   ├── __init__.py
│   │   ├── unified_event_types.py
│   ├── tracking/
│   │   ├── __init__.py
│   │   ├── simple_tracker.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── git_task_helpers.py
│   │   ├── git_utils.py
│   │   └── ... (4 more files)
│   ├── vendor/
│   │   ├── tree-sitter-javascript/
│   │   │   └── bindings/
│   │   └── tree-sitter-typescript/
│   │       └── bindings/
│   └── workflow/
│       └── v3/
│           ├── api/
│           ├── commands/
│           ├── listeners/
│           └── tests/
│           ├── __init__.py
│           ├── ai_instruction_executor.py
│           ├── code_integration.py
│           └── ... (17 more files)
│       ├── __init__.py
│   ├── __init__.py
│   ├── api_manager.py
│   ├── debug_flow.py
│   └── ... (15 more files)
└── src/
    ├── core/
    │   ├── domain/
    │   │   ├── entities/
    │   │   └── repositories/
    │   │   ├── index.ts
    │   └── infrastructure/
    │       └── filesystem/
    │       ├── index.ts
    │   ├── index.ts
    ├── handlers/
    │   ├── api-toggle-handler.ts
    │   ├── backup-handler.ts
    │   ├── build-handler.ts
    │   └── ... (4 more files)
    ├── services/
    │   ├── logger.ts
    ├── tools/
    │   ├── tool-definitions.ts
    ├── types/
    │   ├── tool-interfaces.ts
    └── utils/
        ├── hybrid-helper-system.ts
        ├── indent-helper.ts
        ├── logger.ts
        └── ... (1 more files)
    ├── index.ts
├── .ai-brain.config.json
├── .eslintrc.json
├── base_api_fixed.py
└── ... (6 more files)
```
- `.ai-brain.config.json`: AI Coding Brain 설정
- `package.json`: Node.js 프로젝트 설정
- `tsconfig.json`: TypeScript 설정
- `.env`: 환경 변수
- `.gitignore`: Git 무시 파일
- `requirements.txt`: Python 의존성

## 📊 프로젝트 통계

- **전체 파일 수**: 221개
- **디렉토리 수**: 71개
- **파일 타입 분포**:
  - `.py`: 124개 (56.1%)
  - `.json`: 49개 (22.2%)
  - `.ts`: 28개 (12.7%)
  - `.md`: 6개 (2.7%)
  - `.jsonl`: 4개 (1.8%)

## 🚀 빠른 시작

1. **프로젝트 클론**
   ```bash
   git clone [repository-url]
   cd ai-coding-brain-mcp
   ```

2. **의존성 설치**
   ```bash
   npm install
   pip install -r requirements.txt
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
