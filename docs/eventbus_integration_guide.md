# EventBus 통합 가이드

## 🎯 개요
WorkflowManager V3가 이제 EventBus와 완전히 통합되어, 모든 워크플로우 상태 변경이 이벤트로 발행됩니다.

## 🛠️ 구현된 변경사항

### 1. WorkflowManager 수정
```python
# manager.py
from .workflow_event_adapter import WorkflowEventAdapter

class WorkflowManager:
    def __init__(self, project_name: str):
        # ... 기존 코드 ...
        # EventBus 연동을 위한 어댑터 초기화
        self.event_adapter = WorkflowEventAdapter(self)

    def _add_event(self, event):
        '''이벤트를 EventStore에 추가하고 EventBus로 발행'''
        self.event_store.add(event)
        if hasattr(self, 'event_adapter') and self.event_adapter:
            try:
                self.event_adapter.publish_workflow_event(event)
            except Exception as e:
                logger.error(f"Failed to publish event to EventBus: {e}")
```

### 2. WorkflowEventAdapter 개선
- `publish_workflow_event()` 범용 메서드 추가
- WorkflowEvent → Event 변환 로직 수정
- 'name' vs 'plan_name' 필드 호환성 처리

## 📊 지원되는 이벤트

| 이벤트 타입 | 발생 시점 | 페이로드 |
|------------|----------|----------|
| PLAN_CREATED | 플랜 생성 | plan_id, plan_name, description |
| PLAN_STARTED | 플랜 시작 | plan_id, plan_name |
| TASK_ADDED | 태스크 추가 | task_id, task_title, plan_id |
| TASK_COMPLETED | 태스크 완료 | task_id, task_title, duration |
| PLAN_COMPLETED | 플랜 완료 | plan_id, total_tasks, duration |

## 💻 사용 예제

### 이벤트 구독
```python
from python.workflow.v3.event_bus import event_bus
from python.workflow.v3.event_types import EventType

# 핸들러 정의
def on_task_completed(event):
    print(f"태스크 완료: {event.payload['task_title']}")
    print(f"소요 시간: {event.payload.get('duration', 'N/A')}")

# 구독
event_bus.subscribe(EventType.TASK_COMPLETED.value, on_task_completed)

# EventBus 시작
event_bus.start()
```

### WorkflowManager 사용
```python
from python.workflow.v3.manager import WorkflowManager

# 매니저 생성 (자동으로 EventBus 연결됨)
wf = WorkflowManager("my_project")

# 플랜 생성 → PLAN_CREATED, PLAN_STARTED 이벤트 발행
plan = wf.start_plan("새 프로젝트")

# 태스크 추가 → TASK_ADDED 이벤트 발행
task = wf.add_task("첫 번째 작업")

# 태스크 완료 → TASK_COMPLETED 이벤트 발행
wf.complete_task(task.id)
```

## 🔧 고급 활용

### 1. 실시간 모니터링
```python
class WorkflowMonitor:
    def __init__(self):
        self.active_tasks = {}
        self._subscribe_events()

    def _subscribe_events(self):
        event_bus.subscribe(EventType.TASK_ADDED.value, self._on_task_added)
        event_bus.subscribe(EventType.TASK_COMPLETED.value, self._on_task_completed)

    def _on_task_added(self, event):
        task_id = event.payload['task_id']
        self.active_tasks[task_id] = {
            'title': event.payload['task_title'],
            'started_at': event.timestamp
        }

    def _on_task_completed(self, event):
        task_id = event.payload['task_id']
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
```

### 2. 외부 시스템 연동
```python
class SlackNotifier:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
        event_bus.subscribe(EventType.PLAN_COMPLETED.value, self._notify_completion)

    def _notify_completion(self, event):
        message = f"✅ 플랜 완료: {event.payload['plan_name']}"
        # Slack으로 알림 전송
        requests.post(self.webhook_url, json={'text': message})
```

## ⚠️ 주의사항

1. **메모리 정리**: 사용 후 반드시 cleanup 호출
   ```python
   wf.cleanup()  # EventAdapter 정리 포함
   ```

2. **이벤트 핸들러 제거**: 구독 해제 필수
   ```python
   event_bus.unsubscribe(event_type, handler)
   ```

3. **helpers.workflow 제한**: 현재 helpers.workflow 명령은 별도 인스턴스를 사용하므로 이벤트가 발행되지 않음

## 📈 향후 로드맵

- [ ] helpers.workflow 통합
- [ ] 이벤트 필터링/라우팅
- [ ] 이벤트 영속성 (DB 저장)
- [ ] 이벤트 재생 기능
- [ ] WebSocket 실시간 스트리밍

---
작성일: 2025-01-10
버전: 1.0
