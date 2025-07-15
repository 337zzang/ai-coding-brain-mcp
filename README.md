# ai-coding-brain-mcp

통합 AI 코딩 브레인 MCP - Memory Bank, Desktop Commander, Notebook, Claude Memory 통합

## 📋 프로젝트 정보

- **버전**: 1.0.0
- **언어**: TypeScript/JavaScript
- **최종 업데이트**: 2025-07-15 00:54:57

## 📊 프로젝트 통계

- **전체 파일**: 362개
- **디렉토리**: 96개
- **주요 언어**:
  - Python: 191개 파일
  - TypeScript: 28개 파일
  - JavaScript: 3개 파일

## 🗂️ 프로젝트 구조

```
ai-coding-brain-mcp/
├── .pytest_cache/
├── backup_before_protocol_replace_20250715_003154/
├── backup_deleted_modules/
├── backup_legacy_workflow_20250714_233227/
├── backup_protocol_migration_20250715_002449/
├── docs/
├── examples/
├── generated_scripts/
└── ... (외 7개)
```



## 🚀 최근 업데이트 (2025-07-15)

### MCP 도구 → Execute Code 전환
- `flow_project`, `start_project`, `build_project_context` MCP 도구 제거
- 더 빠르고 안정적인 execute_code 기반 함수로 대체
- Timeout 문제 완전 해결

### 새로운 프로젝트 관리 함수
execute_code에서 사용 가능한 함수들:
- `project_switch(project_name)` - 프로젝트 전환
- `safe_flow_project(project_name, timeout=30)` - 타임아웃 보호 전환
- `project_create(project_name, init_git=True)` - 새 프로젝트 생성
- `project_build_context()` - 문서 자동 생성
- `check_project_status()` - 현재 프로젝트 상태 확인

### 문서
- [Execute Code 마이그레이션 가이드](docs/execute_code_migration_guide.md)
- [프로젝트 관리 Quick Reference](docs/project_management_quick_ref.md)

## 🚀 시작하기

### 설치

```bash
# 의존성 설치
npm install
```

### 실행

```bash
# 프로젝트 실행 명령어를 여기에 추가하세요
```

## 📖 문서

- [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md) - 프로젝트 상세 컨텍스트
- [file_directory.md](./file_directory.md) - 파일 구조 문서

## 🤝 기여하기

기여를 환영합니다! PR을 보내주세요.

---
*이 문서는 /build 명령으로 자동 생성되었습니다.*
