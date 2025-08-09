# AI Coding Brain MCP - 유저 프리퍼런스 v3.0
*최종 수정: 2025-08-09 (Facade 패턴 적용 + Phase 2 완료 + 폴더 구조 개선)*

## 🎯 핵심 원칙 (16개)

### 🔴 최우선 원칙 (1-8)
1. **Facade 네임스페이스 우선** - `h.file.*`, `h.code.*` 등 구조화된 API 사용
2. **Project Knowledge 자동 활용** - Claude가 자동으로 프로젝트 지식 검색
3. **기존 모듈 재사용 강제** - 신규 생성보다 기존 확장 우선
4. **초상세 설계 → 명시적 승인 → 결과 피드백** - 3단계 확인 프로세스
5. **표준 응답 형식** - `{'ok': bool, 'data': Any, 'error': str}` 준수
6. **Python 블록 단위 수정** - try-except, if-elif-else는 전체 블록으로
7. **Git 브랜치 전략** - 브랜치 생성 → 수정 → 검증 → 병합
8. **요청한 작업만 수행** - 과도한 자동 분석 금지

### 🟡 핵심 원칙 (9-13)
9. **TaskLogger 완전 추적** - 모든 작업 과정과 결과 기록
10. **기능 단위 TODO** - Task를 5-10개 논리적 기능 단위로 분할
11. **AST 검증 필수** - 코드 수정 전 구문 검증으로 실패 예방
12. **프로젝트 컨텍스트** - 절대경로 우선, 프로젝트 내부에서만 작업
13. **자동 오류 복구** - 실패 시 복구 모드 자동 전환

### 🟢 보조 원칙 (14-16)
14. **Task 브랜치형 진행** - 이전 Task 컨텍스트 필수 확인
15. **O3-Claude 협업** - 코드 변수화로 효율적 전달
16. **REPL 우선 테스트** - execute_code의 영속성 활용

## 🚀 Facade 패턴 사용법 (v2.7.0)

### 새로운 네임스페이스 방식 (권장) ✨
```python
import ai_helpers_new as h

# 📁 파일 작업
content = h.file.read("test.txt")
h.file.write("output.txt", content)
h.file.append("log.txt", "new line")
exists = h.file.exists("config.json")
info = h.file.get_file_info("data.csv")
h.file.create_directory("new_folder")
files = h.file.list_directory(".")

# 🔍 검색
py_files = h.search.files("*.py")
imports = h.search.imports("pandas")  # Phase 1 신규
stats = h.search.statistics(".")      # Phase 1 신규
results = h.search.code("TODO", ".")
func = h.search.function("main", ".")
cls = h.search.class_("Manager", ".")

# 📝 코드 분석/수정
parsed = h.code.parse("module.py")
h.code.view("file.py", "function_name")
h.code.replace("file.py", old, new)
h.code.insert("file.py", "new line", position="def main():", after=True)
funcs = h.code.functions("module.py")
classes = h.code.classes("module.py")

# 🔀 Git 작업
status = h.git.status()
h.git.add(".")
h.git.commit("feat: 새 기능 추가")
diff = h.git.diff()
log = h.git.log(limit=10)
h.git.checkout_b("feature/new")
h.git.merge("main")
h.git.push()
```

### 레거시 방식 (하위 호환성 유지)
```python
# 여전히 작동하지만 권장하지 않음
content = h.read("test.txt")
h.write("output.txt", content)
h.git_status()
h.git_commit("update")
```

## 📂 파일 저장 위치 체계 (개선됨)

### 문서 카테고리별 저장 경로
| 카테고리 | 저장 경로 | 파일명 예시 | 용도 |
|----------|----------|-------------|------|
| **분석 보고서** | `docs/reports/` | `test_report_v26.md` | 테스트, 성능 분석 |
| **O3 분석** | `docs/analysis/` | `o3_fuzzy_matching_analysis.md` | AI 분석 결과 |
| **구현 문서** | `docs/implementations/` | `facade_implementation_report.md` | 구현 완료 보고 |
| **Phase별 문서** | `docs/phase{n}/` | `phase2_comprehensive_review.md` | 단계별 산출물 |
| **설계 문서** | `docs/design/` | `auth_architecture.md` | 아키텍처 설계 |
| **사용 가이드** | `docs/guides/` | `facade_migration_guide.md` | 사용법 안내 |
| **API 문서** | `docs/api/` | `search_api.md` | API 레퍼런스 |
| **트러블슈팅** | `docs/troubleshooting/` | `import_errors.md` | 문제 해결 |
| **프로토타입** | `docs/prototypes/` | `facade_prototype.py` | 코드 예시 |
| **시니어 질문** | `docs/questions/{timestamp}/` | `senior_review.md` | 검토 요청 |
| **테스트** | `test/` | `test_facade.py` | 테스트 코드 |
| **백업** | `backups/{date}/` | `backup_20250809.zip` | 백업 파일 |
| **TaskLogger** | `.ai-brain/flow/plans/{plan_id}/` | `1.task_name.jsonl` | 작업 로그 |
| **임시 파일** | `.temp/` | `temp_analysis.md` | 임시 작업 |

### 파일명 규칙
- **보고서**: `{주제}_report_{버전}.md` (예: `facade_implementation_report.md`)
- **분석**: `{도구}_{주제}_analysis.md` (예: `o3_architecture_analysis.md`)
- **Phase 문서**: `phase{n}_{주제}.md` (예: `phase2_comprehensive_review.md`)
- **가이드**: `{주제}_guide.md` (예: `migration_guide.md`)
- **프로토타입**: `{기능}_prototype.{ext}` (예: `facade_prototype.py`)

## 🔧 헬퍼 함수 상세 (Facade 기준)

### 📁 h.file.* (파일 네임스페이스)
```python
# 기본 파일 작업
h.file.read(filepath, offset=0, length=1000)    # 부분 읽기 지원
h.file.write(filepath, content, mode='rewrite') # 쓰기/덮어쓰기
h.file.append(filepath, content)                # 추가
h.file.exists(filepath)                         # 존재 확인 {'ok': True, 'data': bool}
h.file.get_file_info(filepath)                  # 메타데이터

# 디렉토리 작업
h.file.create_directory(path)                   # 디렉토리 생성
h.file.list_directory(path)                     # 파일 목록
h.file.scan_directory(path, max_depth=2)        # 깊이 제한 스캔

# JSON 작업
h.file.read_json(filepath)                      # JSON 읽기
h.file.write_json(filepath, data)               # JSON 쓰기

# 경로 작업
h.file.resolve_project_path(relative_path)      # 프로젝트 경로 해결
```

### 🔍 h.search.* (검색 네임스페이스)
```python
# 파일 검색
h.search.files("pattern")        # 와일드카드 자동 변환 (*pattern*)
h.search.files("*.py")           # 확장자 검색

# 코드 검색
h.search.code("pattern", path=".", context=3)  # 컨텍스트 라인 포함
h.search.function("name", path=".")            # 함수 검색
h.search.class_("name", path=".")              # 클래스 검색
h.search.grep("pattern", path=".")             # grep 스타일

# Phase 1 신규 기능
h.search.imports("module_name")  # import 추적
h.search.statistics(".")         # 코드베이스 통계
```

### 📝 h.code.* (코드 네임스페이스)
```python
# 분석
h.code.parse(filepath)            # AST 분석 {'functions': [], 'classes': []}
h.code.view(filepath, target)     # 특정 부분 보기
h.code.functions(filepath)        # 함수 목록
h.code.classes(filepath)          # 클래스 목록

# 수정
h.code.replace(filepath, old, new, fuzzy=True)      # 텍스트 교체
h.code.insert(filepath, content, position, after)   # 스마트 삽입
h.code.delete(filepath, target, mode='block')       # 블록 삭제 (예정)
```

### 🔀 h.git.* (Git 네임스페이스)
```python
# 기본 명령
h.git.status()                   # 상태 확인
h.git.add(files)                 # 스테이징
h.git.commit(message)            # 커밋
h.git.diff()                     # 변경사항
h.git.log(limit=10)              # 히스토리

# 브랜치
h.git.branch()                   # 브랜치 목록
h.git.checkout(branch)           # 브랜치 전환
h.git.checkout_b(new_branch)     # 브랜치 생성
h.git.merge(branch)              # 병합

# 원격
h.git.push()                     # 푸시
h.git.pull()                     # 풀

# 추가
h.git.stash()                    # 임시 저장
h.git.reset("HEAD~1")            # 리셋
h.git.status_normalized()        # 확장된 상태 (Phase 1)
```

### 📊 Flow API (19개 메서드)
```python
# FlowAPI 가져오기
api = h.get_flow_api()
api.help()  # 메서드 목록

# Plan 관리 (6개)
api.create_plan(name, description="")
api.list_plans(status=None, limit=10)
api.get_plan(plan_id)
api.update_plan(plan_id, **kwargs)
api.delete_plan(plan_id)
api.select_plan(plan_id)  # 체이닝 가능

# Task 관리 (8개)
api.create_task(plan_id, name, description="")
api.add_task(plan_id, title, **kwargs)
api.list_tasks(plan_id, status=None)
api.get_task(plan_id, task_id)
api.get_task_by_number(plan_id, number)
api.update_task(plan_id, task_id, **kwargs)
api.update_task_status(plan_id, task_id, status)
api.update_task_status_by_number(plan_id, number, status)

# 검색/통계/컨텍스트 (6개)
api.search(query)
api.get_stats()
api.set_context(key, value)  # 체이닝 가능
api.get_context(key)
api.clear_context()         # 체이닝 가능
api.get_current_plan()
```

### 🤖 O3/LLM 함수
```python
# 기본 O3 사용
question = "코드 분석 요청..."
task_id = h.ask_o3_async(question)['data']
h.show_o3_progress()
result = h.get_o3_result(task_id)
h.clear_completed_tasks()

# O3 컨텍스트 빌더 (효율적 전달)
from ai_helpers_new import O3ContextBuilder
builder = O3ContextBuilder()
builder.add_file("code.py", code_content)
builder.add_error(traceback)
builder.add_context("목적", "버그 수정")
result = builder.ask(question)

# 상태 확인
status = h.check_o3_status(task_id)
```

### 📋 TaskLogger
```python
# 초기화
logger = h.create_task_logger(plan_id, task_num, "task_name")

# 작업 단계 기록
logger.task_info(title="제목", priority="high", estimate="2h")
logger.design(content={"목표": "...", "범위": [...]})
logger.todo(items=["item1", "item2", ...])
logger.code(action="create", file="test.py", summary="생성")
logger.blocker(issue="문제", severity="high", solution="해결")
logger.complete(summary={"성과": "...", "next_steps": [...]})
```

### 🚀 프로젝트 관리
```python
# 프로젝트 전환
h.flow_project_with_workflow("project-name")  # 전환 + 최신 플랜 3개
h.get_current_project()                       # 현재 프로젝트
h.scan_directory(".", max_depth=2)            # 구조 스캔

# 플랜 선택 및 표시
h.select_plan_and_show('1')                   # JSONL 로그 포함
```

## 🌐 웹 자동화 (Persistent)
```python
# 영속적 세션
from api.web_session_persistent import PersistentSession
session = PersistentSession("my_work")
page = session.start("https://example.com")
page.fill("input", "text")
session.stop(keep_profile=True)

# --- REPL 재시작 후 ---
session = PersistentSession("my_work")
page = session.reconnect()  # 상태 복원!
```

## 📊 Excel 자동화
```python
h.excel_connect("file.xlsx")
h.excel_write_range("Sheet1", "A1", data)
h.excel_read_range("Sheet1", "A1:C3")
h.excel_apply_formula("Sheet1", "D1", "=SUM(A1:C1)")
h.excel_disconnect(save=True)
```

## 🐛 알려진 문제 및 해결

### Phase 2 이후 변경사항
| 변경 전 | 변경 후 | 설명 |
|---------|---------|------|
| `h.read()` | `h.file.read()` | 네임스페이스 사용 권장 |
| `h.search_files()` | `h.search.files()` | 구조화된 API |
| `h.git_status()` | `h.git.status()` | Git 네임스페이스 |
| 직접 import | Facade 패턴 | 내부 구조 캡슐화 |

### 주요 개선사항 (Phase 1 & 2)
- ✅ 순환 import 해결
- ✅ search_imports 구현
- ✅ get_statistics 구현
- ✅ Facade 패턴 적용
- ✅ 안전한 속성 접근 (getattr)

### 미구현 함수 대체 방법
| 함수 | 대체 방법 |
|------|----------|
| `list_projects()` | 파일 시스템 직접 스캔 |
| `project_info()` | `h.get_current_project()` + `h.file.scan_directory()` |
| `get_cache_info()` | 향후 구현 예정 |
| `clear_cache()` | 향후 구현 예정 |

## 📝 작업 템플릿

### 설계 승인 템플릿
```markdown
## 🎯 [작업명] 설계

### 📚 기존 모듈 활용
- 재사용: `h.file.read()`, `h.code.parse()`
- 확장: 기존 클래스에 메서드 추가

### 🆕 신규 추가 (최소화)
- [필수 이유 명시]

### ✅ 승인 요청
이 설계로 진행하시겠습니까? (Y/N)
```

### 수정 승인 템플릿
```markdown
## 🔧 코드 수정

### 현재 코드:
```python
[현재]
```

### 수정 후:
```python
[수정]
```

### ✅ 승인 요청
이렇게 수정하시겠습니까? (Y/N)
```

## ⚡ 빠른 참조 (Facade 기준)

### 자주 사용하는 명령어
```python
# 프로젝트 관리
h.flow_project_with_workflow("project")
h.select_plan_and_show('1')

# 파일 작업 (네임스페이스)
content = h.file.read("file.py")['data']
h.file.write("output.py", content)

# 코드 수정 (네임스페이스)
h.code.replace("file.py", old, new, fuzzy=True)
h.code.insert("file.py", code, position="def main():", after=True)

# 검색 (네임스페이스)
files = h.search.files("*.py")
imports = h.search.imports("pandas")
stats = h.search.statistics(".")

# Git (네임스페이스)
h.git.status()
h.git.checkout_b("feature/name")
h.git.commit("feat: 설명")

# Flow API
api = h.get_flow_api()
api.create_plan("작업명")
api.create_task(plan_id, "Task 이름")

# O3 사용
task_id = h.ask_o3_async("질문")['data']
result = h.get_o3_result(task_id)
```

## 🚨 긴급 대응

| 문제 | 해결 |
|------|------|
| Import 오류 | `h = get_facade()` 재실행 |
| 속성 없음 | getattr 사용 또는 None 체크 |
| 네임스페이스 오류 | 레거시 함수 사용 |
| 중복 모듈 | 기존 검색 → 통합 |
| 패턴 불일치 | 이전 Task 확인 → 수정 |
| 코드 오류 | `h.git.checkout("file.py")` |
| 세션 끊김 | `PersistentSession.reconnect()` |

## 🏁 통합 체크리스트

### 작업 시작 전
□ **프로젝트 전환** (`h.flow_project_with_workflow()`)
□ **기존 모듈 검색** (`h.search.files()`, `h.search.code()`)
□ **이전 컨텍스트 확인** (패턴, 네이밍, 결정사항)
□ **설계 승인** 받기

### 작업 중
□ **네임스페이스 사용** (`h.file.*`, `h.code.*`)
□ **표준 응답 형식** 확인 (`if result['ok']`)
□ **블록 단위 수정** (완전한 구조)
□ **TaskLogger 기록**

### 작업 후
□ **수정 승인** 받기
□ **결과 피드백** 받기
□ **문서 저장** (적절한 폴더에)
□ **Git 커밋** (`h.git.commit()`)

## 📈 버전 히스토리

### v3.0 (2025-08-09)
- Facade 패턴 적용 완료
- 네임스페이스 구조화
- 파일 저장 위치 체계 개선
- Phase 2 완료

### v2.7 (2025-08-09)
- Phase 1 완료 (search_imports, get_statistics)
- 순환 import 해결

### v2.6 (2025-08-08)
- 기존 모듈 재사용 강화
- O3 협업 패턴
- 피드백 프로세스

## 💡 핵심 요약
> **"네임스페이스 우선"** → **"기존 재사용"** → **"설계/승인/피드백"** → **"블록 수정"** → **"적절한 폴더 저장"** → **"표준 응답"**

---
**버전**: v3.0 (Facade 패턴 적용 + Phase 2 완료)
**최종 수정**: 2025-08-09
**프로젝트**: ai-coding-brain-mcp