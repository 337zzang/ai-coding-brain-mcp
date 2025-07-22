# AI Helpers Parse 함수 상세 분석 보고서

## 1. 개요
ai_helpers_new 모듈의 parse 함수를 상세 분석하여 문제점을 파악하고 개선 방안을 제시합니다.

## 2. 현재 구현 분석

### 2.1 위치 및 구조
- **파일**: `python/ai_helpers_new/code.py`
- **함수명**: `parse(path: str) -> Dict[str, Any]`
- **기능**: Python 파일을 파싱하여 함수와 클래스 정보 추출

### 2.2 현재 기능
✅ 지원하는 기능:
- 일반 함수 파싱 (ast.FunctionDef)
- 클래스 파싱 (ast.ClassDef)
- 클래스 메서드 이름 추출
- import 문 파싱
- 함수 인자 이름 추출

❌ 지원하지 않는 기능:
- async 함수 (ast.AsyncFunctionDef)
- 메서드의 인자 정보
- 데코레이터 정보
- 전역 변수/상수
- docstring
- 타입 힌트
- 상속 정보
- 람다 함수

## 3. 테스트 결과

### 3.1 기본 테스트
```python
# 테스트 코드
class TestClass:
    def __init__(self, name):
        self.name = name

    @property
    def property1(self):
        return self.name

async def async_function():
    return "async"

GLOBAL_VAR = 42
```

**파싱 결과**:
- ✅ TestClass 파싱됨
- ✅ __init__, property1 메서드 이름 추출됨
- ❌ async_function 누락
- ❌ GLOBAL_VAR 누락
- ❌ @property 데코레이터 정보 누락
- ❌ 메서드 인자 정보 누락

### 3.2 향상된 테스트
더 복잡한 코드로 테스트한 결과:
- 전체 함수 중 50%만 파싱 (async 함수 누락)
- 타입 정보 0% 수집
- 데코레이터 정보 0% 수집
- 전역 변수 0% 수집

## 4. 문제점 상세 분석

### 4.1 async 함수 미지원
```python
# 현재 코드
if isinstance(node, ast.FunctionDef):  # async 함수 누락
    functions.append(...)

# 개선 필요
if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
    functions.append(...)
```

### 4.2 메서드 인자 정보 누락
```python
# 현재: 메서드 이름만 수집
methods.append(item.name)

# 개선 필요: 인자 정보도 수집
methods.append({
    'name': item.name,
    'args': [arg.arg for arg in item.args.args],
    'decorators': ...
})
```

### 4.3 데코레이터 정보 누락
- node.decorator_list를 확인하지 않음
- @property, @staticmethod 등 구분 불가

### 4.4 전역 변수 미지원
- ast.Assign 노드를 처리하지 않음
- 상수와 변수 구분 없음

## 5. 개선 방안

### 5.1 즉시 적용 가능한 개선
1. **async 함수 지원 추가**
   - ast.AsyncFunctionDef 처리 추가
   - is_async 플래그 추가

2. **메서드 상세 정보 수집**
   - 인자 리스트 추가
   - 데코레이터 정보 추가

### 5.2 중장기 개선 사항
1. **타입 힌트 지원**
   - 함수/메서드의 인자 타입
   - 반환 타입

2. **전역 변수 파싱**
   - 상수/변수 구분
   - 타입 추정

3. **docstring 추출**
   - ast.get_docstring() 활용

4. **상속 정보**
   - 클래스의 부모 클래스 정보

## 6. 개선된 parse 함수 예시

enhanced_parse 함수에서 구현한 개선 사항:
- ✅ async 함수 지원
- ✅ 타입 힌트 추출
- ✅ 데코레이터 정보
- ✅ 전역 변수 파싱
- ✅ docstring 추출
- ✅ 상속 정보
- ✅ 메서드 인자 정보

## 7. 관련 함수 분석

### 7.1 search_code 함수
- **시그니처**: `search_code(pattern, path='.', file_pattern='*', max_results=100)`
- **반환**: 리스트 (SearchResult 객체가 아님)
- **구조**: `[{'file': str, 'line': int, 'text': str, 'match': str}, ...]`

### 7.2 누락된 함수들
ai_helpers_new에 없는 함수들:
- extract_code_elements
- replace_function
- replace_method
- safe_parse_file

## 8. 권장 사항

1. **단기 개선**
   - parse 함수에 async 함수 지원 추가
   - 메서드 인자 정보 수집 추가

2. **API 확장**
   - enhanced_parse 같은 고급 파서 추가
   - extract_functions, extract_classes 등 세분화된 API

3. **문서화**
   - 각 함수의 제한사항 명시
   - 사용 예제 추가

## 9. 결론
현재 parse 함수는 기본적인 기능만 제공하며, 현대적인 Python 코드의 많은 기능을 지원하지 않습니다. 
특히 async 함수, 타입 힌트, 데코레이터 등 중요한 정보가 누락되어 코드 분석 도구로서의 
활용도가 제한적입니다. 단계적인 개선을 통해 더 강력한 코드 분석 도구로 발전시킬 필요가 있습니다.

## 작성일
2025-07-22
