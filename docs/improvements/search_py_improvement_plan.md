
# Search.py 개선안 문서

## 🚨 즉시 수정 필요한 치명적 버그 (4개)

### 1. get_statistics 함수 중복 정의
**위치**: Line 495, Line 730
**문제**: 같은 함수가 2번 정의되어 첫 번째 구현이 무시됨
**해결**:
```python
# Line 495-729 삭제 (첫 번째 불완전한 구현)
# Line 730의 두 번째 구현만 유지 (include_tests 파라미터 포함)
```

### 2. find_in_file의 잘못된 외부 의존성
**위치**: Line 482
**문제**: h.search_code() 호출 (NameError 발생)
**해결**:
```python
# Before (Line 482):
result = h.search_code(pattern, os.path.dirname(file_path) or '.', ...)

# After:
result = search_code(pattern, os.path.dirname(file_path) or '.', ...)
```

### 3. AST 함수의 잘못된 mode 반환
**위치**: Line 267 (_find_function_ast), Line 377 (_find_class_ast)
**문제**: AST 검색인데 'mode': 'regex'로 반환
**해결**:
```python
# Before:
'mode': 'regex'

# After:
'mode': 'ast'
```

### 4. AST 소스 추출 개선 (Python 3.8+)
**문제**: 수동 들여쓰기 추적으로 부정확
**해결**:
```python
# _find_function_ast와 _find_class_ast에서:
import sys

# 함수/클래스 정의 추출 부분
if sys.version_info >= (3, 8):
    # Python 3.8+ - 정확한 소스 추출
    definition = ast.get_source_segment(content, node)
    if definition:
        results.append({
            'file': file_path,
            'name': node.name,
            'line': node.lineno,
            'definition': definition,
            'mode': 'ast'
        })
else:
    # Python 3.7 이하 - 기존 방식 유지 (개선된 버전)
    # 현재 구현 유지하되 max_lines 제한 제거
```

## 🚀 성능 개선안 (3개)

### 1. 제너레이터 기반 파일 탐색
```python
def search_files_generator(path, pattern, max_depth=None):
    """파일을 발견하는 즉시 yield하는 제너레이터"""
    # ...탐색 로직...
    for file in matching_files:
        yield file  # 즉시 반환

# search_code에서 사용:
for file_path in search_files_generator(path, file_pattern):
    # 파일 내용 검색
    if len(matches) >= max_results:
        break  # 조기 종료
```

### 2. 메모리 효율적 파일 읽기
```python
# grep 함수 개선
def grep(pattern, path=".", context=2, use_regex=False):
    # ...
    with open(file_path, 'r', encoding='utf-8') as f:
        # 전체 로드 대신 줄 단위 읽기
        from collections import deque
        before_context = deque(maxlen=context)

        for line_num, line in enumerate(f, 1):
            if match_found:
                # 매치 처리
                pass
            before_context.append(line)  # 자동으로 오래된 줄 제거
```

### 3. AST 검색 파일 제한 제거
```python
# Before:
for file_path in py_files_result['data'][:100]:  # 임의 제한

# After:
for file_path in py_files_result['data']:  # 모든 파일 검색
```

## 🛡️ 견고성 개선 (3개)

### 1. 특정 예외만 처리
```python
# Before:
try:
    content = file_path.read_text(encoding='utf-8')
except Exception:
    continue

# After:
try:
    content = file_path.read_text(encoding='utf-8')
except (PermissionError, UnicodeDecodeError, IOError) as e:
    # 로깅 또는 건너뛰기
    continue
except Exception as e:
    # 예상치 못한 오류는 로깅
    import logging
    logging.warning(f"Unexpected error reading {file_path}: {e}")
    continue
```

### 2. 바이너리 파일 감지 개선
```python
def is_binary_file(file_path):
    """널 바이트로 바이너리 파일 감지"""
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(8192)  # 처음 8KB만 확인
            return b'\x00' in chunk
    except:
        return True  # 읽기 실패시 바이너리로 간주
```

### 3. 캐싱 적용
```python
from functools import lru_cache

@lru_cache(maxsize=32)
@_register_cache
def get_statistics(path: str = ".", include_tests: bool = False):
    # 비용이 큰 통계 계산에 캐시 적용
    ...
```

## 💡 추가 개선사항

1. **대소문자 구분 옵션**:
   - case_sensitive 파라미터 추가

2. **파일 패턴 유연성**:
   - grep에 file_pattern 파라미터 추가

3. **테스트 파일 감지 개선**:
   - 'test' 문자열 포함 대신 test_*.py, *_test.py 패턴 사용

4. **함수 통합**:
   - grep 기능을 search_code에 통합 (use_regex, context 파라미터)
