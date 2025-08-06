# Task 2: TaskLogger 통합 최종 상세 설계

## 🎯 목표
execute_code() 함수에 EnhancedTaskLogger를 통합하여 모든 REPL 코드 실행을 자동으로 기록

## 📋 설계 개요

### 1. 핵심 원칙
- **비침습적 통합**: 기존 동작에 영향 최소화
- **Fail-safe**: 로깅 오류가 실행을 방해하지 않음
- **성능 고려**: 오버헤드 < 5ms
- **환경변수 제어**: ENABLE_TASK_LOGGING으로 on/off

### 2. 구현 전략

#### A. 필수 상수 정의
```python
MAX_LOG_LENGTH = 10_000  # stdout/stderr 로깅 최대 길이
MAX_MODULES_LOG = 20     # 로깅할 모듈 최대 개수
```

#### B. DummyLogger 준비 (O3 제안)
```python
if ENABLE_TASK_LOGGING and not REPL_LOGGER:
    class _DummyLogger:
        def code(self, *args, **kwargs): pass
    REPL_LOGGER = _DummyLogger()
```

#### C. 로깅 포인트

**1) 실행 전 (Pre-execution)**
- 현재 상태 스냅샷
- 시작 시간 기록

**2) 실행 중 (During execution)**
- 기존 stdout/stderr 캡처 활용
- 예외 처리 유지

**3) 실행 후 (Post-execution)**
- 변경사항 diff 계산
- TaskLogger 기록
- debug_info 업데이트

### 3. 로깅 데이터 스키마

```python
{
    "action": "execute",
    "file": "<repl>",
    "content": "실행된 코드",
    "summary": "Execution #1 - Success",
    "details": {
        "execution_count": 1,
        "timestamp": "2025-08-05T00:00:00.000Z",
        "success": true,
        "elapsed_ms": 125.5,
        "stdout": "출력 내용 (최대 10000자)",
        "stderr": "에러 내용 (최대 10000자)",
        "added_vars": ["pd", "df"],
        "added_modules": ["pandas", "numpy"],
        "flow_context": {
            "plan_id": "plan_xxx",
            "task_id": "task_xxx"
        }
    }
}
```

### 4. 개선사항 (O3 피드백 반영)

1. **출력 길이 제한**
   - stdout/stderr를 MAX_LOG_LENGTH로 제한
   - 과도한 출력으로 인한 로그 파일 폭증 방지

2. **DummyLogger 패턴**
   - REPL_LOGGER가 None일 때도 안전하게 처리
   - 조건문 복잡도 감소

3. **모듈 리스트 제한**
   - added_modules를 MAX_MODULES_LOG 개수로 제한
   - 대규모 import 시 로그 크기 제어

### 5. 성능 최적화

- 로깅 비활성화 시 오버헤드: 0ms
- 로깅 활성화 시 예상 오버헤드: 2-5ms
- 스냅샷은 set() 연산으로 O(1) 접근
- diff 계산은 set 차집합으로 효율적

### 6. 오류 처리

```python
try:
    # 로깅 작업
except Exception as e:
    if DEBUG_MODE:
        print(f"[TaskLogger] {e}", file=sys.stderr)
    # 실행은 계속됨
```

## 📊 구현 체크리스트

- [ ] MAX_LOG_LENGTH 상수 정의
- [ ] DummyLogger 클래스 추가
- [ ] 실행 전 스냅샷 로직
- [ ] 실행 시간 측정 (perf_counter)
- [ ] 실행 후 diff 계산
- [ ] TaskLogger.code() 호출
- [ ] debug_info 업데이트
- [ ] 출력 길이 제한 적용
- [ ] 예외 처리 완성

## ✅ 예상 결과

1. 모든 REPL 실행이 JSONL 파일에 기록됨
2. Flow 시스템과 자동 연동
3. 실행 히스토리 추적 가능
4. 디버깅 및 분석 용이
5. 성능 영향 최소화
