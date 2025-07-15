# SafeHelpers 사용 가이드

## 개요
SafeHelpers는 execute_code의 헬퍼 함수들이 반환하는 다양한 타입의 값들을 일관되게 처리할 수 있도록 돕는 래퍼 클래스입니다.

## 주요 문제점
- `parse_with_snippets`: CodeSnippet 객체 리스트 반환 (dict 메서드 사용 불가)
- `search_code`: dict 리스트 반환
- `git_status`: dict 반환
- 각 함수마다 반환 구조가 달라 타입 에러 발생

## 해결 방법

### 1. SafeHelpers 사용 (권장)
```python
# 파일 파싱
parsed = safe.parse_file("myfile.py")
for func in parsed['functions']:
    print(f"{func['name']} - {func['lines']}줄")

# 코드 검색
results = safe.search_in_code(".", "TODO", "*.py")
for r in results:
    print(f"{r['file']}:{r['line']} - {r['text']}")

# Git 상태
status = safe.get_git_status()
if not status['is_clean']:
    print(f"수정된 파일: {status['modified']}")
```

### 2. 반환값 구조 확인
```python
# 구조를 모를 때
result = helpers.some_function()
inspect_return_value(result, "result")
```

### 3. 직접 처리 시
```python
# dict 타입
if isinstance(result, dict):
    value = result.get('key', default_value)

# CodeSnippet 객체
if hasattr(snippet, 'name'):
    name = getattr(snippet, 'name', 'unknown')

# list 타입
if isinstance(results, list):
    for item in results:
        # 처리
```

## 헬퍼 함수별 반환 타입

| 함수명 | 반환 타입 | 주요 구조 |
|--------|-----------|-----------|
| parse_with_snippets | dict | {success, snippets: list[CodeSnippet]} |
| search_code | list[dict] | [{file, line_number, line, context}] |
| git_status | dict | {success, modified, untracked, staged, clean} |
| replace_block | dict | {success, filepath, backup_path, lines_changed} |
| scan_directory_dict | dict | {root, structure: dict, stats} |

## 팁
1. 항상 타입 체크를 먼저 수행
2. dict는 `.get()` 메서드 사용
3. 객체는 `getattr()` 사용
4. 불확실할 때는 `inspect_return_value()` 사용
