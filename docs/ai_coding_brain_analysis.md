# ai-coding-brain-mcp 코드 분석 결과

## 상세 분석 결과

### 1. 발견된 핵심 문제: 매개변수 순서 혼란

#### 문제의 3중 구조:

1. **search.py (Line 495)**
   ```python
   def files(pattern="*", path=".", max_depth=None, exclude_patterns=None):
       # pattern이 첫 번째, path가 두 번째
   ```

2. **search.py (Line 543)**
   ```python
   search_files = lambda path=".", pattern="*", **kwargs: search.files(pattern, path, **kwargs)
   # path를 첫 번째로 받아서, pattern과 순서를 바꿔 files()에 전달
   ```

3. **facade_safe.py (SearchNamespace)**
   ```python
   self.files = self._safe_getattr('search_files')  # search_files를 찾으려 하지만...
   ```

#### 실제 작동 방식:
- h.search.files는 search.py의 files 함수를 직접 가리킴
- files(pattern, path) 순서로 동작
- 사용자가 h.search.files("*.py", ".")로 호출하면 pattern과 path가 반대로 해석됨

### 2. 테스트 결과:
- OK: h.search.files(".", "*.py") = 164개 파일 (올바른 순서)
- FAIL: h.search.files("*.py", ".") = 0개 파일 (잘못된 순서)
- OK: h.search.files(path=".", pattern="*.py") = 164개 파일 (키워드 인자)

---

## 개선 제안

### 1. 코드 개선 사항

#### A. 즉시 적용 가능한 수정 (Quick Fix)
```python
# search.py Line 495 수정
def files(path=".", pattern="*", max_depth=None, exclude_patterns=None):
    # path를 첫 번째로 변경
    result = list(search_files_generator(path, pattern, max_depth, exclude_patterns))
    return {'ok': True, 'data': result}
```

#### B. Lambda 함수 제거
```python
# search.py Line 543 제거
# search_files = lambda... 삭제

# 대신 직접 함수 정의
def search_files(path=".", pattern="*", **kwargs):
    return files(path, pattern, **kwargs)
```

#### C. Facade 수정
```python
# facade_safe.py SearchNamespace 수정
class SearchNamespace(SafeNamespace):
    def __init__(self):
        super().__init__('search')
        # files를 search_files 대신 직접 바인딩
        self.files = self._safe_getattr('files') or self._safe_getattr('search_files')
```

#### D. 일관성 개선
- 모든 검색 함수를 (path, pattern) 순서로 통일
- 또는 키워드 전용 인자로 강제: def files(*, path=".", pattern="*")

### 2. 유저 프리퍼런스 개선 사항

#### A. 사용 지침 명확화
```markdown
## search 모듈 사용법

### 올바른 사용법
# 방법 1: 올바른 순서 (path, pattern)
h.search.files(".", "*.py")
h.search.files("src", "*.js")

# 방법 2: 키워드 인자 사용 (권장)
h.search.files(path=".", pattern="*.py")
h.search.files(pattern="*.py", path=".")  # 순서 무관

### 잘못된 사용법
# pattern을 먼저 쓰면 실패
h.search.files("*.py", ".")  # 빈 결과 반환
```

#### B. 에러 감지 및 자동 수정
```python
def smart_search_files(arg1=".", arg2="*", **kwargs):
    # 첫 번째 인자가 패턴처럼 보이면 순서 교체
    if '*' in arg1 or '.' in arg1.split('/')[-1]:
        if '*' not in arg2:
            # 순서가 반대일 가능성
            print(f"WARNING: 매개변수 순서 확인: path='{arg2}', pattern='{arg1}'")
            arg1, arg2 = arg2, arg1

    return original_search_files(arg1, arg2, **kwargs)
```

#### C. 디버깅 도움말
```
execute_code 실행 시 주의사항:
1. dict 반환값 슬라이싱: data['key'] 먼저 접근
2. search.files: (path, pattern) 순서 준수
3. 빈 결과 시: 매개변수 순서 확인
```

---

## 핵심 요약

### 문제점:
1. 매개변수 순서 불일치: files(pattern, path) vs search_files(path, pattern)
2. Lambda 함수로 인한 혼란: 순서 변환 과정이 숨겨짐
3. 3중 레이어 구조: search.py > facade > __init__.py

### 해결책:
1. 즉시: 키워드 인자 사용 권장
2. 단기: files 함수 매개변수 순서 수정
3. 장기: 전체 API 일관성 개선

### 교훈:
- API 설계 시 일관성이 가장 중요
- Lambda 함수로 매개변수 순서를 바꾸는 것은 혼란 유발
- 명시적인 것이 암시적인 것보다 낫다 (Zen of Python)
