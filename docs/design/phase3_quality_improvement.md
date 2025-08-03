
# 📋 Phase 3: 품질 개선 상세 설계

## 🎯 개요
Phase 3는 코드 수정 API의 일관성을 확보하고 체계적인 테스트 스위트를 구축하여 전체적인 코드 품질을 향상시키는 것을 목표로 합니다.

## 🔍 현재 상태 분석

### 1. 코드 수정 API 현황
#### 1.1 AST 기반 함수
- `code.py`:
  - `parse()` - AST 파싱
  - `safe_replace()` - AST/텍스트 혼용 (libcst 사용)
  - `replace()` - safe_replace 래퍼
  - `insert()` - 라인 기반 삽입

- `safe_wrappers.py`:
  - `safe_parse()` - AST 파싱 래퍼
  - `safe_replace()` 호출

#### 1.2 텍스트/정규식 기반 함수
- `search.py`:
  - `find_function()` - 정규식 기반
  - `find_class()` - 정규식 기반
  - `search_code()` - ripgrep 기반

### 2. 테스트 현황
- 테스트 파일: 30개 (분산되어 있음)
- 체계적인 테스트 구조 부재
- 단위 테스트와 통합 테스트 혼재

## 📐 개선 설계

### Task 4: 코드 수정 API 일관성 확보

#### TODO #1: AST 기반 통합 파서 구현 (2시간)
```python
# unified_ast_parser.py
class UnifiedASTParser:
    """모든 AST 작업을 위한 통합 파서"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.content = None
        self.tree = None
        self.cst_tree = None  # libcst용

    def parse(self) -> Dict[str, Any]:
        """파일을 파싱하고 AST/CST 트리 생성"""
        # 1. 파일 읽기
        # 2. AST 파싱 (ast.parse)
        # 3. CST 파싱 (libcst) - 코드 수정용
        # 4. 캐싱 메커니즘

    def find_function(self, name: str) -> Optional[FunctionDef]:
        """AST 기반 함수 검색"""
        # 주석이나 문자열 내용 제외
        # 정확한 함수 정의만 반환

    def find_class(self, name: str) -> Optional[ClassDef]:
        """AST 기반 클래스 검색"""

    def replace_node(self, old_node, new_code: str) -> str:
        """AST 노드 수준에서 코드 교체"""
        # CST 사용하여 공백/주석 보존
        # 실패 시 명확한 오류 반환
```

**구현 상세:**
1. 파일당 한 번만 파싱 (캐싱)
2. AST와 CST 동시 관리
3. 모든 검색/수정 작업을 AST 기반으로 통일
4. 텍스트 폴백 완전 제거

#### TODO #2: 기존 함수 마이그레이션 (1시간)
```python
# code.py 수정
def parse(file_path: str) -> Dict[str, Any]:
    """UnifiedASTParser 사용하도록 변경"""
    parser = UnifiedASTParser(file_path)
    return parser.parse()

def safe_replace(file_path: str, old_code: str, new_code: str) -> Dict[str, Any]:
    """AST 기반으로만 동작, 텍스트 모드 제거"""
    parser = UnifiedASTParser(file_path)
    # 1. old_code를 AST에서 찾기
    # 2. 못 찾으면 명확한 오류 메시지
    # 3. AST 노드 교체
    # 4. 코드 재생성

# search.py 수정
def find_function(name: str, path: str = ".") -> Dict[str, Any]:
    """정규식 대신 AST 사용"""
    # 디렉토리의 모든 .py 파일에 대해
    # UnifiedASTParser로 함수 검색

def find_class(name: str, path: str = ".") -> Dict[str, Any]:
    """정규식 대신 AST 사용"""
```

#### TODO #3: 텍스트 폴백 제거 및 오류 처리 개선 (30분)
```python
# safe_wrappers.py 수정
def safe_replace(file_path: str, old_code: str, new_code: str, 
                text_mode: bool = False) -> Dict[str, Any]:
    if text_mode:
        return {
            'ok': False,
            'error': 'Text mode is deprecated. Use AST-based replacement.',
            'suggestion': 'Ensure old_code exactly matches the AST node.'
        }

    try:
        # AST 기반 교체만 수행
        result = unified_replace(file_path, old_code, new_code)
    except ASTNodeNotFound as e:
        # 구체적인 오류 메시지
        return {
            'ok': False,
            'error': f'Code not found in AST: {str(e)}',
            'suggestion': 'Check for exact match including whitespace',
            'similar_nodes': e.get_similar_nodes()  # 유사한 코드 제안
        }
```

#### TODO #4: 성능 최적화 (30분)
1. **AST 캐싱 시스템**
   ```python
   class ASTCache:
       def __init__(self, max_size: int = 100):
           self.cache = OrderedDict()
           self.max_size = max_size

       def get(self, file_path: str, mtime: float) -> Optional[AST]:
           key = (file_path, mtime)
           if key in self.cache:
               # LRU 업데이트
               self.cache.move_to_end(key)
               return self.cache[key]
           return None
   ```

2. **병렬 처리**
   - 여러 파일 검색 시 concurrent.futures 사용
   - 대용량 프로젝트에서 성능 향상

### Task 5: 테스트 스위트 구축

#### TODO #1: 테스트 구조 설계 (1시간)
```
test/
├── unit/                      # 단위 테스트
│   ├── test_ast_parser.py    # UnifiedASTParser 테스트
│   ├── test_code_api.py      # code.py 함수 테스트
│   ├── test_search_api.py    # search.py 함수 테스트
│   └── test_flow_api.py      # flow 시스템 테스트
├── integration/               # 통합 테스트
│   ├── test_code_modification.py  # 전체 코드 수정 플로우
│   ├── test_project_workflow.py   # 프로젝트 작업 플로우
│   └── test_error_handling.py     # 오류 처리 시나리오
├── fixtures/                  # 테스트용 샘플 파일
│   ├── sample_code.py        # 다양한 Python 구조
│   ├── edge_cases.py         # 엣지 케이스
│   └── malformed.py          # 문법 오류 파일
└── conftest.py               # pytest 설정
```

#### TODO #2: 단위 테스트 작성 (1시간)
```python
# test/unit/test_ast_parser.py
import pytest
from ai_helpers_new.core.unified_ast_parser import UnifiedASTParser

class TestUnifiedASTParser:
    def test_parse_valid_file(self, sample_file):
        parser = UnifiedASTParser(sample_file)
        result = parser.parse()
        assert result['ok'] is True
        assert 'functions' in result['data']
        assert 'classes' in result['data']

    def test_find_function_exact_match(self, sample_file):
        parser = UnifiedASTParser(sample_file)
        parser.parse()
        func = parser.find_function("test_function")
        assert func is not None
        assert func.name == "test_function"

    def test_find_function_in_string_ignored(self, sample_file):
        # 문자열 내의 함수명은 무시되어야 함
        parser = UnifiedASTParser(sample_file)
        parser.parse()
        func = parser.find_function("string_function")
        assert func is None  # 실제 함수가 아님

    def test_replace_node_preserves_formatting(self, sample_file):
        parser = UnifiedASTParser(sample_file)
        original = parser.content

        # 함수 내용 변경
        result = parser.replace_node(
            "def old_func():\n    pass",
            "def old_func():\n    return 42"
        )

        # 들여쓰기와 주석 보존 확인
        assert "    return 42" in result
        assert original.count("\n") == result.count("\n")
```

#### TODO #3: 통합 테스트 작성 (30분)
```python
# test/integration/test_code_modification.py
class TestCodeModificationFlow:
    def test_full_modification_workflow(self, temp_project):
        # 1. 파일 생성
        file_path = temp_project / "module.py"
        h.write(file_path, SAMPLE_CODE)

        # 2. 함수 찾기
        result = h.find_function("process_data", str(temp_project))
        assert result['ok'] is True

        # 3. 코드 수정
        old_code = "def process_data(x):\n    return x * 2"
        new_code = "def process_data(x):\n    return x * 3"
        result = h.safe_replace(str(file_path), old_code, new_code)
        assert result['ok'] is True

        # 4. 검증
        content = h.read(str(file_path))['data']
        assert "return x * 3" in content
        assert "return x * 2" not in content

    def test_error_handling_flow(self, temp_project):
        # 존재하지 않는 코드 수정 시도
        result = h.safe_replace("file.py", "nonexistent", "new")
        assert result['ok'] is False
        assert 'suggestion' in result  # 도움말 제공
```

#### TODO #4: 성능 및 회귀 테스트 (30분)
```python
# test/integration/test_performance.py
import time

class TestPerformance:
    def test_ast_parsing_performance(self, large_file):
        """대용량 파일 파싱 성능 테스트"""
        start = time.time()
        parser = UnifiedASTParser(large_file)
        result = parser.parse()
        elapsed = time.time() - start

        assert result['ok'] is True
        assert elapsed < 1.0  # 1초 이내

    def test_cache_effectiveness(self, sample_file):
        """캐시 효과 테스트"""
        # 첫 번째 파싱
        start1 = time.time()
        h.parse(sample_file)
        time1 = time.time() - start1

        # 두 번째 파싱 (캐시됨)
        start2 = time.time()
        h.parse(sample_file)
        time2 = time.time() - start2

        assert time2 < time1 * 0.1  # 90% 이상 빠름
```

## 🎯 기대 효과

### 1. 일관성 향상
- 모든 코드 분석/수정이 AST 기반으로 통일
- 주석이나 문자열을 실제 코드로 착각하는 오류 제거
- 예측 가능한 동작

### 2. 안정성 강화
- 텍스트 폴백으로 인한 예상치 못한 수정 방지
- 명확한 오류 메시지와 해결 방안 제시
- 체계적인 테스트로 회귀 방지

### 3. 성능 개선
- AST 캐싱으로 중복 파싱 제거
- 병렬 처리로 대규모 프로젝트 지원
- 최적화된 검색 알고리즘

### 4. 유지보수성
- 통합된 파서로 코드 중복 제거
- 명확한 테스트 구조
- 확장 가능한 설계

## ⚠️ 주의사항

### 1. 호환성
- 기존 API 시그니처 유지
- 점진적 마이그레이션
- Deprecation 경고 제공

### 2. 성능
- 대용량 파일 처리 시 메모리 사용량 모니터링
- 캐시 크기 제한
- 병렬 처리 시 CPU 사용률 관리

### 3. 오류 처리
- AST 파싱 실패 시 명확한 피드백
- 부분적 성공 시나리오 처리
- 복구 가능한 오류와 치명적 오류 구분

## 📋 구현 체크리스트

### UnifiedASTParser 구현
□ 기본 파싱 기능
□ 함수/클래스 검색
□ 코드 수정 기능
□ 캐싱 시스템
□ 오류 처리

### API 마이그레이션
□ code.py 함수 수정
□ search.py 함수 수정
□ safe_wrappers.py 수정
□ 호환성 레이어

### 테스트 구축
□ 디렉토리 구조 생성
□ 단위 테스트 작성
□ 통합 테스트 작성
□ 성능 테스트 작성
□ CI/CD 통합

## 📅 일정
- TODO #1: 2시간 (AST 파서 구현)
- TODO #2: 1시간 (API 마이그레이션)
- TODO #3: 30분 (폴백 제거)
- TODO #4: 30분 (성능 최적화)
- 테스트: 3시간

**총 예상 시간: 7시간**
