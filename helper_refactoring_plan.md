
## 🎯 AI Coding Brain MCP - 헬퍼 함수 리팩토링 계획

### 📅 리팩토링 로드맵

#### Phase 1: 파일 작업 헬퍼 통합 (우선순위: 🔴 높음)
**목표**: 중복 제거, 일관된 인터페이스 구축

##### 1-1. 읽기 작업 통합
```python
# 현재 (중복 많음)
read_file()
read_file_safe()
read_json()
read_json_safe()

# 개선안
read_file(path, encoding='utf-8', safe=True) -> FileResult
read_json(path, safe=True) -> dict | FileResult
```

##### 1-2. 쓰기 작업 통합
```python
# 현재
write_file()
create_file()
append_to_file()
write_json()

# 개선안
write_file(path, content, mode='w', safe=True) -> WriteResult
write_json(path, data, indent=2, safe=True) -> WriteResult
# create_file과 append는 mode 파라미터로 통합
```

##### 1-3. FileResult 표준화
```python
@dataclass
class FileResult:
    success: bool
    content: Any = None
    error: str = None
    path: str = None
    size: int = None
    encoding: str = None
```

**예상 소요 시간**: 2-3시간
**영향받는 코드**: 모든 파일 작업 사용처

---

#### Phase 2: 검색 작업 헬퍼 통합 (우선순위: 🟡 중간)
**목표**: 통합된 검색 인터페이스

##### 2-1. 검색 함수 통합
```python
# 현재
search_files()
search_code()
find_function()
find_class()
grep()

# 개선안
search(
    path: str,
    pattern: str,
    type: Literal['file', 'code', 'function', 'class'] = 'code',
    options: SearchOptions = None
) -> SearchResult
```

##### 2-2. SearchResult 표준화
```python
@dataclass
class SearchResult:
    matches: List[Match]
    total_count: int
    search_time: float

@dataclass
class Match:
    file: str
    line: int
    column: int
    text: str
    context: List[str]  # 전후 라인
```

**예상 소요 시간**: 2시간
**영향받는 코드**: 검색 기능 사용처

---

#### Phase 3: 코드 분석 헬퍼 통합 (우선순위: 🟡 중간)
**목표**: 통합된 파싱 인터페이스

##### 3-1. 파싱 함수 통합
```python
# 현재
parse_file()
extract_functions()
extract_code_elements()
parse_with_snippets()

# 개선안
parse_code(
    path: str,
    elements: List[Literal['functions', 'classes', 'imports', 'all']] = ['all'],
    include_snippets: bool = False
) -> ParseResult
```

##### 3-2. ParseResult 표준화
```python
@dataclass
class ParseResult:
    functions: List[FunctionInfo]
    classes: List[ClassInfo]
    imports: List[ImportInfo]
    tree: ast.AST = None
```

**예상 소요 시간**: 3시간
**영향받는 코드**: 코드 분석 기능 사용처

---

#### Phase 4: 프로젝트 관리 헬퍼 개선 (우선순위: 🟢 낮음)
**목표**: 명확한 프로젝트 관리 인터페이스

##### 4-1. 프로젝트 함수 정리
```python
# 현재
flow_project()
fp()  # 별칭
get_current_project()

# 개선안
# fp()는 별칭으로 유지 (편의성)
switch_project(name: str) -> ProjectInfo
get_project() -> ProjectInfo
list_projects() -> List[ProjectInfo]
```

**예상 소요 시간**: 1시간
**영향받는 코드**: 프로젝트 전환 로직

---

#### Phase 5: 블록 작업 헬퍼 개선 (우선순위: 🟢 낮음)
**목표**: 안전하고 정확한 코드 수정

##### 5-1. 블록 작업 개선
```python
# 현재
replace_block()
insert_block()

# 개선안
modify_code(
    path: str,
    operation: Literal['replace', 'insert', 'delete'],
    target: str,
    content: str = None,
    position: Literal['before', 'after', 'replace'] = 'replace'
) -> ModifyResult
```

**예상 소요 시간**: 2시간
**영향받는 코드**: 코드 수정 기능

---

### 📊 전체 일정 요약

| Phase | 작업 내용 | 우선순위 | 예상 시간 | 의존성 |
|-------|----------|---------|----------|--------|
| 1 | 파일 작업 통합 | 🔴 높음 | 3시간 | 없음 |
| 2 | 검색 작업 통합 | 🟡 중간 | 2시간 | Phase 1 |
| 3 | 코드 분석 통합 | 🟡 중간 | 3시간 | Phase 1 |
| 4 | 프로젝트 관리 | 🟢 낮음 | 1시간 | 없음 |
| 5 | 블록 작업 개선 | 🟢 낮음 | 2시간 | Phase 1 |

**총 예상 시간**: 11시간 (2-3일)

### ⚠️ 리스크 관리

1. **하위 호환성**
   - 기존 함수는 deprecated로 표시하되 유지
   - 마이그레이션 가이드 제공
   - 점진적 전환 지원

2. **테스트 전략**
   - 각 Phase별 단위 테스트 작성
   - 통합 테스트로 전체 검증
   - 실사용 시나리오 테스트

3. **롤백 계획**
   - 각 Phase별 백업 생성
   - Git 브랜치 전략 활용
   - 문제 발생시 즉시 복원

### 🎯 성공 지표

- ✅ 중복 함수 50% 이상 감소
- ✅ 일관된 Result 패턴 적용
- ✅ 에러 처리 표준화
- ✅ 코드 가독성 향상
- ✅ 유지보수성 개선
