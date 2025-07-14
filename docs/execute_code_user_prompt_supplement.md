
## 🚀 execute_code 고급 활용을 위한 유저 프롬프트 보충 사항

### 1. 세션 관리 명령어
```python
# 세션 상태 확인
if 'session_initialized' not in globals():
    # 초기화 코드
    session_initialized = True
    global_cache = {}
    execution_count = 0

# 세션 카운터
execution_count = globals().get('execution_count', 0) + 1
```

### 2. 대규모 작업 분할 패턴
```python
# 작업을 여러 실행으로 분할
# 첫 번째 실행: 데이터 로드
if 'data_loaded' not in globals():
    data = load_large_dataset()
    data_loaded = True
    print("데이터 로드 완료")

# 두 번째 실행: 처리
if 'data_loaded' in globals() and 'processed' not in globals():
    results = process_data(data)
    processed = True
```

### 3. 스마트 캐싱 패턴
```python
# 전역 캐시 활용
if 'global_cache' not in globals():
    global_cache = {}

def cached_operation(key, compute_func):
    if key in global_cache:
        print(f"캐시 히트: {key}")
        return global_cache[key]

    result = compute_func()
    global_cache[key] = result
    return result
```

### 4. 비동기 작업 패턴
```python
# 비동기 작업을 동기적으로 실행
import asyncio

async def async_workflow():
    tasks = [
        async_task1(),
        async_task2(),
        async_task3()
    ]
    return await asyncio.gather(*tasks)

# 실행
results = asyncio.run(async_workflow())
```

### 5. 에러 복구 패턴
```python
# 체크포인트 기반 복구
if 'checkpoint' in globals():
    print(f"체크포인트에서 재개: {checkpoint['stage']}")
    data = checkpoint['data']
else:
    # 처음부터 시작
    data = initial_data
    checkpoint = {'stage': 'start', 'data': data}
```

### 6. 동적 코드 업데이트
```python
# 함수 동적 재정의
def update_function(func_name, new_code):
    exec(new_code, globals())
    print(f"함수 업데이트: {func_name}")
```

### 7. 메모리 효율적 처리
```python
# 대용량 데이터 스트림 처리
def process_in_chunks(data_source, chunk_size=1000):
    for i in range(0, len(data_source), chunk_size):
        chunk = data_source[i:i+chunk_size]
        yield process_chunk(chunk)
```

### 8. 컨텍스트 압축
```python
# 토큰 절약을 위한 결과 압축
def compress_results(results):
    return {
        'summary': summarize(results),
        'key_metrics': extract_metrics(results),
        'sample': results[:5]  # 샘플만 유지
    }
```

### 9. 병렬 맵리듀스 패턴
```python
from concurrent.futures import ThreadPoolExecutor

def parallel_map_reduce(data, map_func, reduce_func):
    with ThreadPoolExecutor() as executor:
        mapped = list(executor.map(map_func, data))
    return reduce_func(mapped)
```

### 10. 실행 추적 및 프로파일링
```python
import time
import functools

def profile_execution(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start

        # 프로파일 정보 저장
        if 'profile_data' not in globals():
            globals()['profile_data'] = []

        profile_data.append({
            'function': func.__name__,
            'duration': duration,
            'timestamp': time.time()
        })

        return result
    return wrapper
```

### 실제 활용 예시 통합
```python
# 1. 세션 초기화 확인
if 'session_manager' not in globals():
    from datetime import datetime

    session_manager = {
        'start_time': datetime.now(),
        'cache': {},
        'history': [],
        'checkpoints': {},
        'stats': {'executions': 0, 'cache_hits': 0}
    }
    print("새 세션 시작")
else:
    session_manager['stats']['executions'] += 1
    print(f"세션 진행 중 - 실행 #{session_manager['stats']['executions']}")

# 2. 작업 수행
@profile_execution
def main_task():
    # 캐시 확인
    cache_key = 'main_result'
    if cache_key in session_manager['cache']:
        session_manager['stats']['cache_hits'] += 1
        return session_manager['cache'][cache_key]

    # 실제 작업
    result = perform_complex_calculation()

    # 결과 캐싱
    session_manager['cache'][cache_key] = result
    return result

# 3. 실행
result = main_task()
```

### 권장 사항 요약
1. **항상 세션 상태 확인**: globals()로 변수 존재 확인
2. **점진적 실행**: 큰 작업을 여러 단계로 분할
3. **캐싱 활용**: 반복 계산 최소화
4. **에러 처리**: try-except와 체크포인트
5. **메모리 관리**: 불필요한 데이터 정리
6. **비동기 활용**: I/O 작업 효율화
7. **프로파일링**: 성능 병목 지점 파악
