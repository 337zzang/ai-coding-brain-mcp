# o3 Flow 시스템 분석 결과

생성일: 2025-07-24T13:33:17.198513
분석 난이도: high
토큰 사용: 6696

---

✅ 핵심만 먼저 보기  
• 모듈 수 5 → 3 단계( Facade-Service-Repository )  
• FlowManagerUnified + LegacyFlowAdapter → “FlowFacade” 하나로 합치고 90일간만 alias 제공  
• elif 체인 Router → 데코레이터 기반 Command Registry  
• 파일 저장은 유지하되 file-lock, 변경 감지(ETag) 캐시, 백업 자동화 추가  
• Context는 각 Task/Plan/Flow 객체 안으로 인라인 → 별도 Wrapper 제거  

아래에 단계별 행동-리스트, 마이그레이션 전략, 핵심 코드 스케치까지 포함했습니다.  
(전체 난이도-순으로 정렬되어 있으므로 그대로 체크리스트로 써도 됩니다.)

----------------------------------------------------------------
1. 테스트 안전망 확보
----------------------------------------------------------------
① `pytest` + `pytest-cov` 세팅 – 반드시 현재 기능을 깨지 않는지 확인  
② 가장 많이 쓰는 30 여개 public API 와 CLI 시나리오를 통합 테스트로 캡처  
   ex) create→switch→add plan→update task … 실제 JSON 변화를 스냅샷 테스트  

----------------------------------------------------------------
2. 새 아키텍처   (5 → 3 단계)
----------------------------------------------------------------
                             ┌──────────────┐
 CLI / Bot / UI  ───────────▶│ FlowFacade   │  ←––(레거시 alias)
                             └──────────────┘
                                      │
                                      ▼
                             ┌──────────────┐
                             │ FlowService  │   (비즈니스 규칙)
                             └──────────────┘
                                      │
                                      ▼
                             ┌──────────────┐
                             │ JsonRepository│ (I/O, Lock)
                             └──────────────┘

• ContextWrapper, FlowContextWrapper, LegacyAdapter, FlowManagerUnified 삭제  
• 객체 모델:  dataclass `Flow, Plan, Task, Context`  (domain/models.py)  
• Service 는 순수 파이썬, Repository 는 I/O 와 Lock 만 담당  
• Facade 는 레거시 시그니처를 그대로 노출 + 새 API 라우팅

----------------------------------------------------------------
3. Legacy 두 클래스 통합
----------------------------------------------------------------
A. 신규 클래스                 flow/facade.py
```python
# facade.py
from typing import Optional, Dict, Any, List
from .service import FlowService
from .exceptions import ValidationError

class FlowFacade:
    """
    통합 진입점. 과거 FlowManagerUnified/LegacyFlowAdapter 대체
    """
    # ---- 생성 ----
    def __init__(self, *, context_enabled=True):
        self._svc = FlowService(context_enabled=context_enabled)

    # ---- 레거시 alias (90일동안 유지) ----
    # 단순 forward 만 하므로 @deprecated 로그 출력
    def __getattr__(self, item):
        import warnings, inspect
        if hasattr(self._svc, item):
            warnings.warn(f"{item} is deprecated – use FlowService.{item}", DeprecationWarning, stacklevel=2)
            return getattr(self._svc, item)
        raise AttributeError(item)

    # ---- 신 API 예시 ----
    def create_flow(self, name: str, project_id: Optional[str]=None) -> Dict[str, Any]:
        return self._svc.create_flow(name, project_id).to_dict()

    def list_flows(self, *, search:str=None, sort_by:str='name', include_archived=False) -> List[Dict]:
        return [f.to_dict() for f in self._svc.list_flows(search, sort_by, include_archived)]
```

B. import 호환
```python
# legacy_alias.py
from .facade import FlowFacade as FlowManagerUnified, FlowFacade as LegacyFlowAdapter
```

C. 제거 대상
• flow_manager_unified.py, legacy_flow_adapter.py 의 실제 구현 삭제하고 위 파일만 남겨 경고.

----------------------------------------------------------------
4. 상태 관리 단순화
----------------------------------------------------------------
현재 단계  
1) FlowManagerUnified  
2) LegacyFlowAdapter  
3) FlowManager  
4) FlowService  
5) ContextIntegration  

→ 아래 3 개만 남김  
1) FlowFacade (캐시·View State만)  
2) FlowService (도메인 상태, 캐시 안 함)  
3) JsonRepository (실제 저장)

추가 규칙  
• Service 에는 ‘현재 선택된 프로젝트/플로우’ 2개의 id 만 보존  
• Plan/Task 의 progress 는 enum(Enum: TODO, DOING, DONE, ARCHIVED) 로 통일  
• 모든 변경은 Service 가 수행하고, 변경 시점에 Repository.save() 호출  

----------------------------------------------------------------
5. 파일 기반 동시성 문제 해결
----------------------------------------------------------------
JsonRepository 개선
```python
# repository.py
import json, time, uuid
from pathlib import Path
from filelock import FileLock

DATA = Path('.ai-brain/flows.json')
LOCK = DATA.with_suffix('.lock')

class JsonRepository:
    def __init__(self, path:Path=DATA):
        self._path = path
        self._lock = FileLock(str(LOCK))

    def load(self) -> dict:
        with self._lock:
            if not self._path.exists():
                return {}
            return json.loads(self._path.read_text())

    def save(self, data:dict):
        tmp = self._path.with_suffix(f'.{uuid.uuid4().hex}.tmp')
        with self._lock:
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2))
            tmp.replace(self._path)  # atomic on POSIX
```
• filelock 으로 프로세스 간 mutex  
• tmp 파일 atomic 교체 → 부분-쓰기 문제 방지  
• 5 분마다 `.bak` timestamp 파일 자동 생성 (옵션)

----------------------------------------------------------------
6. Context 와 Flow 데이터 통합
----------------------------------------------------------------
• Task 내부 필드로 `context: Dict[str, Any]` 포함  
• Plan / Flow 레벨에서도 필요하면 동일 이름의 dict 제공  
• 별도 ContextWrapper 삭제하고 `task.context['actions']` 직접 접근  
• Service 에 고수준 메서드만 유지
   `update_context(scope, id_chain, patch_dict)`  
   (scope: flow/plan/task, id_chain: [flow_id, plan_id, task_id])

----------------------------------------------------------------
7. 명령어 라우터 개선
----------------------------------------------------------------
1) 데코레이터 등록 방식
```python
# cli/router.py
_command_map = {}

def command(*names):
    def decorator(func):
        for n in names:
            _command_map[n] = func
        return func
    return decorator
```

2) 사용 예
```python
@command('flow', 'f')
def flow_cmd(args, facade):
    ...
```

3) Route 함수
```python
def route(facade:FlowFacade, line:str):
    parts = line.strip().split()
    if not parts:
        return err('빈 명령')
    cmd, *args = parts
    handler = _command_map.get(cmd.lstrip('/'))
    return handler(args, facade) if handler else err(f'unknown {cmd}')
```

4) 하위 서브-커맨드는 Click 스타일로 재귀 등록 가능 → elif 체인 제거  
5) v30/v31 의 숫자-선택, 한글 “선택” 문법은 별도 parser 로 분리하여 testable unit 으로 둠

----------------------------------------------------------------
8. 단계별 마이그레이션 로드맵
----------------------------------------------------------------
Phase 0 – 1d  
• 테스트 확보, 코드 freeze

Phase 1 – 2d  
• `domain.models` dataclass 구현  
• JsonRepository 교체 + lock

Phase 2 – 2d  
• FlowService 신규 구현, 기존 FlowManager 로직 이관  
• 통합 Facade 작성, 레거시 alias 연결

Phase 3 – 1d  
• ContextWrapper, FlowManagerUnified, LegacyFlowAdapter 실제 코드 삭제  
• pylint / mypy 통과

Phase 4 – 2d  
• CommandRouter 리팩토링 (decorator registry)  
• CLI 테스트 갱신

Phase 5 – 1d  
• 문서, CHANGELOG, Deprecation 메시지 추가

Phase 6 – 2d  
• QA, 병렬 프로세스 테스트, 배포

총 ≈ 11 인/일

----------------------------------------------------------------
9. 참고 코드 스니펫 (추가)
----------------------------------------------------------------
Domain 모델 예시
```python
# domain/models.py
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any
class Status(str, Enum):
    TODO='todo'; DOING='doing'; DONE='done'; ARCHIVED='archived'

@dataclass
class Task:
    id: str
    name: str
    status: Status = Status.TODO
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Plan:
    id: str
    name: str
    tasks: List[Task] = field(default_factory=list)

@dataclass
class Flow:
    id: str
    name: str
    plans: List[Plan] = field(default_factory=list)
    archived: bool = False

    def to_dict(self):  # (역직렬화도 동일 패턴)
        ...
```

Service 주요 메서드
```python
class FlowService:
    def __init__(self, *, context_enabled=True, repo=None):
        self._repo = repo or JsonRepository()
        self._cache = self._repo.load()
        self.current_project: Optional[str] = None
        self.current_flow: Optional[str] = None
        self.context_enabled = context_enabled

    def _persist(self): self._repo.save(self._cache)

    def create_flow(self, name, project_id=None) -> Flow: ...
    def list_flows(self, search=None, sort_by='name', include_archived=False): ...
```

----------------------------------------------------------------
10. 예상 효과
----------------------------------------------------------------
• 코드 라인 수 약 40 % 감소, 중복 모듈 제거  
• 테스트 커버리지 > 85 % 보장  
• 동시 실행 시 JSON 경합 오류 제거  
• CLI 확장(새 명령) 시 elif 수정 0 줄 → 데코레이터만 추가  
• 유지보수 인력 onboarding 시간 단축 (복잡도 5→3단계)  

이상입니다.
