# 이벤트 시스템 구현 문서

## 개요
워크플로우와 컨텍스트 매니저 간의 순환 의존성을 해결하기 위해 이벤트 기반 아키텍처를 구현했습니다.

## 구현된 컴포넌트

### 1. EventBus (`python/events/event_bus.py`)
- 중앙 이벤트 버스 시스템
- 약한 참조(weakref)를 사용하여 메모리 누수 방지
- 우선순위 기반 핸들러 실행
- 이벤트 히스토리 추적
- 미들웨어 지원

### 2. Event Types (`python/events/event_types.py`)
- 표준화된 이벤트 타입 정의
- 특화된 이벤트 클래스들 (WorkflowEvent, TaskEvent, FileEvent 등)
- 이벤트 생성 헬퍼 함수

### 3. WorkflowContextBridge (`python/events/workflow_context_bridge.py`)
- 워크플로우와 컨텍스트 간 이벤트 중재
- 현재 태스크 ID 추적
- 파일 작업과 태스크 자동 연결

## 주요 기능

### 이벤트 발행/구독
```python
# 핸들러 등록
bus.subscribe(EventTypes.TASK_STARTED, handler)

# 이벤트 발행
event = create_task_started_event("task_id", "task_title")
bus.publish(event)
```

### 데코레이터 패턴
```python
@subscribe_to(EventTypes.FILE_ACCESSED)
def on_file_accessed(event):
    # 파일 접근 시 자동 호출
```

### 느슨한 결합
- WorkflowManager는 ContextManager를 직접 호출하지 않음
- 이벤트를 통해서만 통신
- 모듈 간 직접적인 import 의존성 제거

## 장점
1. **순환 의존성 해결**: 모듈 간 직접 참조 제거
2. **확장성**: 새로운 이벤트 타입과 핸들러 쉽게 추가
3. **테스트 용이성**: 모듈을 독립적으로 테스트 가능
4. **디버깅**: 이벤트 히스토리로 시스템 동작 추적

## 사용 예제
통합 예제는 `python/events/integration_example.py` 참조

## 다음 단계
1. 기존 WorkflowManager에 이벤트 발행 코드 추가
2. ContextManager에 이벤트 구독 코드 추가
3. 점진적으로 직접 호출을 이벤트로 대체
