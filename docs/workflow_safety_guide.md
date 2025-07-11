# 워크플로우 안전성 개선 가이드

## 1. 주요 개선사항

### 1.1 KeyError 방지
```python
# 기존 코드 (위험)
plan_name = status['plan']['name']  # KeyError 위험

# 개선된 코드 (안전)
from python.workflow.safety_utils import safe_get
plan_name = safe_get(status, 'plan.name', '이름없음')
```

### 1.2 TypeError 방지 (Enum 직렬화)
```python
# 기존 코드 (위험)
data = {'status': TaskStatus.COMPLETED}
json.dumps(data)  # TypeError: Object of type TaskStatus is not JSON serializable

# 개선된 코드 (안전)
from python.workflow.safety_utils import safe_json
json_str = safe_json(data)  # Enum이 자동으로 value로 변환됨
```

### 1.3 AttributeError 방지
```python
# 기존 코드 (위험)
if task.completed:  # AttributeError if 'completed' doesn't exist

# 개선된 코드 (안전)
from python.workflow.safety_utils import safe_getattr
if safe_getattr(task, 'completed', False):
    # 또는
if task.status == TaskStatus.COMPLETED:  # Enum 비교 사용
```

### 1.4 명령어 파싱 개선
```python
# 기존 코드 (위험)
parts = args.split('|')
title = parts[0]  # IndexError 위험

# 개선된 코드 (안전)
from python.workflow.safety_utils import CommandParser
parsed = CommandParser.parse_task_command(args)
title = parsed['title']
description = parsed['description']  # 없으면 빈 문자열
```

## 2. 적용 예시

### WorkflowCommands 개선
```python
from python.workflow.safety_utils import safe_get, safe_json, CommandParser

class WorkflowCommands:
    def handle_status(self, args: str) -> Dict[str, Any]:
        """개선된 상태 확인"""
        try:
            current_plan = self.workflow.get_current_plan()

            if not current_plan:
                return {
                    'success': True,
                    'status': 'no_plan',
                    'message': '활성 계획 없음'
                }

            # Enum 값 비교 (문자열이 아닌 Enum으로)
            completed_count = sum(
                1 for task in current_plan.tasks 
                if task.status == TaskStatus.COMPLETED
            )

            # 안전한 직렬화
            return safe_json({
                'success': True,
                'status': 'active',
                'plan': {
                    'id': current_plan.id,
                    'name': current_plan.name,
                    'progress': (completed_count / len(current_plan.tasks)) * 100
                },
                'current_task': self.workflow.get_current_task()
            })

        except Exception as e:
            return {'success': False, 'error': str(e)}
```

## 3. 마이그레이션 체크리스트

- [ ] 모든 딕셔너리 직접 접근을 `safe_get()`으로 변경
- [ ] `json.dumps()`를 `safe_json()`으로 변경
- [ ] Enum 비교시 `.value` 사용 또는 Enum 직접 비교
- [ ] 명령어 파싱을 `CommandParser` 사용으로 변경
- [ ] `hasattr()` 체크 추가 또는 `safe_getattr()` 사용
- [ ] try-except 블록으로 예외 처리 강화

## 4. 테스트 가이드

```python
# 안전성 테스트
def test_safety_utils():
    # 1. safe_get 테스트
    data = {'a': {'b': {'c': 'value'}}}
    assert safe_get(data, 'a.b.c') == 'value'
    assert safe_get(data, 'a.b.x', 'default') == 'default'
    assert safe_get(None, 'a.b.c', 'default') == 'default'

    # 2. Enum 직렬화 테스트
    test_data = {
        'status': TaskStatus.COMPLETED,
        'list': [TaskStatus.TODO, TaskStatus.IN_PROGRESS]
    }
    json_str = safe_json(test_data)
    assert '"completed"' in json_str
    assert '"todo"' in json_str

    print("✅ 모든 테스트 통과")
```
