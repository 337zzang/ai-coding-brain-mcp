# 이벤트 시스템 통합 가이드

## 개요
이 문서는 기존 WorkflowManager와 ContextManager에 이벤트 시스템을 통합하는 방법을 설명합니다.

## 통합 방법

### 1. 자동 통합 (권장)
```python
from events.event_integration_adapter import integrate_all

# 모든 시스템 자동 통합
adapter = integrate_all()
```

### 2. 개별 통합
```python
from events.event_integration_adapter import get_event_adapter
from workflow.workflow_manager import WorkflowManager
from core.context_manager import ContextManager

adapter = get_event_adapter()

# WorkflowManager 통합
wf_manager = WorkflowManager()
adapter.integrate_workflow_manager(wf_manager)

# ContextManager 통합
ctx_manager = ContextManager()
adapter.integrate_context_manager(ctx_manager)

# 파일 작업 통합
adapter.integrate_file_operations()
```

## 통합 후 동작

### WorkflowManager
- `create_plan()` → `WORKFLOW_PLAN_CREATED` 이벤트 발행
- `start_task()` → `WORKFLOW_TASK_STARTED` 이벤트 발행
- `complete_task()` → `WORKFLOW_TASK_COMPLETED` 이벤트 발행

### ContextManager
- `CONTEXT_UPDATED` 이벤트 구독
- 태스크 시작/완료 자동 기록
- 파일 접근 기록에 태스크 ID 연결

### File Operations
- `create_file()` → `FILE_CREATED` 이벤트 발행
- `read_file()` → `FILE_ACCESSED` 이벤트 발행
- 현재 태스크 ID 자동 연결

## 커스텀 이벤트 추가

### 1. 새 이벤트 타입 정의
```python
# events/event_types.py에 추가
MY_CUSTOM_EVENT = "my.custom.event"
```

### 2. 이벤트 발행
```python
from events.event_bus import get_event_bus, Event

bus = get_event_bus()
event = Event(
    type="my.custom.event",
    data={"key": "value"}
)
bus.publish(event)
```

### 3. 이벤트 구독
```python
from events.event_bus import subscribe_to

@subscribe_to("my.custom.event")
def handle_custom_event(event):
    print(f"Custom event: {event.data}")
```

## 디버깅

### 이벤트 히스토리 확인
```python
from events.event_bus import get_event_bus

bus = get_event_bus()
history = bus.get_history(limit=50)

for event in history:
    print(f"{event.timestamp}: {event.type}")
```

### 현재 브릿지 상태 확인
```python
from events.workflow_context_bridge import get_workflow_context_bridge

bridge = get_workflow_context_bridge()
context = bridge.get_current_context()
print(f"Current task: {context['current_task_id']}")
```

## 주의사항
1. 순환 참조를 피하기 위해 이벤트 핸들러에서 직접 이벤트를 발행하지 않도록 주의
2. 이벤트 핸들러는 가능한 한 가볍게 유지
3. 에러 처리를 철저히 (하나의 핸들러 실패가 전체 시스템을 멈추지 않도록)

## 성능 고려사항
- 이벤트 버스는 동기식으로 동작 (비동기 지원 예정)
- 약한 참조(weakref) 사용으로 메모리 누수 방지
- 이벤트 히스토리는 최대 1000개까지 유지
