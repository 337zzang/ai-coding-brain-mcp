# WorkflowManager 통합 가이드

## 1. 기본 사용법

```python
from core.workflow_manager import get_workflow_manager

# WorkflowManager 인스턴스 가져오기
wm = get_workflow_manager()

# 프로젝트 로드
result = wm.load_project("my-project")
if result['success']:
    print(f"프로젝트 로드: {result['data']['project']}")
```

## 2. 계획 관리

```python
# 새 계획 생성
result = wm.create_plan(
    name="스프린트 1",
    description="첫 번째 개발 스프린트"
)

# 커스텀 Phase로 계획 생성
phases = [
    {
        'id': 'backend',
        'name': '백엔드 개발',
        'description': 'API 개발',
        'tasks': []
    },
    {
        'id': 'frontend',
        'name': '프론트엔드 개발',
        'description': 'UI 구현',
        'tasks': []
    }
]

result = wm.create_plan("프로젝트 알파", "전체 개발 계획", phases)
```

## 3. 작업 관리

```python
# 작업 추가
result = wm.add_task(
    phase_id="backend",
    title="사용자 인증 API",
    description="JWT 기반 인증 구현",
    priority="high",
    dependencies=[]
)

# 다음 작업 시작
result = wm.start_next_task()
if result['success']:
    task_data = result['data']
    print(f"시작: {task_data['title']} (예상 {task_data['estimated_hours']}시간)")

# 작업 완료
result = wm.complete_task()
if result['data']['phase_completed']:
    print("Phase도 완료되었습니다!")
```

## 4. 상태 조회 및 분석

```python
# 전체 워크플로우 상태
status = wm.get_workflow_status()
print(f"진행률: {status['progress']['percentage']:.1f}%")

# 작업 분석
analytics = wm.get_task_analytics()
print(f"효율성: {analytics['efficiency']:.1f}%")

# 병목 현상 분석
bottlenecks = wm.get_bottlenecks()
for bottleneck in bottlenecks:
    if bottleneck['type'] == 'blocked_task':
        print(f"차단됨: {bottleneck['title']} - {bottleneck['reason']}")
    elif bottleneck['type'] == 'overdue_task':
        print(f"지연됨: {bottleneck['title']} ({bottleneck['overdue_by']:.1f}시간 초과)")
```

## 5. 이벤트 훅 활용

```python
# 작업 완료 시 알림
def on_task_completed(task):
    print(f"🎉 완료: {task.title}")
    # Wisdom 시스템에 기록
    wisdom.add_best_practice(f"{task.title} 완료", "workflow")

wm.register_hook('task_completed', on_task_completed)

# 작업 차단 시 알림
def on_task_blocked(task):
    print(f"⚠️ 차단: {task.title} - {task.blocking_reason}")

wm.register_hook('task_blocked', on_task_blocked)
```

## 6. 명령어 리팩토링 예시

### 기존 cmd_next.py
```python
# Before: 복잡한 dict 조작과 이원화된 큐 관리
def cmd_next():
    context = get_context_manager().context
    if not context.tasks.get('next'):
        # 복잡한 로직...
    # dict 변환, 수동 저장 등...
```

### 개선된 cmd_next.py
```python
# After: WorkflowManager 사용
def cmd_next():
    wm = get_workflow_manager()
    result = wm.start_next_task()
    
    if result['success']:
        data = result['data']
        if data.get('status') == 'blocked':
            print(f"⚠️ {data['message']}")
        else:
            print(f"🚀 작업 시작: {data['title']}")
    else:
        print(f"❌ {result['message']}")
    
    return result
```

## 7. 레거시 큐 마이그레이션

```python
# 구 context.tasks['next'] 큐를 Plan으로 마이그레이션
result = wm.migrate_legacy_queue()
print(f"마이그레이션 완료: {result['data']['migrated']}개 작업")
```

## 8. 에러 처리

```python
# 모든 메서드는 StandardResponse 반환
result = wm.add_task("invalid-phase", "테스트")

if not result['success']:
    print(f"에러 타입: {result['error']['type']}")
    print(f"메시지: {result['error']['message']}")
```
