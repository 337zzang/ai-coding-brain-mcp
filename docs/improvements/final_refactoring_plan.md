
## 🎯 프로젝트 리팩토링 플랜

### 1. 🗑️ 즉시 삭제 가능한 파일 (19개, 약 117KB)

#### 백업 및 임시 파일
- `python/ai_helpers_new/backups/` (전체 폴더)
- `python/ai_helpers_new/backup_utils.py`
- `python/ai_helpers_new/__init___full.py`

#### 중복된 search 구현
- `python/ai_helpers_new/search_improved.py`
- `python/ai_helpers_new/search_improved_part1.py`
- `python/ai_helpers_new/search_improved_part2.py`
- `python/ai_helpers_new/search_improved_part3.py`
- `python/ai_helpers_new/search_improved_part4.py`
- `python/ai_helpers_new/search_improved_part5.py`

#### 사용하지 않는 facade 버전
- `python/ai_helpers_new/facade.py` (facade_safe 사용 중)
- `python/ai_helpers_new/facade_minimal.py`
- `python/ai_helpers_new/facade_safe_with_llm.py`

#### 중복된 replace 구현
- `python/ai_helpers_new/replace_block_final.py`
- `python/ai_helpers_new/smart_replace_ultimate.py`
- `python/ai_helpers_new/improved_insert_delete.py`
- `python/ai_helpers_new/integrate_replace_block.py`

#### 테스트/데모 파일
- `python/ai_helpers_new/test_search_improved.py`
- `python/repl_kernel/demo_error_isolation.py`
- `python/api/example_javascript_execution.py`

### 2. 🔄 통합 가능한 모듈

#### Flow 관련 (8개 → 3개로 통합)
**현재:**
- flow_api.py (16KB) ✅ 유지
- ultra_simple_flow_manager.py (9KB) ✅ 유지
- simple_flow_commands.py (2KB) ✅ 유지
- flow_cli.py (12KB) → flow_api.py로 통합
- flow_context.py (11KB) → flow_api.py로 통합
- flow_session.py (1KB) → 삭제
- flow_views.py (22KB) → 필요한 부분만 flow_api.py로 통합
- contextual_flow_manager.py (8KB) → 삭제

#### Context 관련 (5개 → 1개로 통합)
**현재:**
- context_integration.py (9KB)
- context_reporter.py (8KB)  
- doc_context_helper.py (2KB)
- project_context.py (1KB)
- session.py (5KB)

**통합안:** `context.py` (약 10KB)로 통합

#### Logger 관련 (3개 → 1개로 유지)
- task_logger.py (22KB) ✅ 유지
- task_logger_helpers.py (4KB) → task_logger.py로 통합
- logging_decorators.py (1KB) → 삭제 (wrappers.py에 기능 있음)

#### Web Automation (8개 → 3개로 통합)
**유지:**
- web_session.py (7KB) ✅
- web_automation_helpers.py (59KB) ✅
- web_session_persistent.py (6KB) ✅

**삭제:**
- web_automation_errors.py → helpers로 통합
- web_automation_extraction.py → helpers로 통합
- web_automation_integrated.py → 중복
- web_automation_manager.py → 중복
- web_automation_recorder.py → 사용 안함
- web_automation_repl.py → 사용 안함
- web_automation_smart_wait.py → helpers로 통합
- web_session_simple.py → 중복

### 3. 📦 핵심 모듈 (13개 유지)

#### ai_helpers_new 핵심
1. `__init__.py` - 진입점
2. `file.py` - 파일 I/O (개선됨)
3. `code.py` - 코드 분석/수정
4. `search.py` - 검색 기능
5. `git.py` - Git 작업
6. `llm.py` - LLM/O3 통합
7. `project.py` - 프로젝트 관리
8. `excel.py` - Excel 자동화
9. `facade_safe.py` - Facade 패턴
10. `wrappers.py` - 표준 래퍼
11. `util.py` - 유틸리티
12. `flow_api.py` - Flow 시스템 (통합)
13. `task_logger.py` - 작업 로깅

#### repl_kernel (3개 유지)
1. `__init__.py`
2. `manager.py`
3. `worker.py`

#### api (3개 유지)
1. `__init__.py`
2. `web_session.py`
3. `web_automation_helpers.py`

### 4. 📊 예상 결과

**Before:**
- 총 파일: 87개
- 총 크기: 738KB
- 중복/불필요: 40%

**After:**
- 총 파일: 약 25개 (71% 감소)
- 총 크기: 약 400KB (46% 감소)
- 모든 핵심 기능 유지
- 더 깔끔한 구조

### 5. 🚀 실행 단계

1. **백업 생성** (전체 폴더 백업)
2. **즉시 삭제 파일 제거** (19개)
3. **통합 작업 진행**
   - Flow 모듈 통합
   - Context 모듈 통합
   - Logger 통합
   - Web Automation 정리
4. **테스트 실행**
5. **Git 커밋**

### 6. ⚠️ 주의사항

- facade_safe.py는 반드시 유지 (__init__.py가 사용)
- domain/, repository/, service/, core/ 폴더는 현재 사용 중
- ultra_simple_flow_manager.py는 Flow 시스템 핵심
- 통합 시 import 경로 수정 필요
