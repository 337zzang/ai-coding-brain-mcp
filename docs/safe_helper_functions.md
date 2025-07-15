# Safe Helper Functions 사용 가이드

## 개요
기존 helpers.xxx() 형태의 호출을 안전하고 일관된 반환값을 가진 함수로 변경했습니다.

## 변경사항

### 이전 (에러 가능)
```python
# 타입 에러 발생 가능
result = helpers.parse_with_snippets("file.py")
for snippet in result['snippets']:
    print(snippet.get('name'))  # AttributeError!
```

### 현재 (안전)
```python
# 모든 반환값이 dict로 통일
result = parse_file("file.py")
for func in result['functions']:
    print(func['name'])  # 안전!
```

## 주요 함수 매핑

| 기존 함수 | 새 함수 | 반환 형태 |
|-----------|---------|-----------|
| helpers.parse_with_snippets() | parse_file() | dict with functions, classes |
| helpers.search_code() | search_code() | list of dicts |
| helpers.find_function() | find_function() | list of dicts |
| helpers.git_status() | git_status() | dict with is_clean |
| helpers.replace_block() | replace_block() | dict with success |
| helpers.scan_directory_dict() | scan_directory() | dict with files, dirs |

## 사용 예제

### 파일 분석
```python
# 파일 파싱
parsed = parse_file("myfile.py")
print(f"함수: {len(parsed['functions'])}개")
print(f"클래스: {len(parsed['classes'])}개")

for func in parsed['functions']:
    print(f"{func['name']} - {func['start']}:{func['end']}")
```

### 코드 검색
```python
# 패턴 검색
results = search_code(".", "TODO", "*.py")
for r in results:
    print(f"{r['file']}:{r['line']} - {r['text']}")

# 함수 찾기
funcs = find_function(".", "main")
for f in funcs:
    print(f"Found in {f['file']}:{f['line']}")
```

### Git 작업
```python
# 상태 확인
status = git_status()
if not status['is_clean']:
    print(f"Modified: {status['modified']}")

# 커밋
git_add(".")
git_commit("feat: 새 기능 추가")
git_push()
```

### 디렉토리 스캔
```python
# 현재 디렉토리 스캔
scan = scan_directory()
print(f"총 {scan['total_files']}개 파일")

# Python 파일만 필터
py_files = [f for f in scan['files'] if f['name'].endswith('.py')]
```

## 장점

1. **일관된 반환값**: 모든 함수가 dict 또는 list[dict] 반환
2. **안전한 접근**: 타입 체크와 기본값 처리 자동화
3. **직관적 사용**: helpers. 없이 직접 호출
4. **에러 처리**: 모든 예외를 안전하게 처리

## 원본 사용

필요시 원본 helpers 함수도 여전히 사용 가능:
```python
# 원본 사용
result = helpers.parse_with_snippets("file.py")
```
