# SearchResult 사용 가이드

## 개요
SearchResult는 검색 결과를 관리하는 향상된 인터페이스입니다.
기존 List 방식과 100% 호환되면서 추가 기능을 제공합니다.

## 적용된 함수들

### search_ops.py
- `search_code(directory, pattern, file_pattern, case_sensitive) -> SearchResult`
- `find_function(directory, function_name) -> SearchResult`
- `find_class(directory, class_name) -> SearchResult`
- `safe_search_code(...) -> SearchResult`
- `safe_find_function(...) -> SearchResult`
- `safe_find_class(...) -> SearchResult`

### 사용 예시

```python
from ai_helpers_v2.search_ops import search_code, find_function

# 기본 사용법 (기존과 동일)
result = search_code(".", "TODO", "*.py")
for match in result:
    print(f"{match['file']}:{match['line_number']} - {match['line']}")

# 새로운 기능들
print(f"총 {result.count}개 발견")  # 총 개수

# 파일별 그룹화
for file, matches in result.by_file().items():
    print(f"{file}: {len(matches)}개")

# 필터링
python_only = result.filter(lambda m: m['file'].endswith('.py'))
first_10 = result.limit(10)

# 파일 목록만
files = result.files()
```

## SearchResult 메서드

- `count`: 총 결과 수
- `by_file()`: 파일별로 그룹화된 딕셔너리 반환
- `files()`: 매치가 있는 파일 목록
- `filter(predicate)`: 조건에 맞는 결과만 필터링
- `limit(n)`: 처음 n개 결과만 반환

## 리스트 호환성
SearchResult는 리스트처럼 동작합니다:
- `len(result)` 
- `result[0]`
- `for match in result`
- `if result:` (비어있는지 확인)

## Safe 버전
모든 검색 함수는 safe 버전이 있습니다:
- 예외가 발생해도 빈 SearchResult 반환
- 에러 메시지 출력

## 참고: search_files
`search_files()`는 파일명 검색용으로 여전히 List[str]을 반환합니다.
코드 내용 검색과는 용도가 다르므로 SearchResult를 사용하지 않습니다.
