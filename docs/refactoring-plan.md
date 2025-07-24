# 🔧 리팩토링 방안

## 🚨 주요 우려점

### 1. **거대한 메서드 (God Method)**
- `handle_flow_status`: 538줄
- 단일 책임 원칙 위반
- 테스트 및 유지보수 어려움

### 2. **데이터 구조 일관성 부재**
- Flow가 dict와 객체로 혼재
- 매번 타입 체크 필요
- 중복 코드 발생

### 3. **의존성 문제**
- 메서드 내부에서 직접 import
- 순환 참조 위험
- 결합도 높음

### 4. **에러 처리 중복**
- 동일한 에러 패턴 22회 반복
- 중앙화된 에러 처리 없음

## 💡 리팩토링 방안

### 1. 거대 메서드 분리
```python
# Before: 538줄의 handle_flow_status
def handle_flow_status(self, args):
    # 모든 로직이 한 곳에...

# After: 책임별로 분리
def handle_flow_status(self, args):
    status = self._get_flow_status()
    if not status['ok']:
        return status

    plan_list = self._format_plan_list(status['data'])
    return {'ok': True, 'data': plan_list}

def _get_flow_status(self):
    # Flow 상태 조회 로직
    pass

def _format_plan_list(self, flow_data):
    # Plan 리스트 포맷팅 로직
    pass

def _get_plan_status_icon(self, plan):
    # Plan 상태 아이콘 결정 로직
    pass
```

### 2. 데이터 모델 정의
```python
# models.py
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class Task:
    id: str
    name: str
    status: str
    context: Dict = field(default_factory=dict)

@dataclass
class Plan:
    id: str
    name: str
    tasks: Dict[str, Task] = field(default_factory=dict)
    completed: bool = False

@dataclass
class Flow:
    id: str
    name: str
    plans: Dict[str, Plan] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> 'Flow':
        # dict를 Flow 객체로 변환
        pass
```

### 3. 에러 처리 중앙화
```python
# errors.py
class FlowError:
    @staticmethod
    def not_found(item_type: str, item_id: str) -> Dict:
        return {
            'ok': False, 
            'error': f'{item_type} {item_id}를 찾을 수 없습니다'
        }

    @staticmethod
    def no_active_flow() -> Dict:
        return {
            'ok': False, 
            'error': '활성 Flow가 없습니다. /flow [name]으로 Flow를 선택하세요.'
        }

# 사용 예
if not flow_id:
    return FlowError.no_active_flow()
```

### 4. 의존성 주입
```python
# FlowCommandRouter 생성자 개선
class FlowCommandRouter:
    def __init__(self, unified_manager, flow_manager=None):
        self.manager = unified_manager
        self.flow_manager = flow_manager or FlowManager()
        # FlowManager를 생성자에서 주입받음
```

### 5. 타입 일관성 보장
```python
# Flow 데이터 접근 헬퍼
class FlowAccessor:
    @staticmethod
    def get_flow_id(flow) -> str:
        if isinstance(flow, dict):
            return flow.get('id', 'unknown')
        return getattr(flow, 'id', 'unknown')

    @staticmethod
    def get_flow_plans(flow) -> Dict:
        if isinstance(flow, dict):
            return flow.get('plans', {})
        return getattr(flow, 'plans', {})
```

### 6. workflow_wrapper 개선
```python
# 전략 패턴 사용
class CommandProcessor:
    def process(self, command: str) -> Dict:
        pass

class RouterProcessor(CommandProcessor):
    def __init__(self, router):
        self.router = router

    def process(self, command: str) -> Dict:
        return self.router.route(command)

# wf 함수 단순화
def wf(command: str) -> Dict:
    manager = get_workflow_manager()
    processor = get_command_processor(manager)
    return processor.process(command)
```

## 🎯 우선순위

1. **긴급**: handle_flow_status 메서드 분리
2. **중요**: 데이터 모델 정의 및 타입 일관성
3. **필요**: 에러 처리 중앙화
4. **개선**: 의존성 주입 패턴 적용

## 📊 예상 효과

- 코드 가독성 ↑
- 유지보수성 ↑
- 테스트 용이성 ↑
- 확장성 ↑
- 버그 발생률 ↓
