# 워크플로우 시스템 개선 방안

아래 설계‧로드맵은 “python/workflow/” 모듈을 중심으로 워크플로우 엔진을 ‘멀티-프로젝트’ 구조로 재구성하면서  
① fp 함수 복구, ② 프로젝트별 워크플로우·히스토리 관리, ③ 캐시 계층, ④ 메모리 컨텍스트(대화·작업 맥락) 유지까지 단계적으로 해결하는 방안이다.  

────────────────────────
1. 목표별 핵심 설계
────────────────────────
1-1. fp 함수 복구 + 프로젝트 전환  
 • 파일: python/helpers/flow_project_wrapper.py  
 • 아이디어: 전역 싱글톤 FlowProject 인스턴스를 포인터 fp 로 노출한다.  
   - fp( ) 호출 → 현재 활성 프로젝트의 FlowProject 객체 반환  
   - switch_project('projA') → fp 가 projA 로 바뀜  
 • 최소 API 예시  
   ```python
   from helpers.flow_project_wrapper import fp, switch_project, list_projects
   
   fp().add_task({...})
   switch_project('demo2')        # 자동 저장 후 포인터 교체
   fp().status()
   ```

1-2. 프로젝트별 workflow.json / workflow_history.json  
 • 폴더 구조 예시  
   projects/
     └─ myproj/
         ├─ workflow.json              # { "project": "myproj", "tasks": [...] }
         ├─ workflow_history.json      # event log
         └─ cache/
             ├─ memory_cache.md  
             └─ results_cache.json  
 • FlowProject.load(path) 시 위 파일들이 없으면 자동 생성(스켈레톤 템플릿 사용).  

1-3. 캐시 시스템 (JSON/Markdown)  
 • 추상 클래스 CacheStore with {get, set, exists, clear}.  
 • 구현체  
   - JSONCache(path)      → pickle 불필요, 직렬화 쉬움  
   - MarkdownCache(path)  → 요약, 대화 기록 등 human-readable 용  
 • 각 FlowProject 가 self.cache[‘memory’]·self.cache[‘results’] 식으로 보유.  

1-4. 메모리 컨텍스트 유지  
 • MemoryContext 클래스  
   - short_term: 최근 N(≒10) step 을 메모리에 유지  
   - long_term: N step 초과분은 summary(LLM/텍스트랭크) 후 MarkdownCache 로 이동  
 • retrieve( ) → 요약 + short_term 반환, LLM 프롬프트에 삽입해 토큰 절약.  
 • update(event) → short_term append → overflow? summarize() 후 flush.  

────────────────────────
2. 모듈/클래스 청사진
────────────────────────
python/helpers/flow_project_wrapper.py
```
from workflow.flow_project import FlowProject
_current = None

def fp():
    if _current is None:
        raise RuntimeError("No active project, call load_project or new_project.")
    return _current

def load_project(name, root="projects"):
    global _current
    _current = FlowProject.load(f"{root}/{name}")
    return _current

def new_project(name, template=None, root="projects"):
    global _current
    _current = FlowProject.create(f"{root}/{name}", template)
    return _current

def switch_project(name, root="projects"):
    if fp().name == name:
        return _current
    fp().save()                # 안전 저장
    return load_project(name, root)

def list_projects(root="projects"):
    return [p.name for p in Path(root).iterdir() if p.is_dir()]
```

python/workflow/flow_project.py
```
class FlowProject:
    # ---------- 생성/로드 ----------
    @classmethod
    def create(cls, path, template=None): ...
    @classmethod
    def load(cls, path): ...

    # ---------- Task CRUD ----------
    def add_task(self, task_dict): ...
    def remove_task(self, task_id): ...
    def update_task(self, task_id, **kw): ...
    def status(self): ...               # 표 형식 반환

    # ---------- I/O ----------
    def save(self): ...
    def _save_history(self, event): ...

    # ---------- 캐시 ----------
    def cache_get(self, key, default=None): ...
    def cache_set(self, key, value): ...

    # ---------- 메모리 ----------
    def memory_retrieve(self): ...
    def memory_update(self, event): ...
```

python/workflow/cache.py
```
class CacheStore(ABC):
    def __init__(self, path): ...
    def get(self, key): ...
    def set(self, key, value): ...
    ...

class JSONCache(CacheStore): ...
class MarkdownCache(CacheStore): ...
```

python/workflow/memory.py
```
class MemoryContext:
    def __init__(self, md_cache, limit=10): ...
    def update(self, entry: dict): ...
    def retrieve(self) -> str: ...
    def _summarize_and_flush(self): ...
```

────────────────────────
3. 파일 포맷 예시
────────────────────────
workflow.json  
```
{
  "project": "myproj",
  "created": "2024-04-12T08:15:20Z",
  "tasks": [
    { "id": "T001",
      "name": "데이터 수집",
      "status": "todo",          # todo|doing|done|blocked
      "deps": [],
      "meta": {"owner": "jun", "tags": ["scraping"]}
    }
  ]
}
```
workflow_history.json  
```
[
  { "ts": "2024-04-12T08:16:01Z",
    "event": "create_project",
    "user": "...",
    "detail": {}
  },
  { "ts": "...", "event": "add_task", "detail": { "task_id": "T001"} }
]
```

────────────────────────
4. 단계별 구현 우선순위
────────────────────────
Phase 0 – 코드정비 (½일)
  • 기존 python/workflow/ 디렉토리 분석, 불필요 파일 삭제, 패키지 __init__.py 추가  
  • pytest 셋업, black/ruff 적용  

Phase 1 – FlowProject + fp 복구 (1일)
  1. flow_project.py 에서 create/load/save 구현, 기본 CRUD 포함  
  2. wrapper(fp) 로 전역 접근, switch_project 지원  
  3. 단위 테스트: 새 프로젝트 생성·전환·저장 시나리오  

Phase 2 – workflow.json: tasks 배열 & 히스토리 (1일)
  1. 스키마(위 예시) 정의, jsonschema 로 검증  
  2. _save_history(event) 로 이벤트 자동 기록  
  3. test: add/remove/update 시 history 로그 길이 증가 검증  

Phase 3 – 캐시 계층 (0.5일)
  1. CacheStore/JSONCache/MarkdownCache 작성  
  2. FlowProject 내부 cache 멤버 주입 → cache/ 디렉토리 자동 생성  
  3. test: set→get, 파일 존재, 명세 일치 여부  

Phase 4 – MemoryContext (1일)
  1. memory.py 구현, summarizer: 간단히 nltk + textrank → 후속 LLM 대체 가능  
  2. FlowProject.memory_update/ retrieve 와 연동  
  3. stress test: 100 이벤트 투입 → short_term 길이 유지, md 로 장기 요약 저장  

Phase 5 – CLI/Notebook 헬퍼 (Optional 0.5일)
  • poetry script `flowctl` 추가: new, switch, ls, add-task, status 등  

────────────────────────
5. 추가 고려 사항
────────────────────────
• 동시성: 여러 프로세스가 같은 workflow.json 을 수정할 수 있으므로  
  - 파일 락(fcntl/portalocker) 혹은 git 방식의 optimistic lock 권장.  

• 백업 전략: save() 시 기존 파일을 timestamp.bak 으로 회전.  

• 사양 확장성:  
  - future: task 실행엔진, 의존성 그래프 DAG 시각화, REST API 래핑.  
  - plugin 폴더/hooks 로 after_add_task, before_save 같은 이벤트 훅 지원 가능.  

• 테스트 커버리지 목표 80%+, CI: GitHub Actions.  

────────────────────────
6. 기대 효과
────────────────────────
1) fp 복구 + 프로젝트 전환으로 사용자 API 통일.  
2) tasks 배열 및 히스토리 분리로 구조 명확, 롤백·감사 가능.  
3) 캐시 계층으로 대규모 결과·컨텍스트 영속화, 속도·토큰 비용 절감.  
4) MemoryContext 덕분에 LLM 사용 시 긴 작업도 맥락 유지/요약 자동화.  
5) 단계별 구현으로 매일 배포 가능한 인크리멘탈 개발·테스트 사이클 보장.