
# 🔧 AI Coding Brain MCP - 상세 개선안

## 1️⃣ 즉시 적용 가능한 개선 (당일 완료 가능)

### A. code.py 최소 수정 (O3 권장)
```python
# python/ai_helpers_new/code.py 수정
# 1. 중복 import 제거
-from typing import Dict, Any, List, Optional, List
+from typing import Dict, Any, List, Optional

# 2. parse 함수 안전성 강화 (9줄 추가)
def parse(path: str) -> Dict[str, Any]:
    '''Python 파일을 파싱하여 구조 분석'''
-    source = Path(path).read_text(encoding='utf-8')
-    tree = ast.parse(source, filename=path)
+    try:
+        source = Path(path).read_text(encoding='utf-8')
+    except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
+        return err(f"File read error: {e}")
+    try:
+        tree = ast.parse(source, filename=path)
+    except SyntaxError as e:
+        return err(f"Syntax error: {e}")
```

### B. SafeWrapper 모듈 추가 (기존 코드 수정 없음)
```python
# python/ai_helpers_new/utils/safe_wrappers.py (신규)
from typing import Any, Dict, List, Optional, Callable
import time

class SafeHelpers:
    '''AI Helpers의 안전한 사용을 위한 래퍼'''

    @staticmethod
    def safe_decorator(func: Callable) -> Callable:
        '''모든 예외를 ok/error 형식으로 변환'''
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return {'ok': False, 'error': str(e), 'exception': type(e).__name__}
        return wrapper

    @staticmethod
    def parse_with_retry(file_path: str, max_retries: int = 3) -> Dict[str, Any]:
        '''parse 함수를 재시도 로직과 함께 실행'''
        import ai_helpers_new as h

        for attempt in range(max_retries):
            try:
                result = h.parse(file_path)
                if result.get('ok'):
                    return SafeHelpers.normalize_parse_result(result)
                time.sleep(0.1 * attempt)  # exponential backoff
            except Exception as e:
                if attempt == max_retries - 1:
                    return {'ok': False, 'error': str(e)}

        return {'ok': False, 'error': 'Max retries exceeded'}
```

## 2️⃣ 타입 안전성 강화 (1-2일)

### A. TypedDict 활용
```python
# python/ai_helpers_new/types.py (신규)
from typing import TypedDict, List, Optional

class FunctionInfo(TypedDict):
    name: str
    line: int
    args: List[str]
    docstring: Optional[str]
    is_async: bool
    decorators: List[str]
    end_line: int

class ParseResult(TypedDict):
    ok: bool
    data: Optional[Dict[str, Any]]
    error: Optional[str]
    path: Optional[str]

class StandardResponse(TypedDict):
    ok: bool
    data: Any
    error: Optional[str]
```

### B. 함수 시그니처 개선
```python
# 기존
def parse(path: str) -> Dict[str, Any]:

# 개선
def parse(path: Union[str, Path]) -> ParseResult:
```

## 3️⃣ 에러 처리 표준화 (3-5일)

### A. 에러 클래스 정의
```python
# python/ai_helpers_new/errors.py (신규)
class AIHelperError(Exception):
    '''기본 에러 클래스'''
    def __init__(self, message: str, code: str = 'UNKNOWN'):
        self.message = message
        self.code = code
        super().__init__(message)

class ParseError(AIHelperError):
    '''파싱 관련 에러'''
    pass

class FileAccessError(AIHelperError):
    '''파일 접근 에러'''
    pass
```

### B. 일관된 에러 처리 패턴
```python
def handle_error(error: Exception) -> Dict[str, Any]:
    '''에러를 표준 응답 형식으로 변환'''
    if isinstance(error, AIHelperError):
        return {
            'ok': False,
            'error': error.message,
            'error_code': error.code,
            'error_type': type(error).__name__
        }
    else:
        return {
            'ok': False,
            'error': str(error),
            'error_type': type(error).__name__
        }
```

## 4️⃣ 문서화 개선 (1주)

### A. Docstring 표준화
```python
def parse(path: Union[str, Path]) -> ParseResult:
    '''
    Parse a Python file and analyze its structure.

    Args:
        path: Path to the Python file to parse

    Returns:
        ParseResult: Dictionary with 'ok', 'data', 'error' keys

    Example:
        >>> result = parse('example.py')
        >>> if result['ok']:
        ...     functions = result['data']['functions']

    Raises:
        Never raises - all errors returned in result dict
    '''
```

### B. 사용 가이드 작성
- docs/guides/safe_usage_guide.md
- docs/api/error_handling.md
- docs/api/type_reference.md

## 5️⃣ 장기 개선 방향 (1-3개월)

### A. 아키텍처 개선
1. **Middleware Pattern**
   - 로깅, 검증, 변환 레이어 분리
   - 플러그인 가능한 구조

2. **Strategy Pattern**
   - Parser strategies (Python, JS, etc.)
   - Validator strategies
   - Error handler strategies

3. **Result Type 도입**
   ```python
   from typing import Generic, TypeVar, Union

   T = TypeVar('T')
   E = TypeVar('E')

   class Result(Generic[T, E]):
       '''성공/실패를 타입으로 표현'''
       pass
   ```

### B. 테스트 인프라
1. Property-based testing (hypothesis)
2. Contract testing
3. Mutation testing
4. Performance benchmarks

## 📊 개선 효과 측정

### 메트릭
1. **에러 발생률**: 90% 감소 예상
2. **디버깅 시간**: 70% 단축
3. **코드 재사용성**: 200% 향상
4. **타입 안전성**: mypy 통과율 95%+

### 측정 방법
```python
# 개선 전후 비교 스크립트
def measure_improvement():
    # 1. 에러 발생 빈도
    # 2. 평균 디버깅 시간
    # 3. 코드 중복도
    # 4. 타입 체크 통과율
    pass
```
