# o3 분석: 컨텍스트 저장 방식 개선

**작성일**: 2025-07-23 18:54:03
**Task ID**: o3_task_0001

## 분석 결과

아래 내용은 “AI Coding Brain – MCP” 저장소에 실존하는 파일·클래스 이름( flow_manager.py, cached_flow_service.py …)을 그대로 사용해 서술한 “가능한” 구조/개선안입니다.  
(실제 코드가 조금 다르면 경로-이름만 맞춰 주시면 됩니다.)

────────────────────────────────────
1. FlowManager 와 CachedFlowService 현재 구조 분석
────────────────────────────────────
python/ai_helpers_new/flow_manager.py
------------------------------------------------------------------------------
class FlowManager:
    def __init__(self, flow_service: CachedFlowService):  
        self._service = flow_service              # 메타데이터·캐시 계층
        self._mem_cache: Dict[str, Task] = {}     # 프로세스 내 캐시

    # ↓ 현재 문제가 된 메서드
    def update_task_context(self, task_id, key, value) -> None:
        """
        (1) 인자 시그니처가 key/value 쌍.
        (2) 기존 컨텍스트와 머지 로직 없음.
        (3) self._service 쪽 메서드 호출부도 맞지 않는다.
        """
        ...

python/ai_helpers_new/service/cached_flow_service.py
------------------------------------------------------------------------------
class CachedFlowService:
    def __init__(self, backend: FlowBackend):  # DB or REST
        self._backend = backend
        self._lru_cache = LRUCache(maxsize=128) # 프로세스 내부 캐시

    def get_task(self, task_id) -> Task: ...
    def save_task(self, task: Task) -> None: ...
    # 아직 “context” 전용 API 는 없다.

현재 흐름
FlowManager        ↔        CachedFlowService        ↔        FlowBackend
(서비스 레이어)             (캐시 +  I/O)                     (DB / REST)

문제점
• Task.extra_data 같은 필드에 context 를 저장할 수 있는데 FlowManager 쪽 메서드가 이를 활용하지 못한다.  
• Flow CLI / UI 에서 조회할 수 없는 JSON 파일을 임시로 떨궈 두고 있음.



────────────────────────────────────
2. update_task_context “올바른” 시그니처 & 사용법
────────────────────────────────────
“컨텍스트 전체 dict” 를 한 번에 전달하고, Merge 동작을 옵션으로 둔다.

def update_task_context(
        self,
        task_id: str,
        context: Dict[str, Any],
        *,
        merge: bool = True
) -> Dict[str, Any]:
    """
    • merge=True : 기존 context 와 dict union.
    • return : 병합 후 최종 context.
    """
    task = self._service.get_task(task_id)

    existing = (task.extra_data or {}).get("context", {})
    task.extra_data = task.extra_data or {}

    task.extra_data["context"] = {**existing, **context} if merge else context
    self._service.save_task(task)

    # 프로세스 캐시 동기화
    self._mem_cache[task_id] = task
    return task.extra_data["context"]

호출 예시
FlowManager.update_task_context(task_id, {"retrieved_file": "spec.yaml"})

레거시 호환용 래퍼 (legacy_flow_adapter.py)
def add_to_context(task_id, key, value):
    fm = FlowManager.get()            # 싱글톤
    fm.update_task_context(task_id, {key: value}, merge=True)



────────────────────────────────────
3. Flow 시스템과 “완전히” 통합하는 최선의 방법
────────────────────────────────────
가. DB/모델 계층
• Task 테이블(혹은 Document)에 jsonb/text 컬럼 context 추가
  (있다면 extra_data.context 를 그대로 사용)

나. CachedFlowService 계층
class CachedFlowService:
    ...
    def get_task_context(self, task_id) -> Dict[str, Any]:
        task = self.get_task(task_id)
        return (task.extra_data or {}).get("context", {})

    def set_task_context(self, task_id, ctx: Dict[str, Any]) -> None:
        task = self.get_task(task_id)
        task.extra_data = task.extra_data or {}
        task.extra_data["context"] = ctx
        self.save_task(task)

다. Flow CLI / Dashboard 노출
• Metaflow 의 경우 : task.set_tag("context", json.dumps(ctx))  
• Prefect 2.x : state.result() / task.set_variable()  
• Dagster : event_metadata={"context": ctx}

즉 “태그 또는 메타데이터” 로도 복사해 두면 Flow UI 에서 바로 볼 수 있게 된다.



────────────────────────────────────
4. “작업별 컨텍스트 자동 저장” 메커니즘
────────────────────────────────────
핵심 아이디어 :  
(1) 모든 Step/Task 함수가 끝날 때 FlowManager.update_task_context 를 자동 호출  
(2) 호출부를 최소화 하기 위해 Decorator 또는 ContextManager 사용

Decorator 예시
------------------------------------------------------------------------------
# context_integration.py
def auto_context(*capture_args):
    """
    capture_args : 저장할 변수 이름들.
    """

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            task_id = kwargs.get("task_id") or args[0].task_id
            result = fn(*args, **kwargs)

            bound = inspect.signature(fn).bind(*args, **kwargs)
            bound.apply_defaults()

            ctx_update = {name: bound.arguments[name] for name in capture_args
                          if name in bound.arguments}

            FlowManager.get().update_task_context(task_id, ctx_update)
            return result
        return wrapper
    return decorator


사용 예시
------------------------------------------------------------------------------
class GitCloneService:
    @auto_context("repo_url", "branch")
    def execute(self, task_id: str, repo_url: str, branch: str = "main"):
        ... # 실제 클론 로직

결과  
• repo_url, branch 두 키가 Task.context 로 자동 저장  
• 서비스 레이어는 한 줄의 애노테이션만 추가.



────────────────────────────────────
5. “최소 수정”으로 기존 코드 살리면서 통합하기
────────────────────────────────────
Step 0) JSON 파일 → Flow 로 이관 스크립트(1회성)
------------------------------------------------------------------------------
# migrate_json_context.py
for file in Path("./context_dump").glob("*.json"):
    with open(file) as fp:
        data = json.load(fp)
        task_id = data["task_id"]
        FlowManager.get().update_task_context(task_id, data["context"], merge=True)

Step 1) FlowManager 메서드 시그니처 변경 + 구버전 래퍼 유지
------------------------------------------------------------------------------
# flow_manager.py
class FlowManager:
    ...
    def update_task_context(self, task_id, context, *, merge: bool=True):
        ...

# legacy_flow_adapter.py  (구 메서드 그대로 쓰던 코드 대응)
def update_task_context(task_id, key, value):
    FlowManager.get().update_task_context(task_id, {key: value}, merge=True)

기존 코드에서는
legacy_flow_adapter.update_task_context(task_id, "last_file", "foo.txt")
처럼 호출하므로 수정 필요 없다.

Step 2) CachedFlowService 에 context 전용 API 소규모 추가
------------------------------------------------------------------------------
class CachedFlowService:
    def get_task_context(self, task_id): ...
    def set_task_context(self, task_id, ctx): ...

save_task / get_task 는 이미 있으므로 구현은 10~15줄.

Step 3) (선택) 각 Service 메서드에 @auto_context 적용
• 점진적 도입 : 컨텍스트가 꼭 필요한 일부 서비스부터 붙인다.
• 데코레이터 한 줄 추가만으로 끝.

Step 4) Flow UI 태그 연동
• FlowManager.update_task_context 내부에서
  self._service.add_tag(task_id, "context:"+base64.b64encode(json.dumps(ctx)))
  정도를 호출해 놓으면 CLI 검색도 가능.



────────────────────────────────────
요약
────────────────────────────────────
1. update_task_context 시그니처를 (task_id, context_dict, merge=True) 로 단일화한다.  
2. CachedFlowService 에 get/set_task_context API 를 15줄 이하로 추가한다.  
3. legacy_flow_adapter 에 thin-wrapper 를 둬서 기존 key/value 호출 코드를 살린다.  
4. @auto_context 데코레이터(또는 ContextManager) 로 “서비스 → 컨텍스트” 자동 기록을 지원한다.  
5. extra_data.context 컬럼 + Flow 태그(또는 메타데이터) 2중 저장으로 Flow CLI 에서도 조회할 수 있게 한다.  

이렇게 하면
• 더 이상 JSON 파일 관리가 필요 없고,  
• Flow 대시보드/CLI 로도 컨텍스트를 즉시 조회,  
• 컨텍스트 기반 추천(“이전 스텝에서 사용한 repo_url 을 자동 제안”) 같은 고급 기능을 손쉽게 붙일 수 있습니다.

## 주요 개선 사항 요약

### 1. FlowManager 메서드 시그니처 개선
- 현재: `update_task_context(task_id, key, value)`
- 개선: `update_task_context(task_id, context: Dict[str, Any], *, merge: bool = True)`

### 2. CachedFlowService에 컨텍스트 전용 API 추가
- `get_task_context(task_id) -> Dict[str, Any]`
- `set_task_context(task_id, ctx: Dict[str, Any]) -> None`

### 3. 자동 컨텍스트 저장 메커니즘
- `@auto_context` 데코레이터 구현
- 서비스 메서드 실행 후 자동으로 컨텍스트 저장

### 4. 레거시 호환성 유지
- `legacy_flow_adapter.py`에 래퍼 함수 추가
- 기존 코드 수정 최소화

### 5. Flow UI/CLI 통합
- 태그 또는 메타데이터로 컨텍스트 노출
- Flow 대시보드에서 직접 조회 가능
