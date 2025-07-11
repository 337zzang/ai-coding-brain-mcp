# Workflow v2 API Reference

## 목차
1. [WorkflowV2Manager](#workflowv2manager)
2. [Handler Functions](#handler-functions)
3. [Dispatcher](#dispatcher)
4. [Models](#models)
5. [HelperResult](#helperresult)

---

## WorkflowV2Manager

워크플로우를 관리하는 핵심 클래스입니다.

### 생성자
```python
WorkflowV2Manager(project_name: str)
```
- `project_name`: 프로젝트 이름 (파일명에 사용됨)

### 메서드

#### create_plan
```python
create_plan(name: str, description: str = "") -> WorkflowPlan
```
새로운 플랜을 생성합니다.

#### add_task
```python
add_task(title: str, description: str = "") -> Task
```
현재 플랜에 태스크를 추가합니다.

#### get_current_task
```python
get_current_task() -> Optional[Task]
```
현재 진행 중인 태스크를 반환합니다.

#### complete_task
```python
complete_task(task_id: str, notes: str = "") -> Optional[Task]
```
지정된 태스크를 완료 처리합니다.

#### get_status
```python
get_status() -> Dict[str, Any]
```
현재 워크플로우 상태를 반환합니다.

---

## Handler Functions

### workflow_status
```python
workflow_status() -> HelperResult
```
현재 워크플로우 상태를 조회합니다.

**반환값**:
```python
{
    'success': True,
    'status': 'active',
    'plan_name': '플랜 이름',
    'total_tasks': 5,
    'completed_tasks': 2,
    'progress_percent': 40.0
}
```

### workflow_plan
```python
workflow_plan(name: str, description: str = "", reset: bool = False) -> HelperResult
```
새 플랜을 생성합니다.

**매개변수**:
- `name`: 플랜 이름
- `description`: 플랜 설명 (선택)
- `reset`: 기존 플랜 초기화 여부 (선택)

### workflow_task
```python
workflow_task(title: str, description: str = "") -> HelperResult
```
태스크를 추가합니다.

**매개변수**:
- `title`: 태스크 제목
- `description`: 태스크 설명 (선택)

### workflow_done
```python
workflow_done(summary: str = "", details: List[str] = None, outputs: Dict = None) -> HelperResult
```
현재 태스크를 완료 처리합니다.

---

## Dispatcher

### execute_workflow_command
```python
execute_workflow_command(command: str) -> HelperResult
```
텍스트 명령어를 실행합니다.

**지원 명령어**:
- `/status` - 상태 조회
- `/plan <이름> | <설명>` - 플랜 생성
- `/task <제목> | <설명>` - 태스크 추가
- `/done [메모]` - 태스크 완료
- `/next` - 다음 태스크로 이동
- `/history` - 작업 이력 조회

---

## Models

### TaskStatus (Enum)
```python
TODO = "todo"
IN_PROGRESS = "in_progress"
COMPLETED = "completed"
CANCELLED = "cancelled"
```

### PlanStatus (Enum)
```python
DRAFT = "draft"
ACTIVE = "active"
COMPLETED = "completed"
ARCHIVED = "archived"
```

### Task
```python
@dataclass
class Task:
    id: str
    title: str
    description: str
    status: TaskStatus
    created_at: str
    completed_at: Optional[str]
    updated_at: str
    notes: List[str]
    outputs: Dict[str, Any]
```

### WorkflowPlan
```python
@dataclass
class WorkflowPlan:
    id: str
    name: str
    description: str
    status: PlanStatus
    tasks: List[Task]
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]
```

---

## HelperResult

모든 API 함수의 반환 타입입니다.

### 속성
- `ok`: 성공 여부 (bool)
- `data`: 결과 데이터 (dict)
- `error`: 에러 메시지 (str, 실패시만)

### 메서드
```python
get_data(default=None) -> Any
```
안전하게 데이터를 가져옵니다. 실패시 default 반환.

### 사용 예시
```python
result = workflow_plan("새 프로젝트", "설명")
if result.ok:
    data = result.get_data({})
    print(f"플랜 ID: {data.get('plan_id')}")
else:
    print(f"오류: {result.error}")
```
