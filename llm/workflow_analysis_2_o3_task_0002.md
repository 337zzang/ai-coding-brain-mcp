# 워크플로우 분석 2

워크플로우 V2 → V3 리팩토링 종합 로드맵
=============================================================
(아직 작성되지 않은 모듈 ‑ 예: “workflow/v3/manager.py” -을 전제로 한 설계안입니다)

1) 프로젝트별 독립적 워크플로우 구현 방안
-------------------------------------------------------------
• 저장 위치  
  – ~/.ai-coding-brain/projects/<project-slug>/workflow.json  
  – 프로젝트 루트에도 심볼릭 링크 (.workflow → 위 실제 파일)만 남겨 과거 경로 호환

• 식별 방법  
  – GlobalContextManager.current_project 를 ​싱글톤으로 저장  
  – flow_project_with_workflow(…) 호출 → current_project 갱신 → WorkflowManager.switch(project_path)  

• 동시 세션  
  – manager 객체를 프로젝트별로 1개씩 캐싱(WeakValueDictionary)  
  – get_manager(path=.) → 이미 있으면 반환, 없으면 load  
  – CLI / helper 모듈은 항상 “현재 작업 디렉터리”로부터 manager 조회

• 데이터 포맷 (v3)  
  {  
    "v": "3.0",  
    "project": "name",  
    "state": "R|P|D|X",  
    "started_at": ISO,  
    "finished_at": null,  
    "tasks": [{"id":1,"name":"…","tags":["AI"],"done":false,"skip":false,"created":ISO,"finished":null}],  
    "history": { "files":[…], "git":[…] },  
    "meta": {…}  
  }  

• 자동 감지  
  – 파일 생성/저장 hook, git commit hook → manager.track_event(type, payload)  
  – 워크플로우가 없으면 silent no-op

• 검색, 리포트, 치환  
  – manager.query(keyword) → task / file / commit 검색  
  – report() → markdown, JSON 둘 다 지원


2) 삭제(폐기) 대상 파일·함수
-------------------------------------------------------------
• python/session_workflow.py (전량)  
• python/workflow_wrapper.py 중  
  – WorkflowHelpers, hook_file_creation, hook_git_commit, wt/ws/wd …  
  – !! “wf” 심볼은 유지하되 manager 호출 방식으로 교체

• workflow/__init__.py 내부의 init(), wf(), check_v2_files() 등 v2 전용 헬퍼

• flow_project_wrapper.py 안의 wf("/start …") 직접 호출 부분

• memory/workflow.json, workflow_history.json (런타임에서 v3 형태로 마이그레이션 후 삭제)


3) 통합해야 할 중복 기능
-------------------------------------------------------------
1. 태스크 CRUD  
   – session_workflow.WorkSession.add_task / workflow.integration.task  
   – 단일 API : WorkflowManager.task_add …  
2. 상태 출력  
   – session_workflow.list_tasks / workflow.integration.status / report  
   – `manager.report(view="compact|full")` 로 통합  
3. 프로젝트 전환 시 컨텍스트 저장  
   – flow_project_wrapper + GlobalContextManager 중복 로직  
   – GlobalContextManager.save_project_context() 에서 project-switch hook 만 호출  
4. 파일/커밋 자동 추적  
   – workflow_wrapper 의 hook* 함수 들과 manager 내부 track_event 를 합침  
5. 명령어 파서  
   – workflow.integration.workflow_integrated 와 session_workflow 명령 파트  
   – workflow/v3/cli.py 로 단일화 (argparse + chat-friendly free-text 파서)


4) WorkflowManager 클래스 상세 설계
-------------------------------------------------------------
class WorkflowManager:  
    # ────────── 핵심 속성 ──────────  
    project_name: str  
    project_path: Path  
    _state: dict           # in-memory JSON  
    _file: Path            # 실제 저장 파일  
    _lock: FileLock        # 멀티 프로세스 보호  

    # ────────── 생성·로드 ──────────  
    @classmethod  
    def load(cls, project_path: Path) -> "WorkflowManager"  
    @classmethod  
    def switch(cls, project_path: Path) -> "WorkflowManager"    # 내부 캐시 활용  

    # ────────── 태스크 API ──────────  
    def task_add(self, name:str, tags:List[str]=[]) -> str  
    def task_start(self, task_id:int=None) -> str             # 다음 미완료 태스크  
    def task_done(self, task_id:int=None, summary:str="") -> str  
    def task_skip(self, task_id:int, reason:str="") -> str  
    def task_delete(self, task_id:int) -> str  

    # ────────── 상태 / 리포트 ──────────  
    def status(self) -> Dict   
    def report(self, view="md") -> str  
    def progress(self) -> Tuple[int,int,float]  

    # ────────── 이벤트 트래킹 ──────────  
    def track_event(self, kind:str, payload:Dict) -> None     # file_created, git_commit …  

    # ────────── 유지보수 ──────────  
    def archive(self) -> None                                 # 완료/취소시 자동 호출  
    def migrate_v2(self, legacy_path:Path) -> None            # 최초 load 시 감지  
    def reset(self, hard=False) -> None  

    # ────────── 내부 유틸 ──────────  
    def _save(self) -> None  
    def _load(self) -> None  
    def _broadcast(self, event:str, data:Dict) -> None        # 외부 hook (예: MCP) 호출


5) 마이그레이션 순서 · 단계별 계획
-------------------------------------------------------------
Step 0 (준비)  
  • 현재 master 브랜치 동결, 리팩토링 브랜치(feature/workflow-v3) 생성  
  • 기존 메인 함수 호출 경로 파악(grep -R "task(" 등)

Step 1 (코어 작성)  
  • workflow/v3/manager.py, task.py(dataclass), cli.py 생성  
  • 파일 포맷 v3 스키마 정의 및 unit‐test 작성  

Step 2 (어댑터 레이어)  
  • workflow/__init__.py 의 task/start/done… → 내부적으로 v3 manager 호출  
  • workflow_wrapper.wf → v3 CLI 파서 사용  
  • session_workflow.WorkSession → deprecate 데코레이터 추가 + 내부에서 manager.migrate_v2() 호출

Step 3 (프로젝트 전환 통합)  
  • flow_project_wrapper → 프로젝트 이동 완료 후 WorkflowManager.switch(os.getcwd()) 호출

Step 4 (후크 통합)  
  • common.file_ops.create_file, git.commit 등에 manager.track_event 연결  
  • Hook 구현이 어려우면 먼저 “수동 호출 함수(track_file, track_commit)” 만 두고 기존 hook_* 함수 제거

Step 5 (데이터 마이그레이션)  
  • 첫 load 시 memory/workflow.json 존재 → manager.migrate_v2() 실행 → v3 파일 저장 → 기존 파일 *.bak 로 이동  
  • workflow_history.json → history[].json 병합 후 삭제  

Step 6 (문서·헬퍼 정리)  
  • README, docs/workflow.md 업데이트  
  • helpers/ 경로에 “wt/ws/wd” 대신 “wf” 단일 심볼만 유지  
  • Deprecated 경고(logging.warning) 삽입

Step 7 (정리 & 제거)  
  • 불필요 파일/함수 최종 삭제, isort/black 적용, CI 통과 확인  
  • feature/workflow-v3 → master 병합  

Step 8 (배포 이후)  
  • 2주 동안 v2→v3 자동 마이그레이션 로그 수집  
  • 문제 없으면 v2 호환 코드 완전 제거(major 버전 업)

이상입니다.