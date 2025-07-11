# 순환 의존성 해결 방안

## 문제 분석
발견된 순환 참조 경로:
```
context_manager.py 
    ↓ (imports switch_project_workflow)
workflow_integration.py 
    ↓ (imports WorkflowCommands)
workflow/commands.py 
    ↓ (imports ContextManager)
context_manager.py (순환!)
```

## 해결 방안

### 1. 즉시 적용 가능한 해결책: 지연 import
context_manager.py에서 workflow_integration의 import를 함수 내부로 이동:

```python
# 기존 코드 (문제)
from python.workflow_integration import switch_project_workflow

# 개선 코드
def switch_project(self, project_name: str):
    # 함수 내부에서 import
    from python.workflow_integration import switch_project_workflow
    return switch_project_workflow(project_name)
```

### 2. 중기적 해결책: 인터페이스 분리
공통 인터페이스를 별도 모듈로 분리:

```python
# interfaces/project_switcher.py
from abc import ABC, abstractmethod

class ProjectSwitcherInterface(ABC):
    @abstractmethod
    def switch_project(self, project_name: str):
        pass

# context_manager는 인터페이스만 알면 됨
# workflow_integration이 인터페이스를 구현
```

### 3. 장기적 해결책: 이벤트 기반 아키텍처
이벤트 버스를 통한 느슨한 결합:

```python
# events/project_events.py
class ProjectSwitchEvent:
    def __init__(self, project_name: str):
        self.project_name = project_name

# context_manager는 이벤트만 발행
event_bus.publish(ProjectSwitchEvent(project_name))

# workflow_integration은 이벤트를 구독
event_bus.subscribe(ProjectSwitchEvent, handle_project_switch)
```

## 구현 우선순위
1. **즉시**: 지연 import로 순환 참조 해결 (5분)
2. **단기**: 인터페이스 분리로 구조 개선 (2시간)
3. **중기**: 이벤트 시스템 도입 (1-2일)
