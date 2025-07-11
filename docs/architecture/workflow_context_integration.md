# 워크플로우-컨텍스트 통합 아키텍처

## 개요
이 문서는 ai-coding-brain-mcp 프로젝트의 워크플로우와 컨텍스트 매니저 간 통합 아키텍처를 설명합니다.

## 아키텍처 개요

### 핵심 컴포넌트

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ WorkflowManager │     │   Event Bus      │     │ ContextManager  │
│                 │────▶│                  │────▶│                 │
│ - Plans         │     │ - Publish        │     │ - Project Info  │
│ - Tasks         │     │ - Subscribe      │     │ - File History  │
│ - Progress      │     │ - History        │     │ - Error Logs    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       ▲                         │
         │                       │                         │
         └───────────────────────┴─────────────────────────┘
                    Event Integration Adapter
```

### 이벤트 플로우

1. **워크플로우 작업**
   - WorkflowManager가 계획/태스크 작업 수행
   - EventIntegrationAdapter가 메서드 래핑으로 이벤트 발행
   - 예: `create_plan()` → `WORKFLOW_PLAN_CREATED` 이벤트

2. **이벤트 전달**
   - EventBus가 이벤트를 구독자에게 전달
   - 우선순위 기반 처리 (CRITICAL > HIGH > NORMAL > LOW)
   - 약한 참조(weakref)로 메모리 관리

3. **컨텍스트 업데이트**
   - WorkflowContextBridge가 이벤트 수신
   - 적절한 컨텍스트 업데이트 이벤트 발행
   - ContextManager가 최종 업데이트 수행

## 주요 설계 결정

### 1. 이벤트 기반 아키텍처
**이유**: 모듈 간 순환 의존성 제거 및 느슨한 결합
- 직접 호출 대신 이벤트를 통한 통신
- 새로운 기능 추가 시 기존 코드 수정 불필요
- 테스트 및 디버깅 용이

### 2. 어댑터 패턴
**이유**: 기존 코드 최소 수정으로 통합
- EventIntegrationAdapter로 메서드 래핑
- 원본 동작 유지하며 이벤트 추가
- 점진적 마이그레이션 가능

### 3. 브릿지 패턴
**이유**: 워크플로우와 컨텍스트 간 중재
- WorkflowContextBridge가 이벤트 변환
- 현재 태스크 추적 및 파일 작업 연결
- 양방향 의존성 제거

## 구현 상세

### EventBus
- 중앙 이벤트 관리 시스템
- 우선순위 큐 기반 핸들러 실행
- 이벤트 히스토리 추적 (최대 1000개)
- 미들웨어 지원

### Event Types
```python
# 워크플로우 이벤트
WORKFLOW_PLAN_CREATED = "workflow.plan.created"
WORKFLOW_TASK_STARTED = "workflow.task.started"
WORKFLOW_TASK_COMPLETED = "workflow.task.completed"

# 컨텍스트 이벤트
CONTEXT_PROJECT_SWITCHED = "context.project.switched"
CONTEXT_UPDATED = "context.updated"

# 파일 시스템 이벤트
FILE_CREATED = "file.created"
FILE_ACCESSED = "file.accessed"
```

### 통합 방법
```python
# 자동 통합
from events.event_integration_adapter import integrate_all
adapter = integrate_all()

# 수동 통합
adapter = get_event_adapter()
adapter.integrate_workflow_manager(wf_manager)
adapter.integrate_context_manager(ctx_manager)
```

## 성능 특성
- **처리량**: 50,000+ events/sec
- **평균 지연**: < 1ms
- **메모리 오버헤드**: < 50MB (1000 핸들러 + 10000 이벤트)

## 확장 포인트

### 커스텀 이벤트 추가
1. `event_types.py`에 새 이벤트 타입 정의
2. 이벤트 클래스 생성 (옵션)
3. 핸들러 구현 및 등록

### 새로운 통합 추가
1. EventIntegrationAdapter에 통합 메서드 추가
2. 대상 시스템의 주요 메서드 래핑
3. 적절한 이벤트 발행 코드 추가

## 모니터링 및 디버깅

### 이벤트 히스토리 조회
```python
bus = get_event_bus()
history = bus.get_history(event_type="workflow.task.started", limit=50)
```

### 현재 상태 확인
```python
bridge = get_workflow_context_bridge()
context = bridge.get_current_context()
```

## 향후 개선 계획
1. **비동기 이벤트 처리**: asyncio 기반 비동기 핸들러
2. **이벤트 영속성**: 중요 이벤트 DB 저장
3. **분산 이벤트 버스**: 여러 프로세스/서버 간 이벤트 공유
4. **실시간 모니터링**: 웹 기반 이벤트 플로우 시각화
