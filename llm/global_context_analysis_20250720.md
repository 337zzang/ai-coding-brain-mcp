아래 제안은  

• “바탕 화면의 프로젝트 디렉터리” ↔ “~/.ai-coding-brain 의 글로벌 컨텍스트” ↔ “현재 세션의 WorkflowV2Manager”  

세 축을 끊김 없이 연결한다는 관점으로 설계되어 있습니다.  
(코드-조각은 이해를 돕기 위한 skeleton 이며 그대로 copy & paste 가 가능하도록 최소한의 의존성만 포함했습니다)

────────────────────────────────────────
Ⅰ. GlobalContextManager 설계
────────────────────────────────────────
파일: python/workflow/global_context.py

역할
1. 프로젝트 간 전환 시 워크플로우 스냅샷과 메타데이터를 디스크(~/.ai-coding-brain/)에 영속화
2. 마지막에 열려 있던 프로젝트 및 최근 사용 히스토리 관리
3. 세션이 시작될 때 자동으로 가장 최근 프로젝트의 컨텍스트를 로드
4. CLI/REPL 에서 gc(), project_history(), gc_search() 와 같은 헬퍼 명령을 제공

데이터 구조 ( ~/.ai-coding-brain/global_context.json )

{
  "version": "1.0",
  "current_project": "my_app",
  "history": ["my_lib", "my_app"],
  "projects": {
    "my_app": {
      "path": "/Users/…/Desktop/my_app",
      "last_opened": "2024-03-29T09:12:16",
      "workflow_snapshot": {...  # WorkflowV2Manager.to_dict() 결과},
      "metadata": {
        "notes": "...",          # 필요 시 확장
        "custom": {...}
      }
    },
    ...
  }
}

핵심 API
class GlobalContextManager
  ── __init__(base_dir: Path = ~/.ai-coding-brain)
  ── load() / save()                    # json 직렬화
  ── get_current_project() -> str|None
  ── set_current_project(name:str, path:Path)
  ── capture_workflow(manager:WorkflowV2Manager)
  ── restore_workflow(project:str) -> WorkflowV2Manager
  ── push_history(project:str)
  ── get_history(limit:int=10) -> List[str]
  ── search_tasks(query:str) -> List[Task]  # 모든 프로젝트를 가로질러 검색
싱글톤 getter:  get_gc()

────────────────────────────────────────
Ⅱ. 코드 스켈레톤
────────────────────────────────────────
# python/workflow/global_context.py
from pathlib import Path
import json, os
from datetime import datetime
from typing import Dict, Any, Optional, List
from .manager import WorkflowV2Manager, WorkflowV2   # 기존 코드 재사용

class GlobalContextManager:
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path.home() / ".ai-coding-brain"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.ctx_file = self.base_dir / "global_context.json"
        self.data: Dict[str, Any] = {
            "version": "1.0",
            "current_project": None,
            "history": [],
            "projects": {}
        }
        self._load()

    # ---------- persistence ----------
    def _load(self):
        if self.ctx_file.exists():
            try:
                self.data.update(json.loads(self.ctx_file.read_text()))
            except Exception as e:
                print(f"⚠️ 글로벌 컨텍스트 로드 실패: {e}")

    def _save(self):
        try:
            self.ctx_file.write_text(json.dumps(self.data, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"⚠️ 글로벌 컨텍스트 저장 실패: {e}")

    # ---------- project meta ----------
    def set_current_project(self, name:str, path:Path):
        self.data["current_project"] = name
        self.push_history(name)
        proj = self.data["projects"].setdefault(name, {})
        proj["path"] = str(path)
        proj["last_opened"] = datetime.now().isoformat()
        self._save()

    def get_current_project(self) -> Optional[str]:
        return self.data.get("current_project")

    def push_history(self, name:str):
        hist: List[str] = self.data.setdefault("history", [])
        if hist and hist[-1] == name:
            return
        hist.append(name)
        # 중복 제거 + 최근 50개 유지
        self.data["history"] = list(dict.fromkeys(hist))[-50:]

    def get_history(self, limit:int=10) -> List[str]:
        return self.data.get("history", [])[-limit:]

    # ---------- workflow snapshot ----------
    def capture_workflow(self, wf: WorkflowV2Manager):
        name = wf.project_name
        proj = self.data["projects"].setdefault(name, {})
        proj["workflow_snapshot"] = wf.workflow.to_dict()
        self._save()

    def restore_workflow(self, name:str) -> WorkflowV2Manager:
        from .helper import init_workflow_v2   # 순환 import 문제 방지
        snapshot = self.data.get("projects", {}).get(name, {}).get("workflow_snapshot")
        manager = init_workflow_v2(project_name=name)
        if snapshot:
            manager.workflow = manager._dict_to_workflow(snapshot)
            manager.save()   # memory/workflow.json 갱신
        return manager

    # ---------- cross-project search ----------
    def search_tasks(self, query:str):
        from .schema import Task
        result=[]
        for proj,meta in self.data.get("projects", {}).items():
            wf_dict = meta.get("workflow_snapshot")
            if not wf_dict: continue
            for t in wf_dict.get("tasks", []):
                if query.lower() in t["name"].lower():
                    task = Task.from_dict(t)
                    task.project = proj        # 태스크에 프로젝트 표시 (속성 추가)
                    result.append(task)
        return result

# 싱글톤
_gc: Optional[GlobalContextManager] = None
def get_gc() -> GlobalContextManager:
    global _gc
    if _gc is None:
        _gc = GlobalContextManager()
    return _gc

# 편의 단축 함수
def gc(cmd:str=None):
    """
    예)
    gc()                  -> 현재 프로젝트/히스토리 출력
    gc('search login')    -> 모든 프로젝트 태스크 검색
    """
    gcm = get_gc()
    if cmd is None:
        print("🌐 GlobalContext")
        print("현재:", gcm.get_current_project())
        print("히스토리:", " > ".join(gcm.get_history()))
        return
    parts = cmd.split()
    if parts[0]=="search":
        q=" ".join(parts[1:])
        rs=gcm.search_tasks(q)
        if not rs:
            print("🔍 없음")
        else:
            for t in rs:
                print(f"[{t.project}] #{t.id} {t.name}")

def project_history(limit:int=10):
    print("📜 최근 프로젝트:", " > ".join(get_gc().get_history(limit)))

────────────────────────────────────────
Ⅲ. flow_project_wrapper.py 수정
────────────────────────────────────────
수정 포인트 3 곳

1) 최상단 import
from workflow.global_context import get_gc
from workflow.helper        import get_manager   # 이미 존재

2) 프로젝트 이동 직전에 “현재” 컨텍스트 스냅샷
# --- 이전 코드 일부 ---
previous_dir = os.getcwd()

# NEW ↓
try:
    gc_mgr = get_gc()
    if gc_mgr.get_current_project():
        # 현재 manager 싱글톤이 있으면 워크플로우 스냅샷 저장
        try:
            wf_mgr = get_manager()
            gc_mgr.capture_workflow(wf_mgr)
        except:
            pass
except:
    pass
# --- 기존 로직 계속 ---

3) 성공적으로 디렉터리 이동한 뒤
# after os.chdir(str(project_path)) …
gc_mgr = get_gc()
gc_mgr.set_current_project(project_name, project_path)

# Workflow 로드/초기화
from workflow.helper import init_workflow_v2
wf_mgr = gc_mgr.restore_workflow(project_name)  # 스냅샷이 있으면 복원

print(f"✅ 워크플로우도 {project_name} 로 전환됨 (tasks:{len(wf_mgr.workflow.tasks)})")

기존 논리를 건드리지 않으면서 “스냅샷 저장 → 디렉터리 이동 → 스냅샷 복원” 의 흐름만 추가했습니다.  
WorkflowV2Manager 의 내부는 전혀 수정하지 않기 때문에 완전 호환됩니다.

────────────────────────────────────────
Ⅳ. json_repl_session.py (또는 main 진입점) 수정
────────────────────────────────────────
세션이 시작될 때 최근 프로젝트 컨텍스트를 자동으로 로드

from workflow.global_context import get_gc
from workflow.helper import init_workflow_v2

def init_session():
    gc_mgr = get_gc()
    curr = gc_mgr.get_current_project()
    if curr:
        init_workflow_v2(curr)        # manager 싱글톤 생성
        gc_mgr.restore_workflow(curr) # snapshot → manager
        print(f"🌐 Global context loaded: {curr}")
    else:
        init_workflow_v2()            # default
    # (기존 초기화 로직 이어서…)

해당 초기화 함수를 json_repl_session.py 의 세션 시작 시점(예: if __name__ == '__main__': 부분) 호출하도록 연결하면 끝.

────────────────────────────────────────
Ⅴ. 편의 명령/헬퍼
────────────────────────────────────────
• gc()                         – 현재 글로벌 상태 요약  
• gc('search keyword')         – 모든 프로젝트 태스크 검색  
• project_history(n)           – 최근 n개 프로젝트 목록  
• fp('SomeProject')            – 프로젝트 전환(이미 존재) → 내부적으로 컨텍스트까지 스냅 복원  

※ 필요하면 workflow.helper.workflow_v2() 안에  
  elif cmd=="gsearch": get_gc().search_tasks(…).  
  등의 hook 을 넣어도 됨.

────────────────────────────────────────
Ⅵ. 단계별 구현 플랜
────────────────────────────────────────
Step-0  브랜치 따기 / 테스트용 데스크톱 dummy 프로젝트 2~3개 준비  
Step-1  python/workflow/global_context.py 파일 생성 – skeleton 완성 & 단위테스트  
Step-2  flow_project_wrapper.py ①,②,③ patch → 프로젝트 전환 시 saving/restore 확인  
Step-3  json_repl_session.py 에 init_session() 삽입 → REPL 재시작 후 이전 상태 자동 복원 여부 확인  
Step-4  helper 함수(gc, project_history) REPL 이나 spyder-style 스타트업 스크립트에 등록  
Step-5  cross-project search / edge-case (첫 전환, 스냅샷 없음, json 훼손) 테스트  
Step-6  README / CHANGELOG 업데이트, 버전 bump 2.1  

────────────────────────────────────────
Ⅶ. 호환성 주의사항
────────────────────────────────────────
1. WorkflowV2Manager 에 단 한 줄도 수정하지 않는다.  
   – snapshot 을 dict 로 만들고 다시 _dict_to_workflow() 로 되돌리는 방식으로만 교류  
2. path 의존성은 “프로젝트 전환 시 현재 working-dir 을 바꾼다” 라는 flow_project_wrapper 의 기존 철학을 그대로 따른다.  
   – WorkflowV2Manager 는 상대 경로 memory/workflow.json 을 바라보므로, 프로젝트 폴더로 chdir 만 해주면 별도 수정 불필요  
3. 글로벌 컨텍스트 json 저장/로딩 과정에서 예외가 발생해도 프로젝트 전환 자체는 중단되지 않도록 try/except 로 래핑  
4. 잠재적 병행 세션(두 터미널에서 동시에 실행) → mkdir 을 이용한 OS-lock 혹은 파일 타임스탬프로 충돌 감지(필요 시 추후 작업)  
5. 버전 필드를 두어 스키마 변경 시 마이그레이션 경로를 확보(“version”:”1.x”)  

────────────────────────────────────────
Ⅷ. 마무리
────────────────────────────────────────
위 구조를 적용하면  

• “데스크톱 프로젝트 폴더”는 그대로 보존되면서  
• 프로젝트를 전환할 때마다 Workflow 의 스냅샷이 ~/.ai-coding-brain/ 에 보관  
• REPL 을 끄고 다시 켜더라도 즉시 직전 작업 맥락을 복원  
• cross-project 검색/요약이 가능  

즉, “세션을 넘어서는 기억”이라는 목표를 최소 침투적(기존 코드 변경 최소화)으로 달성할 수 있습니다.