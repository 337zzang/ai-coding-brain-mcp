
## 🎯 Task 2: Plan.tasks 데이터 모델 개선

### 목표
Plan.tasks를 더 직관적이고 사용하기 쉬운 구조로 개선

### 현재 문제점
1. `Dict[str, Task]` 구조로 인한 순회 시 혼란
2. `for task in plan.tasks` → task는 문자열(key)
3. 순서 보장 안됨
4. 번호 기반 접근 불편

### 설계 옵션 비교

#### Option 1: List 구조 (직관성 최우선)
```python
@dataclass
class Plan:
    tasks: List[Task] = field(default_factory=list)
    _task_index: Dict[str, int] = field(default_factory=dict, init=False, repr=False)

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)
        self._task_index[task.id] = len(self.tasks) - 1

    def get_task(self, task_id: str) -> Optional[Task]:
        idx = self._task_index.get(task_id)
        return self.tasks[idx] if idx is not None else None
```

**장점:**
- 직관적인 순회: `for task in plan.tasks`
- 순서 보장
- 번호 접근 쉬움: `plan.tasks[0]`

**단점:**
- ID 검색 시 O(n) → 인덱스로 개선 필요
- 삭제 시 인덱스 재계산 필요

#### Option 2: OrderedDict 구조 (균형형)
```python
from collections import OrderedDict

@dataclass 
class Plan:
    tasks: OrderedDict[str, Task] = field(default_factory=OrderedDict)

    def get_task_list(self) -> List[Task]:
        return list(self.tasks.values())

    def get_task_by_number(self, number: int) -> Optional[Task]:
        tasks = self.get_task_list()
        if 0 <= number-1 < len(tasks):
            return tasks[number-1]
        return None

    def iter_tasks(self):
        """직관적인 순회를 위한 헬퍼"""
        return self.tasks.values()
```

**장점:**
- 순서 보장 (Python 3.7+)
- ID 검색 O(1) 유지
- 기존 코드와 호환성 좋음

**단점:**
- 여전히 `.values()` 필요
- OrderedDict import 필요

### 결정: Option 2 (OrderedDict) 선택

**이유:**
1. 기존 코드와의 호환성
2. 성능 특성 유지 (O(1) 검색)
3. 헬퍼 메서드로 직관성 보완 가능
4. 마이그레이션 리스크 최소화
