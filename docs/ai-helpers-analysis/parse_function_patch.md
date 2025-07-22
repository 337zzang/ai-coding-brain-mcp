# Parse 함수 즉시 적용 가능한 개선 패치

## 1. async 함수 지원 추가

### 수정 위치: Line 36
```python
# 기존 코드
if isinstance(node, ast.FunctionDef):

# 수정 코드
if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
```

### 추가 정보 수집
```python
# 함수 정보에 is_async 플래그 추가
functions.append({
    'name': node.name,
    'line': node.lineno,
    'args': [arg.arg for arg in node.args.args],
    'is_async': isinstance(node, ast.AsyncFunctionDef)  # 추가
})
```

## 2. 메서드에도 async 지원 추가

### 수정 위치: Line 46
```python
# 기존 코드
if isinstance(item, ast.FunctionDef):

# 수정 코드  
if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
```

## 3. 테스트 코드
```python
# async 함수가 포함된 테스트
async def test_async():
    return "async result"

# 파싱 후 확인
result = h.parse('test.py')
# is_async 플래그로 async 함수 구분 가능
```

이 최소 패치만으로도 async 함수 지원이 가능합니다.
