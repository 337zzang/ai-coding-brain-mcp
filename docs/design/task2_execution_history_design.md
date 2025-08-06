# Task 2: 실행 히스토리 추적 기능 - 상세 설계

## 🎯 목표
json-repl-session.py에 간단한 실행 히스토리 추적 기능 추가

## 📋 설계 개요

### 1. 전역 변수 추가
```python
# 실행 히스토리를 저장할 리스트 (순환 버퍼)
EXECUTION_HISTORY = []
MAX_HISTORY_SIZE = 100  # 최대 저장 개수
```

### 2. execute_code() 함수 수정

#### A. 실행 시작 시점
```python
# 실행 시작 시간 기록
if ENABLE_TASK_LOGGING:
    exec_start_time = time.perf_counter()
```

#### B. 실행 완료 후
```python
# 실행 완료 후 히스토리 기록
if ENABLE_TASK_LOGGING:
    exec_end_time = time.perf_counter()
    elapsed_ms = (exec_end_time - exec_start_time) * 1000

    history_entry = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'execution_count': execution_count,
        'code': code[:100],  # 처음 100자만 저장
        'success': result['success'],
        'elapsed_ms': round(elapsed_ms, 2)
    }

    # 히스토리에 추가
    EXECUTION_HISTORY.append(history_entry)

    # 순환 버퍼 - 오래된 항목 제거
    if len(EXECUTION_HISTORY) > MAX_HISTORY_SIZE:
        EXECUTION_HISTORY.pop(0)

    # debug_info에 히스토리 정보 추가
    result['debug_info']['elapsed_ms'] = round(elapsed_ms, 2)
    result['debug_info']['history_size'] = len(EXECUTION_HISTORY)
```

### 3. 헬퍼 함수 추가 (선택사항)

```python
def get_execution_history(n=10):
    """최근 n개의 실행 히스토리 반환"""
    return EXECUTION_HISTORY[-n:] if EXECUTION_HISTORY else []

def get_execution_stats():
    """실행 통계 반환"""
    if not EXECUTION_HISTORY:
        return {'total': 0, 'success': 0, 'failed': 0}

    total = len(EXECUTION_HISTORY)
    success = sum(1 for e in EXECUTION_HISTORY if e['success'])
    return {
        'total': total,
        'success': success,
        'failed': total - success,
        'success_rate': success / total
    }
```

## 📊 데이터 구조

### history_entry 스키마
```json
{
    "timestamp": "2025-08-05T00:00:00.000Z",
    "execution_count": 42,
    "code": "df = pd.read_csv('data.csv')",  // 최대 100자
    "success": true,
    "elapsed_ms": 125.5
}
```

## 🔧 구현 상세

### 1. 메모리 효율성
- 최대 100개 항목만 유지
- 각 항목은 약 200-300 bytes
- 전체 메모리 사용량: ~30KB

### 2. 성능 영향
- 추가 오버헤드: < 1ms
- time.perf_counter()는 고정밀 타이머
- 리스트 append/pop은 O(1)

### 3. 안전성
- ENABLE_TASK_LOGGING 환경변수로 제어
- 히스토리 기록 실패 시 실행에 영향 없음
- try-except 불필요 (단순 연산만 수행)

## ✅ 구현 체크리스트

- [ ] EXECUTION_HISTORY 전역 변수 선언
- [ ] MAX_HISTORY_SIZE 상수 정의
- [ ] 실행 시간 측정 코드 추가
- [ ] 히스토리 항목 생성 및 추가
- [ ] 순환 버퍼 로직 구현
- [ ] debug_info 업데이트
- [ ] (선택) 헬퍼 함수 추가

## 🚀 활용 예시

```python
# 최근 실행 확인
>>> print(EXECUTION_HISTORY[-5:])

# 오류만 필터링
>>> [e for e in EXECUTION_HISTORY if not e['success']]

# 평균 실행 시간
>>> sum(e['elapsed_ms'] for e in EXECUTION_HISTORY) / len(EXECUTION_HISTORY)
```

## 📌 주의사항
- TaskLogger와 혼동하지 않기 (별개 기능)
- 민감한 정보는 code에 포함되지 않도록 100자 제한
- 장기 실행 코드는 elapsed_ms가 클 수 있음
