# AI Helpers 함수 인벤토리 보고서

생성일: 2025-07-24 04:59

## 📊 전체 요약

- **총 모듈 수**: 34개
- **총 함수 수**: 364개
- **중복 함수**: 40개
- **표준 미준수**: 18개 (핵심 모듈 기준)

## 📂 카테고리별 분포

| 카테고리 | 함수 수 | 비율 |
|---------|--------|------|
| Flow 관리 | 79개 | 21.7% |
| 도메인/인프라 | 61개 | 16.8% |
| 프레젠테이션 | 50개 | 13.7% |
| Context 관리 | 35개 | 9.6% |
| 서비스 | 34개 | 9.3% |
| 검색 | 19개 | 5.2% |
| 코드 분석/수정 | 15개 | 4.1% |
| 기타 | 14개 | 3.8% |
| 파일 작업 | 12개 | 3.3% |
| Git | 12개 | 3.3% |
| LLM/AI | 11개 | 3.0% |
| 프로젝트 관리 | 11개 | 3.0% |
| 유틸리티 | 11개 | 3.0% |


## 🔍 주요 발견사항

### 1. 중복 함수 (상위 10개)

1. **add_task_action** (2개 모듈)
   - `legacy_flow_adapter.py`
   - `service\task_service.py`

2. **aliases** (3개 모듈)
   - `presentation\command_interface.py`
   - `presentation\plan_commands.py`
   - `presentation\task_commands.py`

3. **create_flow** (2개 모듈)
   - `flow_manager.py`
   - `legacy_flow_adapter.py`

4. **create_flow_manager** (2개 모듈)
   - `helpers_integration.py`
   - `legacy_flow_adapter.py`

5. **create_plan** (2개 모듈)
   - `flow_manager.py`
   - `service\plan_service.py`

6. **create_project** (2개 모듈)
   - `legacy_flow_adapter.py`
   - `unified_manager_prototype.py`

7. **create_task** (2개 모듈)
   - `flow_manager.py`
   - `service\task_service.py`

8. **current_flow** (4개 모듈)
   - `flow_manager.py`
   - `flow_manager.py`
   - `legacy_flow_adapter.py`
   - ... 외 1개

9. **current_project** (4개 모듈)
   - `flow_manager.py`
   - `flow_manager.py`
   - `legacy_flow_adapter.py`
   - ... 외 1개

10. **decorator** (2개 모듈)
   - `context_decorator.py`
   - `flow_context_wrapper.py`


### 2. 표준 형식 미준수 함수

#### git.py (3개)
- `find_git_executable()` (line 8)
- `git_diff()` (line 177)
- `git_status_string()` (line 202)

#### llm.py (1개)
- `prepare_o3_context()` (line 391)

#### util.py (4개)
- `ok()` (line 7)
- `err()` (line 20)
- `is_ok()` (line 34)
- `get_data()` (line 39)

#### project.py (10개)
- `detect_project_type()` (line 39)
- `scan_directory()` (line 52)
- `scan_directory_dict()` (line 75)
- `create_project_structure()` (line 144)
- `flow_project_with_workflow()` (line 198)
- ... 외 5개


## 📋 핵심 모듈 상세

### file.py (파일 작업)
- read, write, append
- read_json, write_json
- exists, info, list_all

### code.py (코드 분석/수정)
- parse, view, replace, insert
- functions, classes, imports
- stats, dependencies

### git.py (Git 작업)
- git_status, git_add, git_commit
- git_push, git_pull, git_branch
- git_log, git_diff

### search.py (검색)
- search_files, search_code
- find_function, find_class
- grep

### llm.py (AI/LLM)
- ask_o3_async, check_o3_status
- get_o3_result, prepare_o3_context

## 🎯 개선 권장사항

1. **중복 제거**: 40개의 중복 함수 통합 필요
2. **표준화**: 18개 함수를 표준 형식으로 수정
3. **모듈 재구성**: Flow 관련 모듈 통합 (79개 → 30개 목표)
4. **문서화**: docstring이 없는 함수들에 문서 추가
5. **네이밍**: 일관된 네이밍 규칙 적용
