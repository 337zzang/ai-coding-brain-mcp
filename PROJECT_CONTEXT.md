# 프로젝트 컨텍스트: ai-coding-brain-mcp

> 이 문서는 프로젝트의 상세 컨텍스트와 구조를 설명합니다.
> 최종 업데이트: 2025-07-12 21:30:58

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
| `.vscode/` | 프로젝트 관련 파일 |
| `backup/` | 프로젝트 관련 파일 |
| `backups/` | 프로젝트 관련 파일 |
| `docs/` | 문서 |
| `logs/` | 프로젝트 관련 파일 |
| `memory/` | 캐시 및 상태 저장 |
| `python/` | Python 스크립트 및 유틸리티 |
| `scripts/` | 유틸리티 스크립트 |
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
│   └── v/
│       └── cache/
│   ├── README.md
├── .vscode/
│   ├── settings.json
├── backup/
│   ├── dist_backup_20250706_165604/
│   │   ├── core/
│   │   │   ├── domain/
│   │   │   └── infrastructure/
│   │   │   ├── index.d.ts
│   │   │   ├── index.js
│   │   ├── handlers/
│   │   │   ├── api-toggle-handler.d.ts
│   │   │   ├── api-toggle-handler.js
│   │   │   ├── backup-handler.d.ts
│   │   │   └── ... (13 more files)
│   │   ├── memory/
│   │   │   ├── config.d.ts
│   │   │   ├── config.js
│   │   ├── services/
│   │   │   ├── logger.d.ts
│   │   │   ├── logger.js
│   │   ├── tools/
│   │   │   ├── tool-definitions.d.ts
│   │   │   ├── tool-definitions.js
│   │   ├── types/
│   │   │   ├── tool-interfaces.d.ts
│   │   │   ├── tool-interfaces.js
│   │   └── utils/
│   │       ├── hybrid-helper-system.d.ts
│   │       ├── hybrid-helper-system.js
│   │       ├── indent-helper.d.ts
│   │       └── ... (5 more files)
│   │   ├── index.d.ts
│   │   ├── index.js
│   └── workflow_backups/
│   ├── context_backup_20250706_163020.json
│   ├── workflow_backup_20250706_163020.json
├── backups/
│   ├── atomic_io_backup_20250710_122520/
│   │   ├── atomic_io.py
│   │   ├── utils_io_helpers.py
│   ├── cache_api_integration_20250710_145158/
│   ├── context_improvement_20250710_201108/
│   │   ├── context.json
│   │   ├── context_integration.py
│   │   ├── context_manager.py
│   │   └── ... (1 more files)
│   ├── enhanced_flow_20250711_030102/
│   │   ├── enhanced_flow.py
│   ├── event_improvement_20250711_131439/
│   │   ├── manager.py
│   │   ├── models.py
│   │   ├── workflow_event_adapter.py
│   ├── event_system_20250712_151628/
│   │   └── listeners/
│   │       ├── base.py
│   │       ├── context_listener.py
│   │       ├── error_listener.py
│   │   ├── event_bus.py
│   │   ├── event_helpers.py
│   │   ├── event_types.py
│   │   └── ... (3 more files)
│   ├── legacy_cleanup_20250709_120454/
│   │   └── workflow_v2_data/
│   │       ├── ai-coding-brain-mcp_workflow.json
│   │       ├── final_test_workflow.json
│   │   ├── context_manager_backup.py
│   │   ├── helpers_wrapper_backup.py
│   │   ├── storage_backup.py
│   ├── path_utils_backup_20250710_121805/
│   │   ├── core_path_utils.py
│   │   ├── path_utils.py
│   └── ... (11 more directories)
│   ├── workflow_event_adapter_backup_20250712_152114.py
├── docs/
│   ├── architecture/
│   │   ├── event_listener_design.md
│   │   ├── workflow_context_integration.md
│   ├── examples/
│   │   ├── event_bus_example.py
│   │   ├── workflow_context_bridge_example.py
│   ├── fixes/
│   │   ├── list_functions_error_fix.md
│   ├── integrated/
│   │   ├── summary_report_20250712_164427.md
│   │   ├── summary_report_20250712_164541.md
│   │   ├── task_4c36482a_complete.md
│   │   └── ... (1 more files)
│   ├── tasks/
│   │   ├── import_fix_report.md
│   │   ├── task1_atomic_save.md
│   │   ├── task1_completion_report.md
│   │   └── ... (8 more files)
│   ├── workflow/
│   │   ├── task_hooktest_20250712_173014.md
│   ├── workflow_docs/
│   └── workflow_v2/
│       ├── API_REFERENCE.md
│       ├── DEPLOYMENT_CHECKLIST.md
│       ├── MIGRATION_GUIDE.md
│       └── ... (2 more files)
│   ├── circular_dependency_analysis.md
│   ├── circular_dependency_fix_report.md
│   ├── data_ownership_policy.md
│   └── ... (50 more files)
├── logs/
│   ├── errors/
│   ├── file/
│   ├── git/
│   ├── system/
│   └── workflow/
│   ├── active_errors.json
│   ├── error_history.json
│   ├── log_manager_config.json
│   └── ... (2 more files)
├── memory/
│   ├── archive/
│   ├── backup/
│   │   ├── active_backup_20250710_171855/
│   │   │   ├── context.json
│   │   │   ├── session_info.json
│   │   │   ├── task_context.json
│   │   │   └── ... (1 more files)
│   │   ├── ai-coding-brain-mcp_20250704_195124/
│   │   │   ├── context.json
│   │   │   ├── workflow.json
│   │   ├── ai-coding-brain-mcp_20250705_120052/
│   │   │   ├── context.json
│   │   │   ├── workflow.json
│   │   │   ├── workflow_data.json
│   │   ├── legacy_final_backup_20250710_095949/
│   │   │   ├── workflow.json
│   │   ├── old_contexts/
│   │   │   ├── context_backup_20250701_145124_before_optimization.json
│   │   │   ├── context_backup_ai-coding-brain-mcp_20250703_153224.json
│   │   │   ├── context_backup_ai-coding-brain-mcp_20250704_180546.json
│   │   │   └── ... (18 more files)
│   │   ├── old_workflows/
│   │   │   ├── workflow_backup_20250707_155352.json
│   │   │   ├── workflow_before_cleanup_20250707_155640.json
│   │   ├── workflow_backups/
│   │   │   ├── workflow_backup_20250710_125357.json
│   │   ├── workflow_test_backup_20250710_162330/
│   │   │   ├── workflow.json
│   │   └── ... (2 more directories)
│   │   ├── context_ai-coding-brain-mcp_20250704_195124.json
│   │   ├── context_ai-coding-brain-mcp_20250705_120052.json
│   │   ├── enhanced_flow_load_workflow_backup.py
│   │   └── ... (3 more files)
│   ├── backups/
│   │   └── contexts/
│   │       └── ai-coding-brain-mcp/
│   │       ├── ai-coding-brain-mcp_context_removed.json
│   │   ├── workflow_backup_20250712_210225.json
│   │   ├── workflow_backup_20250712_210456.json
│   │   ├── workflow_backup_20250712_210512.json
│   │   └── ... (17 more files)
│   ├── cache/
│   │   └── test_cache/
│   │       ├── cache_metadata.json
│   │       ├── test_key.json
│   │   ├── cache_manifest.json
│   │   ├── cache_metadata.json
│   │   ├── file_directory.json
│   │   └── ... (1 more files)
│   ├── deprecated/
│   │   ├── active_backup_20250710_180947/
│   │   │   ├── context.json
│   │   │   ├── session_info.json
│   │   │   ├── task_context.json
│   │   │   └── ... (2 more files)
│   │   └── cleanup_20250710_182629/
│   │       └── active/
│   ├── errors/
│   ├── logs/
│   ├── projects/
│   │   ├── ai-coding-brain-mcp/
│   │   │   └── workflow_v3/
│   │   ├── project-alpha/
│   │   │   ├── backups/
│   │   │   └── cache/
│   │   │   ├── context.json
│   │   │   ├── workflow.json
│   │   ├── project-beta/
│   │   │   ├── backups/
│   │   │   └── cache/
│   │   │   ├── context.json
│   │   │   ├── workflow.json
│   │   ├── project-gamma/
│   │   │   ├── backups/
│   │   │   └── cache/
│   │   │   ├── context.json
│   │   │   ├── workflow.json
│   │   ├── test-independent-project/
│   │   │   ├── backups/
│   │   │   └── cache/
│   │   │   ├── context.json
│   │   │   ├── workflow.json
│   │   └── test-workflow-project/
│   │       ├── workflow.json
│   └── ... (4 more directories)
│   ├── context.json
│   ├── hook_config.json
│   ├── integrated_context.json
│   └── ... (9 more files)
├── python/
│   ├── ai_helpers/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── image.py
│   │   │   ├── manager.py
│   │   │   └── ... (2 more files)
│   │   └── search/
│   │       ├── __init__.py
│   │       ├── code_search.py
│   │       ├── core.py
│   │       └── ... (4 more files)
│   │   ├── __init__.py
│   │   ├── build.py
│   │   ├── code.py
│   │   └── ... (11 more files)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── image_generator.py
│   │   ├── public.py
│   │   └── ... (3 more files)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── cache_manager.py
│   │   ├── context_manager.py
│   │   └── ... (4 more files)
│   ├── events/
│   │   └── handlers/
│   │       ├── __init__.py
│   │   ├── __init__.py
│   │   ├── enhanced_event_bus.py
│   │   ├── event_bus.py
│   │   └── ... (5 more files)
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
│   ├── workflow/
│   │   └── v3/
│   │       ├── api/
│   │       ├── commands/
│   │       ├── listeners/
│   │       └── tests/
│   │       ├── __init__.py
│   │       ├── code_integration.py
│   │       ├── context_integration.py
│   │       └── ... (19 more files)
│   │   ├── __init__.py
│   └── ... (1 more directories)
│   ├── __init__.py
│   ├── api_manager.py
│   ├── debug_flow.py
│   └── ... (14 more files)
└── ... (7 more directories)
├── .ai-brain.config.json
├── .eslintrc.json
├── check_syntax.py
└── ... (57 more files)
```
- `.ai-brain.config.json`: AI Coding Brain 설정
- `package.json`: Node.js 프로젝트 설정
- `tsconfig.json`: TypeScript 설정
- `.env`: 환경 변수
- `.gitignore`: Git 무시 파일
- `requirements.txt`: Python 의존성

## 📊 프로젝트 통계

- **전체 파일 수**: 746개
- **디렉토리 수**: 167개
- **파일 타입 분포**:
  - `.py`: 266개 (35.7%)
  - `.json`: 168개 (22.5%)
  - `.md`: 101개 (13.5%)
  - `.ts`: 63개 (8.4%)
  - `.map`: 60개 (8.0%)

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
