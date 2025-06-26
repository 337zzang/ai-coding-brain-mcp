# 프로젝트 컨텍스트: ai-coding-brain-mcp

> 이 문서는 프로젝트의 상세 컨텍스트와 구조를 설명합니다.
> 최종 업데이트: 2025-06-27 00:13:29

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
| `docs/` | 문서 |
| `image/` | 프로젝트 관련 파일 |
| `memory/` | 캐시 및 상태 저장 |
| `python/` | Python 스크립트 및 유틸리티 |
| `src/` | 소스 코드 |
| `test/` | 테스트 코드 |

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
├── docs/
│   ├── AI_IMAGE_GENERATION_GUIDE.md
│   ├── API_Safety_Guide.md
│   ├── DLC_Architecture_Design.md
│   └── ... (5 more files)
├── image/
│   ├── image_metadata.json
├── memory/
│   ├── .cache/
│   │   ├── cache_analyzed_files.json
│   │   ├── cache_core.json
│   │   ├── cache_plan.json
│   │   └── ... (2 more files)
│   ├── backups/
│   ├── context_backups/
│   │   └── 2025-06-26/
│   │       ├── ai-coding-brain-mcp_context_174328.json
│   │       ├── ai-coding-brain-mcp_context_174347.json
│   │       ├── ai-coding-brain-mcp_context_175400.json
│   ├── docs/
│   ├── plan_templates/
│   │   ├── default.json
│   ├── wisdom/
│   │   ├── ai-coding-brain-mcp_wisdom.json
│   └── wisdom_data/
│       ├── _wisdom.json
│   ├── coding_flow.md
│   ├── manifest_backup_20250625.json
│   ├── manifest_backup_20250626.json
│   └── ... (7 more files)
├── python/
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── file_analyzer.py
│   │   ├── manifest_manager.py
│   │   └── ... (1 more files)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── image_generator.py
│   │   ├── public.py
│   │   └── ... (1 more files)
│   ├── commands/
│   │   └── improved/
│   │       ├── apply_improvements.py
│   │       ├── next_improved.py
│   │       ├── plan_improved.py
│   │       └── ... (2 more files)
│   │   ├── __init__.py
│   │   ├── enhanced_flow.py
│   │   ├── file_analyze.py
│   │   └── ... (4 more files)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── context_manager.py
│   │   └── ... (1 more files)
│   ├── output/
│   │   ├── __init__.py
│   │   ├── handlers.py
│   ├── vendor/
│   │   ├── tree-sitter-javascript/
│   │   │   ├── .github/
│   │   │   ├── bindings/
│   │   │   ├── examples/
│   │   │   ├── queries/
│   │   │   ├── src/
│   │   │   └── test/
│   │   │   ├── grammar.js
│   │   │   ├── package-lock.json
│   │   │   ├── package.json
│   │   │   └── ... (3 more files)
│   │   ├── tree-sitter-javascript-master/
│   │   │   ├── .github/
│   │   │   ├── bindings/
│   │   │   ├── examples/
│   │   │   ├── queries/
│   │   │   ├── src/
│   │   │   └── test/
│   │   │   ├── grammar.js
│   │   │   ├── package-lock.json
│   │   │   ├── package.json
│   │   │   └── ... (3 more files)
│   │   ├── tree-sitter-typescript/
│   │   │   ├── .github/
│   │   │   ├── bindings/
│   │   │   ├── common/
│   │   │   ├── examples/
│   │   │   ├── queries/
│   │   │   ├── test/
│   │   │   ├── tsx/
│   │   │   └── typescript/
│   │   │   ├── package-lock.json
│   │   │   ├── package.json
│   │   │   ├── README.md
│   │   │   └── ... (2 more files)
│   │   └── tree-sitter-typescript-master/
│   │       ├── .github/
│   │       ├── bindings/
│   │       ├── common/
│   │       ├── examples/
│   │       ├── queries/
│   │       ├── test/
│   │       ├── tsx/
│   │       └── typescript/
│   │       ├── package-lock.json
│   │       ├── package.json
│   │       ├── README.md
│   │       └── ... (2 more files)
│   └── wisdom_data/
│       ├── _wisdom.json
│       ├── ai-coding-brain-mcp_wisdom.json
│   ├── __init__.py
│   ├── api_manager.py
│   ├── ast_parser_helpers.py
│   └── ... (20 more files)
├── src/
│   ├── core/
│   │   ├── domain/
│   │   │   ├── entities/
│   │   │   └── repositories/
│   │   │   ├── index.ts
│   │   └── infrastructure/
│   │       └── filesystem/
│   │       ├── index.ts
│   │   ├── index.ts
│   ├── handlers/
│   │   ├── api-toggle-handler.ts
│   │   ├── backup-handler.ts
│   │   ├── build-handler.ts
│   │   └── ... (7 more files)
│   ├── memory/
│   │   ├── config.ts
│   ├── services/
│   │   ├── logger.ts
│   ├── tools/
│   │   ├── tool-definitions.ts
│   ├── types/
│   │   ├── tool-interfaces.ts
│   └── utils/
│       ├── hybrid-helper-system.ts
│       ├── logger.ts
│   ├── index.ts
└── test/
    ├── app-0.10.38/
    ├── fixtures/
    │   ├── __init__.py
    ├── integration/
    │   ├── __init__.py
    │   ├── test_workflow.py
    └── unit/
        ├── __init__.py
        ├── test_commands.py
        ├── test_context_manager.py
    ├── conftest.py
    ├── run_tests.py
    ├── test_cache_v7.py
    └── ... (1 more files)
├── .ai-brain.config.json
├── .eslintrc.json
├── claude_desktop_config.json
└── ... (17 more files)
```
- `.ai-brain.config.json`: AI Coding Brain 설정
- `package.json`: Node.js 프로젝트 설정
- `tsconfig.json`: TypeScript 설정
- `.env`: 환경 변수
- `.gitignore`: Git 무시 파일
- `requirements.txt`: Python 의존성

## 📊 프로젝트 통계

- **전체 파일 수**: 480개
- **디렉토리 수**: 142개
- **파일 타입 분포**:
  - `.py`: 73개 (15.2%)
  - `.json`: 54개 (11.2%)
  - `.js`: 38개 (7.9%)
  - `.ts`: 36개 (7.5%)
  - `.md`: 32개 (6.7%)

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
- 프로젝트 작업 중 발견한 교훈은 [project_wisdom.md](./project_wisdom.md) 참조
- API 문서는 [API_REFERENCE.md](./API_REFERENCE.md) 참조 (생성 예정)

---
*이 문서는 /build 명령으로 자동 생성되었습니다.*
