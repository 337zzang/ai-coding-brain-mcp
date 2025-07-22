# FlowManagerUnified + FlowRegistry 통합 계획

## 📋 통합 전략

### Phase 1: FlowRegistry 도입 (최소 변경)
1. FlowRegistry import 추가
2. __init__에서 FlowRegistry 초기화
3. 기존 self.flows를 FlowRegistry로 프록시

### Phase 2: 메서드 교체
1. create_flow() → flow_registry.create_flow()
2. switch_flow() → flow_registry.switch_flow()
3. delete_flow() → flow_registry.delete_flow()
4. list_flows() → flow_registry.list_flows()
5. _load_flows() → flow_registry.load_flows()
6. _save_flows() → flow_registry.save_flows()

### Phase 3: 최적화
1. 중복 코드 제거
2. 에러 처리 통일
3. 성능 모니터링 추가

## 🔧 구현 코드

### Step 1: Import 및 초기화
```python
from .flow_registry import FlowRegistry

class FlowManagerUnified:
    def __init__(self, has_context_manager=True, _has_flow_v2=True):
        # ... 기존 코드 ...

        # FlowRegistry 초기화
        self.flow_registry = FlowRegistry(flows_file=self.flows_file)
        self.flow_registry.load_flows()

        # 호환성을 위한 프록시
        self._flows_proxy = None
```

### Step 2: flows 프로퍼티 (호환성)
```python
@property
def flows(self):
    # 리스트 형태로 반환 (하위 호환성)
    return list(self.flow_registry._flows.values())

@flows.setter
def flows(self, value):
    # 설정 시 경고
    print("⚠️ 직접 flows 설정은 deprecated. create_flow() 사용")
```

### Step 3: 메서드 교체
```python
def create_flow(self, name: str) -> dict:
    flow = self.flow_registry.create_flow(name)
    self.current_flow = flow.to_dict()
    self.flow_registry.save_flows()
    return self.current_flow

def switch_flow(self, flow_id: str) -> bool:
    result = self.flow_registry.switch_flow(flow_id)
    if result:
        flow = self.flow_registry.get_current_flow()
        self.current_flow = flow.to_dict() if flow else None
    return result
```
