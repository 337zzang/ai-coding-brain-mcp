# Search API 마이그레이션 가이드

## 1. 변경 사항 요약

### 기존 API → 새 API 매핑
- `search_files_advanced()` → `list_file_paths()`
- `search_code_content()` → `grep_code()`
- `scan_directory_dict()` → `scan_dir()`

### 반환 형식 표준화
- **Path List 형식**: `{'paths': [str, ...]}`
- **Grouped Dict 형식**: `{'results': {filepath: [matches]}}`

## 2. 마이그레이션 예제

### 예제 1: 파일 검색 (search_files_advanced → list_file_paths)

**기존 코드:**
```python
result = helpers.search_files_advanced('.', '*.py')
if result.ok:
    for file_info in result.data['results']:
        print(file_info['path'])
```

**새 코드:**
```python
result = helpers.list_file_paths('.', '*.py')
if result.ok:
    for path in result.data['paths']:
        print(path)
```

### 예제 2: 코드 검색 (search_code_content → grep_code)

**기존 코드 (잘못된 사용):**
```python
result = helpers.search_code_content('.', 'TODO', '*.py')
if result.ok:
    # 🐛 버그: results는 list인데 dict처럼 사용
    for file, matches in result.data['results'].items():
        print(file)
```

**새 코드 (올바른 사용):**
```python
result = helpers.grep_code('.', 'TODO', '*.py')
if result.ok:
    # ✅ results는 dict이므로 .items() 사용 가능
    for filepath, matches in result.data['results'].items():
        print(f"{filepath}: {len(matches)} matches")
        for match in matches:
            print(f"  L{match['line_number']}: {match['line']}")
```

### 예제 3: 디렉토리 스캔 (scan_directory_dict → scan_dir)

**기존 코드:**
```python
data = helpers.scan_directory_dict('.')
for file in data['files']:
    # 🐛 file은 dict인데 string 메서드 사용 시도
    if file.endswith('.py'):  # AttributeError!
        print(file)
```

**새 코드 (옵션 1 - Dict 형식):**
```python
result = helpers.scan_dir('.', as_dict=True)
if result.ok:
    for file_info in result.data['files']:
        if file_info['name'].endswith('.py'):
            print(f"{file_info['path']} ({file_info['size']} bytes)")
```

**새 코드 (옵션 2 - Path List 형식):**
```python
result = helpers.scan_dir('.', as_dict=False)
if result.ok:
    for path in result.data['paths']:
        if path.endswith('.py'):
            print(path)
```

## 3. 호환성 래퍼 사용

기존 코드를 즉시 변경하기 어려운 경우, 호환성 래퍼를 사용할 수 있습니다:

```python
from search_helpers_standalone import (
    search_files_advanced_compat,
    search_code_content_compat
)

# 기존 코드와 동일한 인터페이스
result = search_files_advanced_compat('.', '*.py')
```

## 4. 성능 개선 팁

1. **필요한 정보만 요청**: 파일 경로만 필요하면 `list_file_paths()` 사용
2. **max_results 활용**: 대량 파일 검색 시 제한 설정
3. **ignore_patterns 활용**: 불필요한 디렉토리 제외

## 5. 일반적인 오류 해결

### TypeError: 'list' object has no attribute 'items'
- 원인: `search_code_content` 결과를 dict로 착각
- 해결: `grep_code()` 사용 또는 리스트로 순회

### AttributeError: 'dict' object has no attribute 'endswith'
- 원인: `scan_directory_dict` 결과의 file이 dict임
- 해결: `file['name'].endswith()` 또는 `scan_dir(as_dict=False)` 사용
