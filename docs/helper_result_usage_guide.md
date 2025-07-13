# HelperResult 올바른 사용법

## 문제점
`HelperResult` 객체의 `data` 속성에 직접 문자열 메서드를 호출하면 에러가 발생합니다.

```python
# ❌ 잘못된 예
result = helpers.read_file("file.py")
lines = result.data.split('\n')  # AttributeError: 'dict' object has no attribute 'split'
```

## 해결 방법

### 1. read_file의 경우
`read_file`은 dict를 반환하며, 실제 내용은 'content' 키에 있습니다.

```python
# ✅ 올바른 방법
result = helpers.read_file("file.py")
if result.ok:
    content = result.data.get('content', '')
    lines = content.split('\n')
```

### 2. get_data() 메서드 사용 (권장)
모든 HelperResult는 `get_data()` 메서드를 제공합니다.

```python
# ✅ 가장 안전한 방법
result = helpers.read_file("file.py")
if result.ok:
    file_data = result.get_data({})
    content = file_data.get('content', '')
    lines = content.split('\n')
```

### 3. 다른 helper 함수들
각 함수마다 반환하는 데이터 구조가 다릅니다.

```python
# search_code_content의 경우
result = helpers.search_code_content("path", "pattern", "*.py")
if result.ok:
    search_data = result.get_data({})
    results = search_data.get('results', [])
    for match in results:
        print(f"Found at {match['file']}:{match['line']}")

# scan_directory_dict의 경우  
result = helpers.scan_directory_dict(".")
if result.ok:
    scan_data = result.get_data({})
    files = scan_data.get('files', [])
    directories = scan_data.get('directories', [])
```

## 핵심 원칙
1. **항상 result.ok 확인**: 성공 여부를 먼저 확인
2. **get_data() 사용**: 가장 안전한 데이터 접근 방법
3. **구조 확인**: 각 함수의 반환 구조를 이해하고 사용
4. **기본값 제공**: get() 메서드로 안전하게 접근

## 실제 코드에서의 활용
```python
# 파일 읽기와 처리
def process_file(filename):
    result = helpers.read_file(filename)
    if not result.ok:
        print(f"파일 읽기 실패: {result.error}")
        return None

    # content 키로 접근
    content = result.data.get('content', '')

    # 또는 get_data() 사용
    file_data = result.get_data({})
    content = file_data.get('content', '')

    # 내용 처리
    lines = content.split('\n')
    return lines
```
