# EventBus 리스너 아키텍처 설계

## 1. 개요
이벤트 기반 아키텍처를 강화하기 위한 리스너 시스템 설계

## 2. 핵심 구성 요소

### 2.1 BaseEventListener (추상 클래스)
- 모든 리스너의 기본 인터페이스
- 구독 이벤트 타입 정의
- 표준화된 에러 처리

### 2.2 구현 리스너들

#### ContextListener
- **목적**: 워크플로우 이벤트를 컨텍스트에 자동 반영
- **구독 이벤트**: TASK_COMPLETED, TASK_FAILED, PLAN_COMPLETED 등
- **주요 기능**:
  - 태스크 결과 자동 저장
  - 에러 정보 컨텍스트화
  - 플랜 완료 요약 생성

#### UIProgressListener  
- **목적**: UI 진행률 및 상태 표시
- **구독 이벤트**: TASK_STARTED, TASK_COMPLETED, TASK_FAILED 등
- **주요 기능**:
  - 실시간 진행률 계산
  - 상태 변경 알림
  - 예상 완료 시간 표시

#### ErrorHandlerListener
- **목적**: 에러 자동 처리 및 복구
- **구독 이벤트**: TASK_FAILED, TASK_BLOCKED, SYSTEM_ERROR
- **주요 기능**:
  - 에러 분류 및 로깅
  - 자동 재시도 로직
  - 복구 불가능 시 플랜 일시정지

#### AutoProgressListener
- **목적**: 태스크 자동 진행
- **구독 이벤트**: TASK_COMPLETED, CODE_EXECUTION_SUCCESS
- **주요 기능**:
  - 다음 태스크 자동 시작
  - 의존성 체크
  - 병렬 실행 관리

### 2.3 ListenerManager
- 리스너 중앙 관리
- 메트릭 수집
- 동적 등록/해제

## 3. 구현 우선순위

1. **Phase 1** (즉시):
   - BaseEventListener 인터페이스
   - ContextListener (컨텍스트 통합 개선)

2. **Phase 2** (다음):
   - ErrorHandlerListener (안정성 향상)
   - ListenerManager (관리 체계화)

3. **Phase 3** (추후):
   - UIProgressListener (UI 통합 시)
   - AutoProgressListener (자동화 기능)

## 4. 통합 방안

### 4.1 기존 시스템과의 호환성
- 현재 GitAutoCommitListener 유지
- 점진적 마이그레이션
- 기존 이벤트 발행 코드 유지

### 4.2 초기화 과정
```python
# WorkflowManager 초기화 시
listener_manager = initialize_event_listeners(
    workflow_manager, 
    helpers
)
workflow_manager.listener_manager = listener_manager
```

## 5. 기대 효과
- 모듈 간 결합도 감소
- 새 기능 추가 용이
- 에러 처리 일원화
- 실시간 상태 반영
- 자동화 수준 향상
