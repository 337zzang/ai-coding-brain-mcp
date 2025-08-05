# Task 3: Subprocess Worker 통합 - 상세 설계

## 🎯 목표
json-repl-session.py의 execute_code() 함수에 Subprocess Worker 실행 경로 추가

## 📋 구현 요구사항

### 1. 조건부 실행 경로
- USE_SUBPROCESS_WORKER=1일 때 Worker 프로세스에서 실행
- USE_SUBPROCESS_WORKER=0일 때 기존 로컬 실행 (기본값)
- WORKER_AVAILABLE=False일 때 자동 fallback

### 2. WorkerManager 통합
```python
# 전역 변수로 WorkerManager 인스턴스 관리
_worker_manager = None

def get_worker_manager():
    global _worker_manager
    if _worker_manager is None:
        _worker_manager = WorkerManager()
    return _worker_manager
```

### 3. execute_code() 함수 수정

#### 현재 구조:
```python
def execute_code(code: str) -> Dict[str, Any]:
    # 1. 헬퍼 로드
    # 2. 시간 측정 시작
    # 3. 코드 실행 (exec)
    # 4. 결과 처리
    # 5. 히스토리 기록
    # 6. 결과 반환
```

#### 수정된 구조:
```python
def execute_code(code: str) -> Dict[str, Any]:
    # 1. 헬퍼 로드
    # 2. 시간 측정 시작
    
    # 3. 실행 경로 분기 (신규)
    if USE_SUBPROCESS_WORKER and WORKER_AVAILABLE:
        try:
            # Worker 실행
            manager = get_worker_manager()
            result = manager.execute(code, timeout=30.0)
            
            # 결과 형식 통일
            if 'success' not in result:
                result['success'] = not result.get('error')
                
        except Exception as e:
            # Fallback to local execution
            logger.warning(f"Worker failed: {e}, falling back to local")
            result = execute_locally(code)
    else:
        # 로컬 실행
        result = execute_locally(code)
    
    # 4. 결과 처리
    # 5. 히스토리 기록
    # 6. 결과 반환
```

### 4. execute_locally() 함수 추출
기존 exec() 기반 실행 로직을 별도 함수로 추출:
```python
def execute_locally(code: str) -> Dict[str, Any]:
    # 기존 exec() 기반 실행 로직
    # stdout/stderr 캡처
    # 예외 처리
    # 결과 딕셔너리 생성
```

### 5. 오류 처리 및 복구

#### Worker 실행 실패 시나리오:
1. Worker 프로세스 시작 실패 → 로컬 실행으로 fallback
2. 실행 타임아웃 → 로컬 실행으로 fallback  
3. Worker 프로세스 크래시 → 자동 재시작 후 재시도
4. JSON 통신 오류 → 로컬 실행으로 fallback

#### 복구 전략:
- 3회 재시도 후 로컬 실행
- Worker 실패 시 경고 로그
- 사용자에게는 투명하게 처리

### 6. 성능 고려사항

#### 장점:
- Import 오염 방지
- 메인 REPL 안정성 보장
- 격리된 환경에서 위험한 코드 실행

#### 단점:
- IPC 오버헤드 (약 5-10ms)
- 메모리 사용량 증가 (별도 프로세스)

### 7. 테스트 계획

1. **기본 동작 테스트**
   - USE_SUBPROCESS_WORKER=0 (기존 동작 확인)
   - USE_SUBPROCESS_WORKER=1 (Worker 실행 확인)

2. **오류 복구 테스트**
   - Worker 강제 종료 후 자동 재시작
   - 타임아웃 시나리오
   - Import 충돌 시나리오

3. **성능 테스트**
   - 실행 시간 비교
   - 메모리 사용량 측정

## 📝 구현 단계

1. execute_locally() 함수로 기존 로직 추출
2. get_worker_manager() 함수 추가
3. execute_code()에 분기 로직 추가
4. 오류 처리 및 fallback 구현
5. 디버그 로그 추가
6. 테스트 및 검증