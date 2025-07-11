# 이벤트 기반 아키텍처 개편 - 상세 설계서

## 🎯 프로젝트 개요

### 배경
현재 MCP 프로젝트의 워크플로우와 컨텍스트 시스템은 강한 결합도와 데이터 중복 문제를 안고 있습니다. 
이를 이벤트 기반 아키텍처로 전환하여 확장성과 유지보수성을 크게 향상시키고자 합니다.

### 주요 문제점
1. **강한 결합도**: ContextManager와 WorkflowManager의 직접 참조
2. **데이터 중복**: 양쪽에서 워크플로우 데이터 관리
3. **동기화 문제**: 불일치 가능성과 중복 저장
4. **확장성 부족**: 새 기능 추가 시 기존 코드 수정 필요

## 📐 Phase 1: 이벤트 버스 시스템 구축

### 1-1. EventBus 코어 구현

```python
# python/workflow/v3/event_bus.py
class EventBus:
    '''싱글톤 패턴의 중앙 이벤트 버스'''

    def __init__(self):
        self._handlers = defaultdict(list)
        self._event_queue = Queue()
        self._executor = ThreadPoolExecutor(max_workers=5)

    def subscribe(self, event_type: str, handler: Callable):
        '''이벤트 타입에 핸들러 등록'''

    def publish(self, event: Event):
        '''이벤트 발행 (비동기)'''

    def _process_events(self):
        '''백그라운드 이벤트 처리'''
```

### 1-2. EventTypes 정의

```python
# python/workflow/v3/event_types.py
@dataclass
class Event:
    id: str
    type: str
    timestamp: datetime
    payload: Dict[str, Any]

class WorkflowEvent(Event):
    '''워크플로우 관련 이벤트'''

class ContextEvent(Event):
    '''컨텍스트 관련 이벤트'''

class CommandEvent(Event):
    '''명령어 실행 이벤트'''
```

### 1-3. 비동기 처리 구현

- ThreadPoolExecutor 활용
- 실패 시 재시도 로직 (exponential backoff)
- Dead Letter Queue for 실패한 이벤트
- 이벤트 로그 영속성

## 📊 예상 효과

1. **성능 향상**: 비동기 처리로 UI 응답성 개선
2. **신뢰성**: 이벤트 로그 기반 복구 가능
3. **확장성**: 새 모듈 추가 시 기존 코드 수정 불필요
4. **디버깅**: 모든 상태 변화 추적 가능
