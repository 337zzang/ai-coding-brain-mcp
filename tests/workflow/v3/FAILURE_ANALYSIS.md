# 🔍 이벤트 시스템 테스트 실패 원인 분석

## 1. 🚨 주요 문제점

### 1.1 API 불일치
**문제**: 테스트 코드와 실제 구현의 API가 완전히 다름

| 테스트 예상 | 실제 구현 |
|------------|----------|
| `adapter.add_listener(listener)` | ❌ 메서드 없음 |
| `adapter.emit(event)` | ❌ 메서드 없음 |
| - | `adapter.publish_workflow_event(event)` ✅ |
| - | `adapter.publish_task_started(...)` ✅ |

### 1.2 리스너 등록 방식 차이
**테스트 코드**:
```python
adapter.add_listener(listener)  # ❌ 작동 안 함
```

**실제 필요한 방식**:
```python
adapter.event_bus.subscribe("task_started", handler)  # ✅ 올바른 방식
```

### 1.3 추상 클래스 미구현
**문제**: BaseEventListener는 추상 클래스인데 필수 메서드를 구현하지 않음

```python
class TestListener(BaseEventListener):  # ❌ TypeError 발생
    def handle_event(self, event):
        pass
    # get_subscribed_events() 메서드 누락!
```

**필요한 구현**:
```python
class TestListener(BaseEventListener):  # ✅
    def get_subscribed_events(self) -> Set[EventType]:
        return {EventType.TASK_STARTED, EventType.TASK_COMPLETED}

    def handle_event(self, event: WorkflowEvent):
        # 이벤트 처리
        return None
```

### 1.4 이벤트 타입 불일치
- EventBus는 `Event` 타입 사용
- WorkflowEventAdapter는 `WorkflowEvent` 타입 사용
- 두 타입 간의 변환 또는 호환성 처리 필요

### 1.5 EventBus 생명주기 문제
- "EventBus is already running" 경고
- 테스트 간 EventBus 인스턴스 공유
- 적절한 setup/teardown 필요

## 2. 🏗️ 실제 아키텍처

```
WorkflowEventAdapter
    ├── event_bus: EventBus
    │   ├── subscribe(event_type, handler)
    │   ├── publish(event)
    │   └── start/stop()
    └── publish_* 메서드들
        ├── publish_workflow_event(event)
        ├── publish_task_started(...)
        └── ...
```

## 3. ✅ 올바른 사용 방법

### 3.1 이벤트 발행
```python
# ❌ 잘못된 방법
adapter.emit(WorkflowEvent(...))

# ✅ 올바른 방법
adapter.publish_task_started(task_id="123", title="작업")
# 또는
adapter.publish_workflow_event(WorkflowEvent(...))
```

### 3.2 이벤트 구독
```python
# ❌ 잘못된 방법
adapter.add_listener(listener)

# ✅ 올바른 방법 (EventBus 직접 사용)
def handler(event):
    # 이벤트 처리
    pass

adapter.event_bus.subscribe("task_started", handler)
```

## 4. 🛠️ 해결 방안

1. **테스트 코드 전면 수정**
   - WorkflowEventAdapter의 실제 API 사용
   - publish_* 메서드 활용

2. **리스너 구현 수정**
   - BaseEventListener의 모든 추상 메서드 구현
   - 또는 EventBus의 handler 함수 직접 사용

3. **EventBus 관리**
   - 각 테스트에서 독립적인 EventBus 사용
   - 또는 테스트 후 정리 로직 추가

4. **통합 방식 재검토**
   - WorkflowEventAdapter가 리스너를 관리하도록 수정
   - 또는 EventBus를 직접 노출하지 않도록 캡슐화
