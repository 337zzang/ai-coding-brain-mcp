# o3 Flow 폴더 구조 분석 결과

## 분석 요청
Flow 시스템을 폴더 기반 구조로 재설계

## o3 분석 결과
아래 설계는 “폴더-기반 Flow”를 목표로, 기존 코드(단일 flows.json)에 손을 대지 않고도 단계적으로 확장할 수 있도록 작성되었습니다.  
모든 예시는 Python 3.10+, 표준 라이브러리만 사용(단, orjson / filelock 등은 선택 사항)했습니다.

────────────────────────────────────
1. 디렉터리 레이아웃
────────────────────────────────────
프로젝트/
└── .ai-brain/
    └── flow/                       # Flow 루트
        ├── flow.json               # Flow 메타 정보(Plan ID 리스트만)
        ├── plans/
        │   ├── plan_<id>.json      # Plan + 내부 Task 목록
        │   └── …
        └── context/
            └── events.json         # (선택) 행동 로그

장점
• Plan 단위 Git diff가 깨끗하게 남는다.  
• 대용량 Task를 가진 Plan만 부분 로드/저장 가능.  
• 여러 Flow라도 “.ai-brain/” 한 곳에서 관리 가능(프로젝트 격리).

────────────────────────────────────
2. 도메인 모델(변경 최소화)
────────────────────────────────────
models.py

@dataclass
class Flow:
    id: str
    name: str
    plan_ids: list[str]             # 기존 plans: dict → plan_ids 로 변경
    project: Optional[str] = None
    created_at: str = …
    updated_at: str = …

@dataclass
class Plan:
    id: str
    name: str
    tasks: dict[str, Task]          # 기존과 동일
    flow_id: str                    # 소속 Flow 명시
    …

※ 기존 API 호환성을 위해 Flow.plans 속성을 @property 로 제공하여
   접근 시 PlanRepository에서 lazy-load 하도록 할 수 있다.

────────────────────────────────────
3. 저장소 계층(Repository Layer)
────────────────────────────────────
interface repository.py
```python
from abc import ABC, abstractmethod

class FlowRepository(ABC):
    @abstractmethod
    def save_flow(self, flow: Flow): ...
    @abstractmethod
    def load_flow(self, flow_id: str) -> Flow | None: ...
    @abstractmethod
    def list_flows(self, project: str | None = None) -> list[Flow]: ...

class PlanRepository(ABC):
    def save_plan(self, plan: Plan): ...
    def load_plan(self, flow_id: str, plan_id: str) -> Plan | None: ...
    def delete_plan(self, flow_id: str, plan_id: str): ...
```

파일 구현 file_repo.py
```python
import json, os, pathlib, uuid, shutil, contextlib, time
from filelock import FileLock

class JsonFileMixin:
    @staticmethod
    def _atomic_write(path: pathlib.Path, data: dict):
        tmp = path.with_suffix('.tmp')
        with tmp.open('w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(path)

class FileFlowRepository(JsonFileMixin, FlowRepository):
    def __init__(self, base_path=".ai-brain/flow"):
        self.base = pathlib.Path(base_path)
        self.base.mkdir(parents=True, exist_ok=True)

    def _flow_dir(self, fid): return self.base / fid
    def _flow_meta(self, fid): return self._flow_dir(fid) / "flow.json"

    def save_flow(self, flow: Flow):
        d = self._flow_dir(flow.id)
        d.mkdir(exist_ok=True)
        self._atomic_write(self._flow_meta(flow.id), flow.to_dict())

    def load_flow(self, flow_id: str) -> Flow | None:
        p = self._flow_meta(flow_id)
        if not p.exists(): return None
        with p.open() as f: return Flow.from_dict(json.load(f))

    def list_flows(self, project: str | None = None):
        results = []
        for d in self.base.iterdir():
            if not d.is_dir(): continue
            f = self.load_flow(d.name)
            if f and (project is None or f.project == project):
                results.append(f)
        return results

class FilePlanRepository(JsonFileMixin, PlanRepository):
    def __init__(self, base_path=".ai-brain/flow"):
        self.base = pathlib.Path(base_path)

    def _plan_path(self, flow_id, plan_id):
        return self.base / flow_id / "plans" / f"{plan_id}.json"

    def save_plan(self, plan: Plan):
        path = self._plan_path(plan.flow_id, plan.id)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._atomic_write(path, plan.to_dict())

    def load_plan(self, flow_id, plan_id):
        p = self._plan_path(flow_id, plan_id)
        if not p.exists(): return None
        with p.open() as f: return Plan.from_dict(json.load(f))

    def delete_plan(self, flow_id, plan_id):
        p = self._plan_path(flow_id, plan_id)
        p.unlink(missing_ok=True)
```

────────────────────────────────────
4. 캐싱 계층
────────────────────────────────────
cache.py
```python
import functools, time
from collections import OrderedDict

class LRUCache:
    def __init__(self, max_size=128, ttl=60):
        self.max_size, self.ttl = max_size, ttl
        self._data = OrderedDict()

    def get(self, key):
        v = self._data.get(key)
        if v and (time.time() - v[1] < self.ttl):
            self._data.move_to_end(key)
            return v[0]
        self._data.pop(key, None)  # ttl 만료
        return None

    def set(self, key, value):
        self._data[key] = (value, time.time())
        self._data.move_to_end(key)
        if len(self._data) > self.max_size:
            self._data.popitem(last=False)

    def invalidate(self, key=None):
        if key is None: self._data.clear()
        else: self._data.pop(key, None)
```

CachedFlowService v2
```python
class CachedFlowService:
    def __init__(self, base_path=".ai-brain/flow"):
        self._flow_repo = FileFlowRepository(base_path)
        self._plan_repo = FilePlanRepository(base_path)
        self._flow_cache = LRUCache(64, ttl=30)
        self._plan_cache = LRUCache(256, ttl=30)

    # ---- Flow ----------
    def load_flow(self, fid):
        c = self._flow_cache.get(fid)
        if c: return c
        f = self._flow_repo.load_flow(fid)
        if f: self._flow_cache.set(fid, f)
        return f

    def save_flow(self, flow: Flow):
        self._flow_repo.save_flow(flow)
        self._flow_cache.invalidate(flow.id)

    # ---- Plan ----------
    def load_plan(self, fid, pid):
        key = f"{fid}:{pid}"
        c = self._plan_cache.get(key)
        if c: return c
        p = self._plan_repo.load_plan(fid, pid)
        if p: self._plan_cache.set(key, p)
        return p

    def save_plan(self, plan: Plan):
        self._plan_repo.save_plan(plan)
        self._plan_cache.invalidate(f"{plan.flow_id}:{plan.id}")
```

특징  
• Flow와 Plan을 서로 다른 LRU로 관리 → 메모리 사용 최소.  
• 파일 타임스탬프를 주기적으로(옵션) 감시해 자동 무효화 가능(Watchdog 사용).  
• atomic_write + rename 으로 손상 방지.

────────────────────────────────────
5. FlowManager 수정(핵심만)
────────────────────────────────────
```python
class FlowManager:
    def __init__(self, base_path=".ai-brain/flow", context_enabled=True):
        self._svc = CachedFlowService(base_path)
        …

    # ---- Plan CRUD ----
    @auto_record()
    def create_plan(self, flow_id: str, name: str) -> Plan:
        flow = self._svc.load_flow(flow_id) or raise FlowError
        plan_id = create_plan_id()
        plan = Plan(id=plan_id, name=name, tasks={}, flow_id=flow_id)
        self._svc.save_plan(plan)

        # 메타에 plan_id 추가
        flow.plan_ids.append(plan_id)
        flow.updated_at = now_utc()
        self._svc.save_flow(flow)

        record_plan_action(flow_id, plan_id, 'plan_created', {'name': name})
        return plan

    def get_plan(self, flow_id, plan_id) -> Plan | None:
        return self._svc.load_plan(flow_id, plan_id)

    def list_plans(self, flow_id) -> list[Plan]:
        flow = self._svc.load_flow(flow_id)
        return [self._svc.load_plan(flow_id, pid) for pid in flow.plan_ids]

    @auto_record()
    def delete_plan(self, flow_id, plan_id):
        flow = self._svc.load_flow(flow_id)
        flow.plan_ids.remove(plan_id)
        flow.updated_at = now_utc()
        self._svc.save_flow(flow)
        self._svc._plan_repo.delete_plan(flow_id, plan_id)
        self._svc._plan_cache.invalidate(f"{flow_id}:{plan_id}")
```

Task CRUD 역시 Plan만 다시 저장하면 된다.

────────────────────────────────────
6. 파일 I/O 최적화
────────────────────────────────────
1) Plan 로드-온-디맨드  
   - 대용량 Task를 가진 Plan만 메모리에 올린다.  
2) Atomic rename write  
   - 임시 .tmp → replace, 장애 시 이전 파일 보존.  
3) Chunked Task append  
   - Task 추가만 있을 때 전체 Plan을 다시 직렬화하는 대신  
     “tasks”를 JSON Lines 형식 tasks.jl 로 별도 분리 가능.  
4) orjson, ujson 옵션  
5) filelock / fcntl 락으로 동시 접근 보호.

────────────────────────────────────
7. 마이그레이션 전략
────────────────────────────────────
scripts/migrate_v1_to_v2.py
```python
from pathlib import Path, mkdir
import json, uuid, shutil
from domain.models import Flow, Plan, Task

old = Path(".ai-brain/flows.json")
new_root = Path(".ai-brain/flow")

with old.open() as f:
    data = json.load(f)   # {flow_id: {...}}

for fid, fdict in data.items():
    flow = Flow.from_dict(fdict)
    flow_dir = new_root / fid / "plans"
    flow_dir.mkdir(parents=True, exist_ok=True)

    # Plan 변환
    new_plan_ids = []
    for pid, p in fdict["plans"].items():
        plan = Plan.from_dict(p)
        plan.flow_id = fid
        FilePlanRepository(new_root).save_plan(plan)
        new_plan_ids.append(plan.id)

    # Flow 메타 저장
    flow.plan_ids = new_plan_ids
    FileFlowRepository(new_root).save_flow(flow)

# 백업 후 기존 파일 보존
old.rename(old.with_suffix(".bak"))
```
• O(전체플로우)지만 1회만 실행.  
• 롤백은 .bak 파일 복구.

────────────────────────────────────
8. API 호환성 유지
────────────────────────────────────
1) 동일 메서드 시그니처 유지  
   - create_flow, create_plan, create_task … 변함 없음.  
2) Flow.plans 프로퍼티
```python
class Flow(…):
    @property
    def plans(self) -> dict[str, Plan]:
        # 호환 목적
        mgr = LazyServiceLocator.get_service('cached_flow')  # 전역 or DI
        return {pid: mgr.load_plan(self.id, pid) for pid in self.plan_ids}
```
3) 기존 flows.json 감지 → 자동 마이그레이션 실행 후 계속 진행.  
4) tests/ 에 기존 단위 테스트 그대로 통과 보장.

────────────────────────────────────
9. 향후 확장 포인트
────────────────────────────────────
• Plan 서브폴더에 attachments/ 저장해 Task 산출물 관리  
• Flow/Plan metadata JSON Schema 버전 필드 추가  
• SQLite 백엔드와 Adapter 패턴으로 교체 가능

────────────────────────────────────
요약
1. Flow 메타와 Plan(+Task) JSON 파일을 분리해 Git diff, 부분 I/O 최적화  
2. Repository → Cache → Manager 3-계층으로 파일 시스템에 안전 접근  
3. CRUD 는 Plan 파일만 재작성, Flow 는 plan_id 리스트만 갱신  
4. migrate_v1_to_v2 스크립트로 기존 데이터 자동 변환  
5. 도메인 모델 변경 최소화 + @property + Manager 래퍼로 API 100% 유지

## 분석 일시
2025-07-24T19:56:47.163658

## 토큰 사용량
- Prompt: 1560
- Completion: 3268
- Total: 4828
