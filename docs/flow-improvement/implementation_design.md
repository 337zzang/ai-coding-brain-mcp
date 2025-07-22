# Flow 시스템 개선 구현 설계서

## 1. 핵심 개선사항 (o3 분석 기반)

### 1.1 데이터 구조 변경
```python
# 현재 (리스트)
self.flows = [
    {"id": "flow_1", "name": "project1", ...},
    {"id": "flow_2", "name": "project2", ...}
]

# 개선 (딕셔너리 + 캐시)
class FlowRegistry:
    def __init__(self):
        self._flows: dict[str, dict] = {}  # flow_id -> flow_data
        self._name_index: dict[str, list[str]] = {}  # name -> [flow_ids]
        self._last_flow_cache: tuple[str, dict] | None = None  # Hot-cache
        self._current_flow_id: str | None = None
```

### 1.2 성능 개선 수치 (o3 분석)
- switch_flow: 51ms → 2.6ms (dict) → 1.3ms (dict+cache)
- delete_flow: 3ms → 3µs 
- create_flow: 1µs → 1µs (변화 없음)

## 2. 새로운 FlowRegistry 클래스

```python
from typing import Dict, List, Optional, Tuple
import threading
from dataclasses import dataclass, field
from datetime import datetime

@dataclass(slots=True)  # 메모리 최적화
class Flow:
    id: str
    name: str
    plans: Dict[str, dict] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

class FlowRegistry:
    def __init__(self):
        self._flows: Dict[str, Flow] = {}
        self._name_index: Dict[str, List[str]] = {}
        self._last_flow_cache: Optional[Tuple[str, Flow]] = None
        self._current_flow_id: Optional[str] = None
        self._lock = threading.RLock()  # 동시성 처리

    def get_flow(self, flow_id: str) -> Optional[Flow]:
        '''O(1) Flow 검색 with hot-cache'''
        # Hot-cache 확인
        if self._last_flow_cache and self._last_flow_cache[0] == flow_id:
            return self._last_flow_cache[1]

        # Dictionary 검색
        flow = self._flows.get(flow_id)
        if flow:
            self._last_flow_cache = (flow_id, flow)
        return flow

    def create_flow(self, name: str) -> Flow:
        '''새 Flow 생성'''
        with self._lock:
            flow_id = self._generate_unique_id(name)
            flow = Flow(id=flow_id, name=name)

            # Dictionary에 추가
            self._flows[flow_id] = flow

            # Name index 업데이트
            if name not in self._name_index:
                self._name_index[name] = []
            self._name_index[name].append(flow_id)

            return flow

    def delete_flow(self, flow_id: str) -> bool:
        '''O(1) Flow 삭제'''
        with self._lock:
            flow = self._flows.pop(flow_id, None)
            if not flow:
                return False

            # Name index에서 제거
            if flow.name in self._name_index:
                self._name_index[flow.name].remove(flow_id)
                if not self._name_index[flow.name]:
                    del self._name_index[flow.name]

            # Cache 무효화
            if self._last_flow_cache and self._last_flow_cache[0] == flow_id:
                self._last_flow_cache = None

            return True

    def find_flows_by_name(self, name: str) -> List[Flow]:
        '''이름으로 Flow 검색 - O(k) where k = 동일 이름 개수'''
        flow_ids = self._name_index.get(name, [])
        return [self._flows[fid] for fid in flow_ids if fid in self._flows]
```

## 3. 마이그레이션 전략

```python
def migrate_flows_structure(self, old_data: dict) -> dict:
    '''기존 리스트 구조를 새 딕셔너리 구조로 변환'''
    if 'flows' not in old_data or not isinstance(old_data['flows'], list):
        return old_data

    new_flows = {}
    name_index = {}

    for flow in old_data['flows']:
        flow_id = flow.get('id')
        if not flow_id:
            continue

        # Dictionary에 추가
        new_flows[flow_id] = flow

        # Name index 구축
        name = flow.get('name', 'Unknown')
        if name not in name_index:
            name_index[name] = []
        name_index[name].append(flow_id)

    return {
        'flows': new_flows,
        'name_index': name_index,
        'current_flow_id': old_data.get('current_flow_id'),
        'version': '2.0',
        'last_saved': datetime.now().isoformat()
    }
```

## 4. 구현 체크리스트

- [ ] FlowRegistry 클래스 구현
- [ ] Flow dataclass with __slots__ 구현
- [ ] 마이그레이션 함수 구현
- [ ] 기존 메서드 수정 (load, save, create, delete, switch)
- [ ] Hot-cache 성능 테스트
- [ ] 동시성 테스트 (threading.RLock)
- [ ] 하위 호환성 테스트
