# 워크플로우 시스템 리팩토링 최종 계획 (o3 분석)

## 분석 정보
- 분석 일시: 2025-07-20 01:00
- 추론 노력: high
- 분석 시간: 104.5초

---

🔧 리팩토링 로드맵 – “프로젝트-Aware Workflow v2.1”  
(소요: 3~4 h / 변경 LOC ≒ 150-180)

────────────────────────────────────────────────
1. 아키텍처 개정 개요
────────────────────────────────────────────────
A. “프로젝트 단위 Local DB + 전역 인덱스”  
   • 각 프로젝트 ➜ memory/projects/<project>/workflow.json  
   • 전역 ➜ memory/global/index.json (메타)  
           memory/global/history.json (모든 이벤트 스트림)

B. 싱글톤 대신 “Hub”  
   WorkflowHub (= 현재 project manager + 캐시된 managers)  
   ‣ 현재 프로젝트 변경 시에도 모든 manager 객체·파일 유지 → 연속성 확보

C. 컨텍스트 파이프라인  
   ① 프로젝트 전환 직전에 Hub가 현재 워크플로우를 save()  
   ② Hub가 global_history.json에 ‘project_switched’ event append  
   ③ LLM 프롬프트 구성 시 Hub.summary()를 호출 →  
      – 현재 프로젝트 최근 N개 task/event  
      – 다른 프로젝트 요약(최근 완료 태스크 & 중요 메타)  
      => 모든 프로젝트의 압축 컨텍스트를 AI가 동시에 참조

────────────────────────────────────────────────
2. 디렉터리 구조 & 전역 메타
────────────────────────────────────────────────
memory/
 ├─ global/
 │   ├─ index.json          # {"projects": {<name>: {"created":..,"updated":..}}}
 │   └─ history.json        # append-only event log (project + event)
 └─ projects/
     └─ <project_name>/
         └─ workflow.json   # 개별 WorkflowV2 dump

────────────────────────────────────────────────
3. 코드 수정 핵심
────────────────────────────────────────────────

3-1. workflow/manager.py (v2.1 변경 부분)
-----------------------------------------
class WorkflowV2Manager:
    GLOBAL_DIR = Path("memory/global")
    PROJECTS_DIR = Path("memory/projects")

    def __init__(self, project_name: str):
        self.project_name = project_name or "default"
        self.project_dir  = self.PROJECTS_DIR / self.project_name
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.workflow_path = self.project_dir / "workflow.json"
        self.workflow      = self._load_or_create()
        self._touch_global_index()               # ⭐️추가

    # ---------- new: 전역 인덱스 & 히스토리 ----------
    def _touch_global_index(self):
        self.GLOBAL_DIR.mkdir(parents=True, exist_ok=True)
        idx = self.GLOBAL_DIR / "index.json"
        data = {"projects": {}} if not idx.exists() else json.load(idx.open())
        proj = data["projects"].setdefault(self.project_name, {})
        proj["created"]  = proj.get("created")  or self.workflow.created_at
        proj["updated"]  = datetime.now().isoformat()
        idx.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def _log_global_event(self, event_dict: dict):
        hist = self.GLOBAL_DIR / "history.json"
        with hist.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event_dict, ensure_ascii=False) + "\n")

    # save() 확장
    def save(self):
        self.workflow.updated_at = datetime.now().isoformat()
        json.dump(self.workflow.to_dict(), self.workflow_path.open("w", encoding="utf-8"),
                  indent=2, ensure_ascii=False)
        self._touch_global_index()

3-2. workflow/hub.py (신규)
-----------------------------------------
from .manager import WorkflowV2Manager

class WorkflowHub:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._managers = {}
            cls._instance.current_project = None
        return cls._instance

    def switch(self, project: str):
        # 1) 기존 매니저 저장
        if self.current_project:
            self._managers[self.current_project].save()
            self._log_switch(self.current_project, project)
        # 2) 신규 또는 캐시 manager 반환
        mgr = self._managers.get(project) or WorkflowV2Manager(project)
        self._managers[project] = mgr
        self.current_project = project
        return mgr

    def manager(self) -> WorkflowV2Manager:
        assert self.current_project, "프로젝트가 설정되지 않았습니다"
        return self._managers[self.current_project]

    # -------- LLM 컨텍스트 전용 요약 --------
    def summary(self, each=3) -> str:
        lines = []
        for p, mgr in self._managers.items():
            tasks = sorted(mgr.workflow.tasks, key=lambda t: t.id)[-each:]
            tag = "🔥" if p == self.current_project else "📂"
            lines.append(f"{tag} {p}:")
            for t in tasks:
                lines.append(f"  • #{t.id} {t.name} [{t.status.value}]")
        return "\n".join(lines)

    def _log_switch(self, from_p, to_p):
        ev = {
            "id": str(uuid.uuid4()),
            "type": "project_switched",
            "timestamp": datetime.now().isoformat(),
            "data": {"from": from_p, "to": to_p}
        }
        self._managers[from_p]._log_global_event(ev)

hub = WorkflowHub()    # 싱글톤

3-3. helper.py 수정
-----------------------------------------
def init_workflow_v2(project_name: str):
    from .hub import hub
    return hub.switch(project_name)

def get_manager():
    from .hub import hub
    return hub.manager()

⚠️ 이렇게 바꾸면 /workflow_v2 명령은 그대로이지만 내부적으로 Hub를 통해 다중 프로젝트를 관리한다.

3-4. flow_project_wrapper.py 수정 (통합)
-----------------------------------------
from workflow.helper import init_workflow_v2
# ...
init_workflow_v2(project_name)      # 프로젝트 폴더 전환 직후 호출
print("✅ 워크플로우 컨텍스트 로드 완료")

3-5. Global 히스토리 검색
-----------------------------------------
WorkflowV2Manager.search_tasks() 에 project="*" 매개변수 추가  
→ Hub가 모든 manager 순회하여 cross-project 검색 구현

────────────────────────────────────────────────
4. 프로젝트 간 컨텍스트 연속성 확보 메커니즘
────────────────────────────────────────────────
1) 저장 위치 분리  
   – 전환해도 기존 파일 그대로 → 데이터 불변

2) Hub 캐시  
   – A → B 전환 시도 :  
     A manager.save() ▶ 파일 & 인덱스 & 전역 history 기록  
     Hub.current_project = B  
     B manager 로드 (또는 캐시)  

3) 전역 history + index  
   – LLM이 ‘전체 이벤트 스트림’을 원할 때 history.json 스트림 전달 가능  
   – index.json 로부터 프로젝트 개수를 빠르게 조회

4) prompt helper  
   – cli /ctx 명령 추가 예:  
     `wf("ctx")` ➜ hub.summary() 문자열 반환 → AI 시스템 프롬프트에 삽입

────────────────────────────────────────────────
5. 마이그레이션 스크립트 (1회 실행)
────────────────────────────────────────────────
python scripts/migrate_workflow_v20_to_v21.py
------------------------------------------------
from pathlib import Path, shutil, json
src = Path("memory/workflow.json")
if src.exists():
    data = json.load(src.open())
    proj = data.get("project", "default")
    dst = Path(f"memory/projects/{proj}/workflow.json")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(src, dst)
    print(f"✅ migrated to {dst}")

────────────────────────────────────────────────
6. 검증 시나리오
────────────────────────────────────────────────
[1] A 프로젝트에서 태스크 2개 생성 ➜ wf("task list")  
[2] flow_project_with_workflow("B") 호출, B에서 태스크 1개 생성  
[3] 다시 A로 전환 → A의 태스크 그대로 확인  
[4] wf("ctx") 결과에 A, B 모두 나타나는지 확인  
[5] memory/global/history.json 열어 project_switched event 2개 존재 확인

────────────────────────────────────────────────
7. 향후 개선 포인트
────────────────────────────────────────────────
• history.json → SQLite 도입 시 탐색/쿼리 비용 감소  
• events 압축 요약 주기 실행 (30일 단위)  
• Git commit hook → manager.add_artifact(type="commit") 자동화

이상으로 프로젝트 전환 시에도 완전한 히스토리와 컨텍스트를 유지하면서 기존 WorkflowV2Manager를 적극 활용하는 통합 리팩토링 계획을 제시했습니다.
