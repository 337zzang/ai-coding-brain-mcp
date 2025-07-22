# FlowManagerUnified 문제점 분석 및 개선 방안

## 분석 일시
2025-07-22 09:10:12

## o3 AI 분석 결과

아래 내용은 FlowManagerUnified (v1)에서 발견된 핵심 결함을 요약‧분석하고, 특히 “Plan ID 중복”과 “Task 상태 관리”를 확실히 해결할 수 있는 구체적 개선안을 예시 코드와 함께 제시한 것입니다.  

──────────────────  
1. 원인 분석 (요약)  
──────────────────  
A. Plan ID 중복  
• ID 생성 로직이 `YYYYMMDD_HHMMSS` 단 1초 단위 타임스탬프만 사용 → 같은 초에 2회 이상 호출되면 충돌.  
• 생성 직후 중복 검사나 Registry 갱신을 하지 않음.  

B. Task 상태 관리 미흡  
• status 필드가 문자열 상수(“todo”, “reviewing” 등)로 흩어져 있고 Enum이나 FSM(Finite-State-Machine) 부재.  
• 유효하지 않은 전이(transition) 차단 로직 없음 → reviewing 으로 진입한 뒤 방치.  
• “planning / approved” 같은 상태가 코드에 정의돼 있지 않거나, 정의돼 있어도 CLI/API가 이를 인지하지 못함.  

C. 기타 구조적 문제  
• plan-task 참조가 일관되지 않아 Plan 1개에 Task가 몰림.  
• 저장/로드·Context 추적·CLI 명령어 오타 등 다수.  

──────────────────  
2. 설계 레벨 개선 전략  
──────────────────  
(1) ID & Registry  
• 고유 ID를 다음 규칙으로 생성  
  ‑ time.time_ns() (나노초) + uuid4 6자 해시 + prefix : O(10⁻⁹) 단위 충돌 방지  
• Plan / Task를 메모리와 저장소(파일·DB)에 “중앙 레지스트리” 단일 소스오브트루스로 보관 → 중복 시 raise.  

(2) 데이터 모델 (dataclass + Enum 권장)  
```
class PlanStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskStatus(Enum):
    TODO        = "todo"
    IN_PROGRESS = "in_progress"
    REVIEWING   = "reviewing"
    APPROVED    = "approved"
    BLOCKED     = "blocked"
    DONE        = "done"
    CANCELLED   = "cancelled"

@dataclass
class Task:
    id: str
    plan_id: str
    title: str
    status: TaskStatus = TaskStatus.TODO
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    context: dict = field(default_factory=lambda: deepcopy(DEFAULT_CONTEXT))

@dataclass
class Plan:
    id: str
    title: str
    status: PlanStatus = PlanStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.utcnow)
    tasks: list[str] = field(default_factory=list)   # Task IDs
```

(3) FSM(상태 기계) 내장  
• 상태 전이를 중앙 함수에서만 허용.  
```python
# 허용 전이 그래프
TASK_FSM = {
    TaskStatus.TODO:        {TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED},
    TaskStatus.IN_PROGRESS: {TaskStatus.REVIEWING, TaskStatus.BLOCKED, TaskStatus.CANCELLED},
    TaskStatus.REVIEWING:   {TaskStatus.APPROVED, TaskStatus.BLOCKED},
    TaskStatus.APPROVED:    {TaskStatus.DONE},
    TaskStatus.BLOCKED:     {TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED},
}
def change_task_status(task: Task, new: TaskStatus):
    allowed = TASK_FSM.get(task.status, set())
    if new not in allowed:
        raise ValueError(f"Illegal transition {task.status} → {new}")
    task.status = new
    task.updated_at = datetime.utcnow()
```

(4) 저장 메커니즘  
• 기본은 JSON or TinyDB 파일(`.flow/plan_{id}.json`) + 인메모리 캐시.  
• `FlowManagerUnified.save()` / `load()` 도입 (자동 호출).  
• 컨텍스트·파일 이력 등은 Plan JSON 하위 키로 직렬화.  

──────────────────  
3. 개선 후 주요 API (예시)  
──────────────────
```python
class FlowManagerUnified:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.plans: dict[str, Plan]  = {}
        self.tasks: dict[str, Task]  = {}
        self.load()                                  # ▶︎ 영속 데이터 로드

    # ---------- Plan ----------
    def create_plan(self, title: str) -> Plan:
        pid = self._new_id("plan")
        if pid in self.plans:            # 이론적으로 중복 불가, 방어 코드
            raise RuntimeError("ID collision")
        plan = Plan(id=pid, title=title)
        self.plans[pid] = plan
        self.save()
        return plan

    def _new_id(self, prefix: str) -> str:
        ns  = time.time_ns()
        rnd = uuid.uuid4().hex[:6]
        return f"{prefix}_{ns}_{rnd}"

    # ---------- Task ----------
    def add_task(self, plan_id: str, title: str) -> Task:
        plan = self.plans[plan_id]
        tid  = self._new_id("task")
        task = Task(id=tid, plan_id=plan_id, title=title)
        self.tasks[tid] = task
        plan.tasks.append(tid)
        self.save()
        return task

    def set_task_status(self, task_id: str, next_status: TaskStatus):
        task = self.tasks[task_id]
        change_task_status(task, next_status)
        self.save()

    # ---------- Persistence ----------
    def save(self):
        data = {
            "plans": dataclass_to_dict(self.plans),
            "tasks": dataclass_to_dict(self.tasks),
        }
        (self.root / "flow_state.json").write_text(json.dumps(data, default=str, indent=2))

    def load(self):
        file = self.root / "flow_state.json"
        if not file.exists():
            return
        data = json.loads(file.read_text())
        self.plans = {k: Plan(**v) for k, v in data["plans"].items()}
        self.tasks = {k: Task(**v) for k, v in data["tasks"].items()}
```

──────────────────  
4. CLI / Chat 명령 체계 개선  
──────────────────  
1) 규칙: `/flow <entity> <action> [options]` 로 고정.  
• entity: `plan | task`  
• action: `create | list | show | set-status | …`  
예) `/flow plan list`  `/flow task set-status task_xxx reviewing`

2) 잘못된 명령엔 usage 출력과 함께 Enum 값 힌트 제공.  

──────────────────  
5. “Plan ID 중복” 구체적 해결 경로  
──────────────────  
① ID 생성에 `time.time_ns()` + uuid4 를 도입 → 10억 분의 1초 해상도 & 난수.  
② Plan을 Dict index로만 관리, 생성 직후 `if id in self.plans` 체크.  
③ 동시성 가능성이 있다면 (예: FastAPI) Lock / atomic file write 사용.  

──────────────────  
6. “Task 상태 관리” 구체적 해결 경로  
──────────────────  
① Enum + FSM 테이블로 합법 전이 강제.  
② `FlowManager.set_task_status()` 한 곳으로 통로 단일화.  
③ “reviewing → approved” 가 일정 시간 내 일어나지 않으면 알림/FLAG (스케줄러/cron).  
④ CLI 에서 “--force” 옵션을 주지 않는 한 불법 전이 차단.  
⑤ 필요 시 GitHub PR, Slack 모듈과 연동해 “reviewing” 시 자동 알림.  

──────────────────  
7. 마이그레이션 절차  
──────────────────  
1) 기존 JSON (중복 Plan ID) → 새 구조로 migrate  
   ‑ 동일 ID Plan 여러 개 → 하나만 살리고 나머지는 suffix “_001” 등 붙여 rename.  
2) 무상태(Task 리스트 비어있는 Plan) → 빈 Plan 그대로 옮기되 status=DRAFT.  
3) status 문자열을 Enum 으로 매핑 불가한 경우 `BLOCKED` 또는 `UNKNOWN` 로 이동 후 수동 정정.  

──────────────────  
8. 기대 효과  
──────────────────  
• Plan ID 충돌 불가 → 첫 번째 문제 즉시 소거.  
• Task 진행 흐름이 투명해져 “reviewing 방치” 자동 검출·알림.  
• Plan/Task/Context 저장 규칙이 명확 → 데이터 손실·불일치 최소화.  
• CLI 명령 일관성 확보 → 사용자 혼란 감소.  

위 개선안(특히 ID 생성과 Task FSM)을 적용하면 현재 리포지터리의 주요 병목 원인 두 가지(Plan ID 중복, Task 상태 혼선)를 근본적으로 해결할 수 있습니다.

## 추가 정보
- 분석 노력: high
- 토큰 사용량: {'prompt_tokens': 682, 'completion_tokens': 2878, 'total_tokens': 3560, 'reasoning_tokens': 0}
