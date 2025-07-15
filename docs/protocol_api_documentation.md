# 프로토콜 기반 헬퍼 시스템 API 문서

## 개요
AI Coding Brain MCP v2.0 - 프로토콜 기반 실행 시스템

모든 실행이 자동으로 추적되고, 캐싱되며, 최적화됩니다.

## 핵심 기능

### 1. 자동 실행 추적
```python
# 모든 메서드 호출이 자동으로 추적됨
result = helpers.read_file("example.txt")
# 실행 ID, 시간, 입력, 출력이 모두 기록됨
```

### 2. 스마트 캐싱
```python
# 동일한 작업은 캐시에서 즉시 반환
result1 = helpers.search_in_files("pattern")  # 실제 실행
result2 = helpers.search_in_files("pattern")  # 캐시에서 반환
```

### 3. 병렬 실행
```python
# 여러 작업을 동시에 실행
results = await helpers.parallel_operations([
    {'name': 'task1', 'func': helpers.read_file, 'args': ['file1.txt']},
    {'name': 'task2', 'func': helpers.scan_directory, 'args': ['.']}
])
```

### 4. 성능 모니터링
```python
# 실행 히스토리 및 메트릭 조회
history = helpers.get_execution_history()
metrics = helpers.get_metrics()
```

## 주요 메서드

### 파일 작업
- `read_file(filepath)` - 파일 읽기
- `write_file(filepath, content)` - 파일 쓰기
- `create_file(filepath, content)` - 파일 생성
- `scan_directory(path)` - 디렉토리 스캔

### 검색 작업
- `search_in_files(pattern, file_pattern)` - 파일 내용 검색
- `search_files(pattern)` - 파일명 검색

### 워크플로우 작업
- `execute_task(name, description, steps)` - 작업 실행
- `get_execution_history(limit)` - 실행 히스토리
- `get_metrics()` - 성능 메트릭

### 최적화된 코드 실행
```python
from ai_helpers.protocol.optimized_executor import execute_code

result = execute_code("""
# 여기에 Python 코드 작성
for i in range(10):
    print(i)
result = sum(range(10))
""")

print(result['result'])  # {'result': 45}
```

## 성능 최적화

1. **컴파일 캐싱**: 자주 실행되는 코드는 컴파일된 상태로 캐싱
2. **병렬 실행**: 독립적인 작업은 자동으로 병렬 처리
3. **결과 캐싱**: 동일한 입력에 대한 결과는 5분간 캐싱

## 마이그레이션 가이드

### 기존 코드
```python
from ai_helpers import helpers
result = helpers.read_file("file.txt")
```

### 새 코드 (자동 추적 포함)
```python
from ai_helpers import helpers  # 동일한 import
result = helpers.read_file("file.txt")  # 자동으로 프로토콜 적용
```

변경 없이 모든 기능이 향상됩니다!
