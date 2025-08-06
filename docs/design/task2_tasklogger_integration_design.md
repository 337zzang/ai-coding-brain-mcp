# Task 2: TaskLogger 통합 상세 설계

## 🎯 목표
execute_code() 함수에 EnhancedTaskLogger를 통합하여 모든 코드 실행을 자동으로 기록

## 📋 현재 상태
- Task 1에서 이미 완료된 사항:
  - TaskLogger import 추가
  - REPL_LOGGER 전역 인스턴스 생성
  - 환경변수 기반 활성화 제어 (ENABLE_TASK_LOGGING)

## 🔧 통합 설계

### 1. 로깅 지점 (Logging Points)
execute_code() 함수 내 3개 주요 지점:

#### A. 실행 시작 (Pre-execution)
```python
# 실행 전 상태 캡처
if ENABLE_TASK_LOGGING and REPL_LOGGER:
    pre_snapshot = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'code': code,
        'execution_count': execution_count,
        'current_vars': list(repl_globals.keys()),
        'current_modules': list(sys.modules.keys())
    }
```

#### B. 실행 중 (During execution)
- stdout/stderr 캡처는 기존 로직 활용
- 실행 시간 측정 (time.perf_counter)

#### C. 실행 완료 (Post-execution)
```python
# 실행 후 로깅
if ENABLE_TASK_LOGGING and REPL_LOGGER:
    post_snapshot = {
        'success': result['success'],
        'stdout': result['stdout'],
        'stderr': result['stderr'],
        'elapsed_ms': elapsed_time,
        'added_vars': list(set(repl_globals.keys()) - set(pre_snapshot['current_vars'])),
        'added_modules': list(set(sys.modules.keys()) - set(pre_snapshot['current_modules']))
    }

    # TaskLogger에 기록
    log_entry = {
        'type': 'code_execution',
        'pre': pre_snapshot,
        'post': post_snapshot,
        'plan_id': FLOW_PLAN_ID,
        'task_id': FLOW_TASK_ID
    }
    REPL_LOGGER.code('execute', log_entry)
```

### 2. 로깅 데이터 구조
```json
{
    "type": "code_execution",
    "timestamp": "2025-08-05T00:00:00.000Z",
    "execution_count": 1,
    "code": "import pandas as pd",
    "success": true,
    "stdout": "",
    "stderr": "",
    "elapsed_ms": 125.5,
    "added_vars": ["pd"],
    "added_modules": ["pandas", "numpy", ...],
    "flow_context": {
        "plan_id": "plan_xxx",
        "task_id": "task_xxx"
    }
}
```

### 3. 오류 처리 전략
- TaskLogger 오류가 코드 실행을 방해하지 않도록 보호
- try-except로 각 로깅 작업 감싸기
- 로깅 실패 시 경고만 출력, 실행은 계속

### 4. 성능 고려사항
- 환경변수로 완전히 비활성화 가능
- 최소한의 오버헤드 (< 5ms)
- 비동기 로깅 고려 (future enhancement)

### 5. Flow 시스템 연동
- 환경변수에서 Plan/Task ID 자동 읽기
- ID가 없으면 'local' / 'adhoc' 사용
- TaskLogger가 자동으로 적절한 JSONL 파일에 기록

## 📊 구현 단계

### Phase 1: 기본 로깅 (최소 구현)
1. 실행 전 스냅샷 캡처
2. 실행 시간 측정
3. 실행 후 결과 로깅

### Phase 2: 상세 정보 추가
1. 변수/모듈 diff 계산
2. 메모리 사용량 추적
3. 실행 컨텍스트 메타데이터

### Phase 3: 고급 기능
1. 코드 실행 패턴 분석
2. 성능 통계 생성
3. 자동 최적화 제안

## ⚠️ 주의사항
- 기존 execute_code() 동작 변경 최소화
- 모든 로깅은 선택적 (opt-in)
- 실패 시 graceful degradation
