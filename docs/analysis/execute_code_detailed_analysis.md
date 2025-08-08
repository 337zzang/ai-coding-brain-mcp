# Execute_code 문제점 상세 분석 - 실제 코드 검증 결과

## 🔍 실제 코드 검증 결과

### 1. FlowAPI 실제 메서드 (23개 확인)

#### ✅ 문서와 일치하는 메서드들
- `create_plan()`, `select_plan()`, `get_current_plan()`
- `list_plans()`, `get_plan()`, `update_plan()`, `delete_plan()`
- `create_task()`, `add_task()`, `get_task()`, `get_task_by_number()`
- `list_tasks()`, `update_task()`, `update_task_status()`
- `search()`, `get_stats()`, `set_context()`, `get_context()`, `clear_context()`

#### 🔴 존재하지 않는 메서드 (오류 원인)
- ❌ `show_status()` - 실제로 없음 → `get_current_plan()` 사용
- ❌ `show_plans()` - 실제로 없음 → `list_plans()` 사용

#### 📌 내부 메서드 (사용 불가)
- `_res()` - 표준 응답 형식 생성 (내부용)
- `_sync()` - Manager와 동기화 (내부용)

### 2. Task 모델 실제 구조 (dataclass)

```python
@dataclass
class Task:
    id: str
    title: str  # ✅ 'name'이 아닌 'title' 사용
    description: str = ""
    status: TaskStatus = TaskStatus.TODO
    priority: int = 0
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None
    assignee: Optional[str] = None
    number: Optional[int] = None  # ⚠️ Optional - None 가능
    tags: List[str]
    metadata: Dict[str, Any]
```

#### 🔍 Task number 처리 방식
- `create_task()` 메서드에서 자동 할당
- 기존 Task들의 최대 번호 + 1
- 첫 Task는 1번부터 시작

### 3. TaskStatus Enum 개선 확인

```python
class TaskStatus(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"

    @classmethod
    def _missing_(cls, value):
        # 대소문자 무관 처리 ✅
        # 별칭 지원: 'completed' → 'done' ✅
        # 'canceled' → 'cancelled' ✅
```

### 4. 표준 응답 형식 일관성

#### FlowAPI._res() 메서드 구현
```python
def _res(self, ok: bool, data: Any = None, error: str = None):
    return {"ok": ok, "data": data, "error": error}
```

#### ⚠️ 체이닝 메서드 예외
- `select_plan()` - FlowAPI 객체 반환 (체이닝용)
- `set_context()` - FlowAPI 객체 반환 (체이닝용)
- `clear_context()` - FlowAPI 객체 반환 (체이닝용)

## 📊 문제 패턴 최종 정리

### 1. API 사용 혼동 (40%)
| 잘못된 사용 | 올바른 사용 | 빈도 |
|-------------|-------------|------|
| `api.show_status()` | `api.get_current_plan()` | 3회 |
| `result = api.select_plan()` | `api.select_plan()` (체이닝) | 2회 |
| `h.flow()` 초기화 오류 | `api = h.get_flow_api()` | 2회 |

### 2. 데이터 구조 혼동 (30%)
| 잘못된 접근 | 올바른 접근 | 빈도 |
|-------------|-------------|------|
| `task['name']` | `task['title']` | 2회 |
| `git_status['data']['modified']` | `git_status['data']['files']` | 2회 |
| 직접 data 접근 | `if result['ok']: data = result['data']` | 3회 |

### 3. 함수명 오류 (20%)
| 잘못된 이름 | 올바른 이름 | 빈도 |
|-------------|-------------|------|
| `h.file_info()` | `h.get_file_info()` | 1회 |
| `filePattern=` | `file_pattern=` | 1회 |

### 4. 타입 오류 (10%)
- TypeError: FlowAPI not subscriptable
- TypeError: unexpected keyword argument

## ✅ 검증된 해결책

### 1. FlowAPI 사용 베스트 프랙티스
```python
# API 초기화
api = h.get_flow_api()

# 일반 메서드 (표준 응답)
result = api.create_plan("플랜명")
if result['ok']:
    plan = result['data']

# 체이닝 메서드 (반환값 무시)
api.select_plan(plan_id).set_context('key', 'value')
```

### 2. Task 작업 표준 패턴
```python
# Task 생성
result = api.create_task(plan_id, "Task 제목")
if result['ok']:
    task = result['data']
    print(f"Title: {task['title']}")  # 'name' 아님!
    print(f"Number: {task.get('number', 'N/A')}")  # None 체크
```

### 3. Git 상태 확인 표준
```python
git_result = h.git_status()
if git_result['ok']:
    data = git_result['data']
    files = data['files']  # 변경 파일 목록
    branch = data['branch']
    count = data['count']
```

## 🎯 핵심 교훈

1. **항상 API 문서 대신 실제 코드 확인**
2. **표준 응답 형식 철저히 준수**
3. **체이닝 메서드는 특별 취급**
4. **Optional 필드는 None 체크 필수**
5. **데이터 구조는 실제 모델 정의 참조**
