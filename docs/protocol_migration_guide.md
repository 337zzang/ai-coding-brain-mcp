# 프로토콜 기반 시스템 마이그레이션 가이드

## 변경사항

### 1. 모든 실행이 자동 추적됨
- 실행 ID 자동 생성
- 입력/출력 자동 로깅
- 성능 메트릭 자동 수집

### 2. 캐싱 내장
- 5분간 자동 캐싱
- 동일한 작업 반복시 즉시 반환

### 3. 병렬 실행 지원
```python
results = await helpers.parallel_operations([
    {'name': 'read_1', 'func': helpers.read_file, 'args': ['file1.txt']},
    {'name': 'read_2', 'func': helpers.read_file, 'args': ['file2.txt']}
])
```

### 4. 실행 히스토리
```python
history = helpers.get_execution_history()
metrics = helpers.get_metrics()
```

## 마이그레이션 방법

1. import 변경:
```python
# 기존
from ai_helpers import helpers

# 새로운 방식
from ai_helpers.protocol_based_helpers import create_protocol_helpers
helpers = create_protocol_helpers()
```

2. 메서드는 동일하게 사용 가능
3. 추가 기능 활용 가능
