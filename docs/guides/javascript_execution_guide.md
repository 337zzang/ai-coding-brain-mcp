# JavaScript 실행 메커니즘 가이드

## 개요
웹 자동화에서 JavaScript 코드를 안전하게 실행하고 결과를 반환하는 메커니즘을 제공합니다.

## 주요 기능

### 1. JavaScriptExecutor 클래스
- **위치**: `web_automation_manager.py`
- **목적**: JavaScript 실행의 중앙 관리 및 보안 강화
- **주요 메서드**:
  - `validate_script()`: 기본 스크립트 검증
  - `validate_script_extended()`: 확장된 검증 (화이트리스트 모드 지원)
  - `execute()`: 안전한 스크립트 실행
  - `create_sandbox_wrapper()`: 샌드박스 환경 생성

### 2. 웹 자동화 함수

#### web_evaluate(script, arg=None, strict=False)
페이지에서 JavaScript 표현식을 실행하고 결과를 반환합니다.

```python
# 페이지 제목 가져오기
result = web_evaluate("document.title")
print(result["data"])  # "Example Page"

# 인자 전달
result = web_evaluate("return arg.toUpperCase()", "hello")
print(result["data"])  # "HELLO"

# 엄격 모드 (화이트리스트 검증)
result = web_evaluate("document.querySelector('.btn')", strict=True)
```

#### web_execute_script(script, *args, sandboxed=True)
복잡한 JavaScript 코드를 실행합니다.

```python
# 모든 링크 URL 수집
script = """
const links = document.querySelectorAll('a');
return Array.from(links).map(a => ({
    text: a.textContent,
    href: a.href
}));
"""
result = web_execute_script(script)
links = result["data"]

# 인자를 사용한 계산
result = web_execute_script(
    "return arguments[0] * arguments[1]",
    10, 20
)
print(result["data"])  # 200
```

#### web_evaluate_element(selector, script)
특정 요소에 대해 JavaScript를 실행합니다.

```python
# 버튼 비활성화
web_evaluate_element("button.submit", "element.disabled = true")

# 입력 필드 값 가져오기
result = web_evaluate_element("#email", "return element.value")
email = result["data"]
```

#### web_wait_for_function(script, timeout=30000, polling=100)
JavaScript 조건이 true가 될 때까지 대기합니다.

```python
# 페이지 완전 로드 대기
web_wait_for_function("document.readyState === 'complete'")

# 특정 요소 나타날 때까지 대기
web_wait_for_function(
    "document.querySelector('.loading').style.display === 'none'",
    timeout=10000
)

# 데이터 로드 완료 대기
web_wait_for_function(
    "document.querySelectorAll('.item').length >= 10"
)
```

## 보안 기능

### 1. 스크립트 검증
- `eval()`, `Function()` 등 위험한 패턴 차단
- XSS 공격 벡터 감지
- 무한 루프 패턴 방지

### 2. 샌드박스 실행
- 제한된 전역 변수 접근
- 실행 시간 제한 (기본 5초)
- 에러 격리

### 3. 화이트리스트 모드
엄격 모드 사용 시 안전한 DOM API만 허용:
- querySelector, querySelectorAll
- getAttribute, textContent
- getBoundingClientRect 등

## 실전 예제

### 데이터 스크래핑
```python
# 1. 브라우저 시작
web_start()
web_goto("https://example.com/products")

# 2. 제품 정보 추출
script = """
const products = document.querySelectorAll('.product');
return Array.from(products).map(p => ({
    name: p.querySelector('.name').textContent,
    price: p.querySelector('.price').textContent,
    image: p.querySelector('img').src
}));
"""
result = web_execute_script(script)
products = result["data"]

# 3. 다음 페이지 버튼 클릭 가능 여부 확인
can_continue = web_evaluate(
    "!document.querySelector('.next-page').disabled"
)["data"]
```

### 동적 콘텐츠 처리
```python
# AJAX 로딩 대기
web_wait_for_function(
    "document.querySelector('.spinner').style.display === 'none'"
)

# 무한 스크롤 처리
for i in range(5):
    # 스크롤 다운
    web_execute_script("window.scrollTo(0, document.body.scrollHeight)")

    # 새 콘텐츠 로드 대기
    web_wait_for_function(
        f"document.querySelectorAll('.item').length > {i * 20}",
        timeout=5000
    )
```

### 폼 자동화
```python
# 폼 필드 채우기
web_evaluate_element("#username", "element.value = 'user123'")
web_evaluate_element("#password", "element.value = 'pass456'")

# 체크박스 선택
web_evaluate_element("#agree", "element.checked = true")

# 폼 제출
web_evaluate_element("form", "element.submit()")
```

## 에러 처리

모든 함수는 표준 Response 형식을 반환합니다:

```python
{
    "ok": bool,          # 성공 여부
    "data": Any,         # 성공 시 결과
    "error": str,        # 실패 시 에러 메시지
    "error_type": str,   # 에러 타입
    "stack": str         # JavaScript 에러 스택 (해당 시)
}
```

### 에러 처리 예제
```python
result = web_evaluate("invalid.syntax.error")
if not result["ok"]:
    print(f"Error: {result['error']}")
    if result.get("stack"):
        print(f"Stack trace: {result['stack']}")
```

## 성능 고려사항

1. **스크립트 캐싱**: 반복 사용되는 스크립트는 변수에 저장
2. **배치 처리**: 여러 요소는 한 번에 처리
3. **적절한 대기**: polling 간격 조정으로 CPU 사용 최적화

## 디버깅 팁

1. **콘솔 로그 확인**:
```python
# 브라우저 콘솔 메시지 가져오기
web_execute_script("console.log('Debug message')")
```

2. **단계별 실행**:
```python
# 각 단계 결과 확인
step1 = web_evaluate("document.querySelector('.target')")
print(f"Step 1 result: {step1}")
```

3. **스크립트 검증**:
```python
from web_automation_manager import JavaScriptExecutor
js = JavaScriptExecutor()
is_safe, error = js.validate_script_extended(your_script, strict_mode=True)
```
