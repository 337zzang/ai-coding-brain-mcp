# 🔧 워크플로우-Todo 통합 시스템 기술 문서

## 시스템 아키텍처

### 핵심 클래스: IntegratedWorkflowManager

```python
class IntegratedWorkflowManager:
    def __init__(self):
        self.workflow_data = None
        self.todo_mapping = {}  # workflow_task_id -> [todo_ids]

    def create_workflow_with_todos(self, workflow_plan):
        # 워크플로우 생성과 동시에 연관된 todo들을 자동 생성

    def decompose_task_to_todos(self, task, task_idx):
        # 하나의 워크플로우 task를 여러 세부 todo로 분해

    def get_task_progress(self, task_id, current_todos):
        # 특정 task의 진행률을 해당 todo들의 완료 상태로 계산

    def sync_todos_to_workflow(self, current_todos):
        # 현재 todo 상태를 기반으로 workflow 상태 업데이트
```

### 통합 포인트

1. **Claude Code TodoWrite API**
   - 생성된 todo들을 Claude Code UI에 자동 반영
   - 사용자의 todo 상태 변경을 실시간 감지

2. **ai-coding-brain-mcp execute_code**
   - 워크플로우 로직 실행 및 상태 관리
   - helpers 함수를 통한 파일 및 데이터 처리

### 데이터 구조

#### Todo 객체
```json
{
    "id": "task-{task_idx}-todo-{order}",
    "content": "[Task {n}] 세부 작업 설명",
    "status": "pending|in_progress|completed",
    "priority": "high|medium|low",
    "workflow_task_id": "parent_task_uuid",
    "task_order": 1
}
```

#### Workflow Task 객체  
```json
{
    "id": "task_uuid",
    "title": "작업 제목",
    "description": "작업 설명",
    "status": "pending|in_progress|completed",
    "progress_percent": 0-100,
    "estimated_time": "예상 소요 시간",
    "started_at": "시작 시간",
    "completed_at": "완료 시간"
}
```

### 동기화 알고리즘

1. **Todo → Task 진행률 계산**
```python
def get_task_progress(task_id, current_todos):
    task_todo_ids = self.todo_mapping[task_id]
    task_todos = [todo for todo in current_todos if todo['id'] in task_todo_ids]
    completed_todos = [todo for todo in task_todos if todo['status'] == 'completed']
    return len(completed_todos) / len(task_todos) * 100
```

2. **Task 상태 자동 업데이트**
```python
if progress == 100:
    task['status'] = 'completed'
elif progress > 0:
    task['status'] = 'in_progress'
else:
    task['status'] = 'pending'
```

### 메모리 저장 구조

- `memory/workflow_integration_system.json`: 시스템 메타데이터
- `memory/workflow_learning_context.json`: 학습 컨텍스트
- `memory/enhanced_workflow_procedure.json`: 절차 정의
- `memory/current_workflow.json`: 현재 활성 워크플로우

### 확장 포인트

1. **커스텀 Task 분해 로직**
   - `decompose_task_to_todos()` 메서드 확장
   - 작업 유형별 특화된 분해 패턴 추가

2. **진행률 계산 커스터마이징**
   - 가중치 기반 진행률 계산
   - 우선순위별 차등 점수 적용

3. **알림 및 이벤트 시스템**
   - Task 완료 시 자동 알림
   - 마일스톤 달성 이벤트 처리

---
기술 문의: ai-coding-brain-mcp 시스템 내 helpers.* 함수 활용
