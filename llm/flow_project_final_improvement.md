# flow_project 시스템 종합 분석 및 개선안 (o3)

## 분석 메타데이터
- 추론 노력: high
- 사고 시간: N/A초
- 분석 일시: 2025-07-20 00:45:35

---

────────────────────────────────────────────────────
1. 현재 구조 요약
────────────────────────────────────────────────────
• 프로젝트 위치
  - “Desktop/바탕화면” 하위 폴더에 모든 프로젝트가 모여 있음.
• 전환 로직
  - flow_project(name) → 바탕화면에 <name> 폴더 존재 확인 → os.chdir(project_path)
  - 캐시(~/.ai-coding-brain/cache/current_project.json)에 전환 정보 기록
  - workflow_wrapper.wf("/start <name>") 호출(실패 무시)
• 상태(컨텍스트)
  - 캐시 파일 1개만 사용 → 마지막에 열린 프로젝트만 기억
  - 프로젝트별 메모리(세션)·가상환경·워크플로우는 사실상 분리되지 않음.

────────────────────────────────────────────────────
2. 핵심 분석
────────────────────────────────────────────────────
(1) “바탕화면 기반” 장 • 단점
  장점
    • 사용자에게 가장 직관적인 위치(탐색기에서 바로 확인 가능)
    • 별도의 설정 없이 동작(설치 편리)
  단점
    • 프로젝트 수가 많아지면 바탕화면이 난잡
    • OS/OneDrive 동기화, 폴더 이름(“Desktop/바탕 화면”) 편차로 오류 가능
    • 터미널에서 작업할 때 ‘Desktop’이 루트가 아닌 경우 상대 경로 감퇴
    • CI/CD, 원격 서버, WSL 등 “바탕화면”이 없는 환경에서 작동 불가

(2) os.chdir 기반 경로 변환
  의미
    • 기존 스크립트들이 “상대 경로”만 사용해도 정상 동작하게 만듦.
  문제점
    • 전역 상태이므로 스레드/비동기/다중 세션에서 충돌 가능
    • Python REPL · Jupyter 등에서 디렉터리 뒤바뀜에 따른 예기치 않은 부작용
    • IDE, LSP(Language Server) 캐시가 꼬일 수 있음
    • 실패 중첩(예: 예외 후 cwd 미복원) 시 위험

(3) “메모리 폴더(=캐시)” 역할
  • 현재는 단순히 “마지막 프로젝트”와 전환 시각을 기록하는 수준
  • 장점: 구현이 단순, 복원 로직도 단순
  • 단점:
      – 프로젝트별 독립 정보(가상환경, 작업 히스토리, 임시 산출물 등)를 보존하지 못함
      – 멀티 세션/멀티 터미널 사용 시 충돌

(4) 워크플로우/컨텍스트 관리 현황
  • flow_project → workflow_wrapper 1방향 호출뿐
  • 실패 시 error swallow
  • 프로젝트 자체의 “컨텍스트(환경·상태·세션 변수)”가 워크플로우와 분리

────────────────────────────────────────────────────
3. 개선 목표 재정리
────────────────────────────────────────────────────
A. 상대 경로 기반 작업(=os.chdir 장점) 유지  
B. 프로젝트별 완전 분리(가상환경, 툴체인, 캐시)  
C. 컨텍스트 자동 저장/복원(IDE · 에디터 · 워크플로우 모두)  
D. 진행 상황 가시화(UI/CLI/로그)  
E. 기존 바탕화면 구조와 호환성

────────────────────────────────────────────────────
4. 제안 아키텍처
────────────────────────────────────────────────────
                 ┌────────────────────────────────┐
                 │  ~/.flow_project/              │
                 │  ├─ config.toml               │
                 │  ├─ registry.json             │  <-- 모든 프로젝트 메타
                 │  └─ sessions/                 │
                 │       └─ <pid>.json           │  <-- 터미널 단위 세션
                 └────────────────────────────────┘
                        ▲                 ▲
                        │                 │
      (A) Switch CLI ───┘                 │ (B) 자동
                                          │     컨텍스트 저장
                        ▼                 ▼
          ┌───────────────────────────────┐
          │   프로젝트 루트(다양)         │
          │   ├─ .flow/                   │  <-- per-project state
          │   │     ├─ env.yml            │  <-- 가상환경 스냅샷
          │   │     ├─ context.json       │  <-- 워크플로우·IDE 상태
          │   │     └─ history.log        │
          │   └─ source files …           │
          └───────────────────────────────┘

핵심 아이디어
• “프로젝트 레지스트리” (registry.json)  
  – 프로젝트 이름, 절대경로, 타입, git 여부, 가상환경 경로 등을 관리  
  – 최초 실행 시 바탕화면을 훑어 자동 등록 → 이후 수동/자동 추가 가능

• “.flow” 폴더 (프로젝트 내부)  
  – 각종 상태·설정 저장(가상환경, 워크플로우, 사용자 메모)  
  – git ignore 권장 → 필요에 따라 commit

• “세션(session)” 레이어  
  – 터미널/프로세스마다 독립적으로 cwd, PYTHONPATH, 활성 venv, LSP socket 등 관리  
  – 세션 종료 시 .flow/context.json에 머지

• 환경 전환 방법
  ① flow switch <name> 실행  
  ② registry에서 경로·환경 확인 → venv activate → os.chdir  
  ③ .flow/context.json 로드 → workflow_wrapper.wf(restore …)  
  ④ 세션 파일(~/.flow_project/sessions/<pid>.json)에 현재 상태 기록  
  ⑤ 사용자 작업  
  ⑥ 종료 시(flow exit, Ctrl-D hook) 세션 상태 .flow 하위로 저장

────────────────────────────────────────────────────
5. 구체적인 구현 단계
────────────────────────────────────────────────────
Step 1. 프로젝트 Root 설정 방안
  • 우선순위 탐색
    1) 환경변수 FLOW_PROJECT_ROOT
    2) ~/.flow_project/config.toml 의 root 필드
    3) 기존 데스크톱 경로(호환)
  • 코드 스니펫
    ```
    def resolve_root():
        env = os.getenv("FLOW_PROJECT_ROOT")
        if env and Path(env).is_dir(): return Path(env)
        cfg = tomli.load(Path.home()/".flow_project"/"config.toml")
        if "root" in cfg and Path(cfg["root"]).is_dir():
            return Path(cfg["root"])
        return detect_desktop()  # 기존 로직 재사용
    ```

Step 2. Registry 구축
  • registry.json 스키마
    {
      "projects": {
        "<name>": {
          "path": "...",
          "type": "python|node|...",
          "created": "2024-06-05T12:00:00",
          "venv": "~/venvs/<name>",
          "git": true
        }
      }
    }
  • 최초 실행 시 “root” 아래 모든 1depth 디렉터리를 스캔해 등록.
  • flow list, flow add, flow remove 명령 제공.

Step 3. os.chdir 안전화 (Context manager)
  • glob-style 전역 변경은 유지하되 ‘with’ 구문으로 감싸어 복원 가능
    ```
    @contextmanager
    def project_cwd(path):
        prev = Path.cwd()
        os.chdir(path)
        try:
            yield
        finally:
            os.chdir(prev)
    ```
  • flow_project(name) 내부에서:
    - 세션 저장 필요 시 prev_dir 값 활용
    - 외부 API에서 `flow_project(..., permanent=True)` 옵션 지원

Step 4. 가상환경 자동 생성/활성
  • python-type 프로젝트 → ~/.venvs/<name> 에 virtualenv 생성
  • node-type -> nvm use / npm ci
  • activation 방식
    - Windows: Scripts\activate.bat
    - Unix: . bin/activate
  • CLI 호출 프로세스가 Shell( bash/zsh/PowerShell )인 경우,
    - `eval "$(flow activate <name>)"` 패턴 제공

Step 5. 컨텍스트 자동 저장/복원
  • .flow/context.json 예시
    {
      "open_files": ["src/app.py", "README.md"],
      "cursor": {"src/app.py": 120},
      "tasks": [
        {"id": 3, "desc": "fix bug", "status": "in-progress"}
      ],
      "workflow": {"state": "..."}
    }
  • 플러그인(IDE·workflow_wrapper·CLI)에서 필요한 정보만 머지/읽기
  • 변경 감지는 watchdog(FileSystemEvent) 사용 → 실시간 flush

Step 6. 진행 상황 가시화
  • flow status  (CLI)
       - 현재 프로젝트·분기·가상환경·최근 commit, open_tasks 수 등 표시
  • 탁상 UI(optional): TUI(curses) 또는 system tray
  • 세션이 바뀔 때마다 registry에 heartbeat(ISO datetime) 기록
  • Git hook(pre-commit, post-commit) 이용: commit 메시지에 task id 참고

Step 7. backwards compatibility
  • flow_project_wrapper.fp  → 내부적으로 resolve_root() 호출
  • 바탕화면 내 프로젝트도 그대로 작동
  • 캐시(current_project.json) 계속 유지하되, 외부 도구가 없으면 “fallback 모드”만 사용

────────────────────────────────────────────────────
6. 코드 변경 예시 (중요 부분만 발췌)
────────────────────────────────────────────────────
from pathlib import Path
import json, os, sys, contextlib, subprocess, tomli, datetime as dt

CONFIG_DIR   = Path.home()/".flow_project"
REGISTRY_F   = CONFIG_DIR/"registry.json"
SESSION_DIR  = CONFIG_DIR/"sessions"

def load_registry():
    if not REGISTRY_F.exists():
        return {"projects":{}}
    return json.loads(REGISTRY_F.read_text())

def save_registry(reg):
    CONFIG_DIR.mkdir(exist_ok=True)
    REGISTRY_F.write_text(json.dumps(reg,indent=2,ensure_ascii=False))

def switch(name:str):
    reg = load_registry()
    if name not in reg["projects"]:
        raise RuntimeError(f"프로젝트 미등록: {name}")
    info = reg["projects"][name]
    path = Path(info["path"])
    if not path.exists():
        raise FileNotFoundError(path)
    # activate venv
    if info["type"]=="python":
        os.environ["VIRTUAL_ENV"]=str(Path(info["venv"]))
        sys.path.insert(0,str(path))
    # session file
    sess_f = SESSION_DIR/f"{os.getpid()}.json"
    with open(sess_f,'w',encoding='utf-8') as f:
        json.dump({"project":name,"entered":dt.datetime.now().isoformat()},f)
    # chdir
    os.chdir(path)
    # workflow restore
    try: from workflow_wrapper import wf
    except ImportError: pass
    else: wf(f"/restore {name}") 

def cli():
    import argparse, textwrap
    ap = argparse.ArgumentParser(prog="flow")
    sub=ap.add_subparsers(dest="cmd")
    sub.add_parser("list")
    sw=sub.add_parser("switch"); sw.add_argument("name")
    # ...
    args=ap.parse_args()
    if args.cmd=="list":
        for n in load_registry()["projects"]: print(n)
    elif args.cmd=="switch": switch(args.name)
if __name__=="__main__": cli()

────────────────────────────────────────────────────
7. 기대 효과
────────────────────────────────────────────────────
• 데스크톱 의존 탈피: 환경변수/설정파일 도입 ➔ 서버·WSL·CI에서도 동일 경험  
• 글로벌 cwd 변경 부작용 ↓ : Context manager + Session 파일로 안전 운용  
• 프로젝트별 완전 독립: .flow + 가상환경 자동 관리  
• 작업 재개 속도 ↑ : 컨텍스트(id, 열어둔 파일, cursor) 자동 복원  
• 진행률 가시화: flow status, heartbeat 파일로 실시간 체크  
• 점진적 도입: 기존 flow_project_wrapper.py 100% 호환, 새 기능은 opt-in  

────────────────────────────────────────────────────
8. 우선순위 로드맵
────────────────────────────────────────────────────
1) v0.1 (1주)  : ROOT 결정 로직 + registry 구축 + flow list/switch  
2) v0.2 (2주)  : 가상환경 자동화, Session 파일, flow status  
3) v0.3 (4주)  : .flow/context.json 통합, workflow restore 지원  
4) v0.4 (6주)  : IDE 플러그인 연동, watchdog 실시간 flush  
5) v1.0 (8주)  : TUI/Tray UI, 다중 사용자·멀티 머신 동기화(Cloud/SSH)  

────────────────────────────────────────────────────
9. 마이그레이션 가이드
────────────────────────────────────────────────────
1. pip install flow-project==0.2  
2. export FLOW_PROJECT_ROOT=~/Desktop          # 기존 위치일 때  
3. flow scan-desktop      # 기존 폴더 자동 등록  
4. flow switch my_proj    # 이전과 동일 호출  

※ 기존 스크립트에서 ‘fp("my_proj")’ 사용 부분은 변경 불필요.

────────────────────────────────────────────────────
10. 결론
────────────────────────────────────────────────────
• “바탕화면 + os.chdir” 구조는 학습 곡선이 낮지만, 확장성·안정성이 제한적이다.  
• 제안된 Registry/Session/.flow 설계는 “상대 경로 편리함”을 유지하면서  
  다중 환경·컨텍스트·가상환경을 안전하게 분리·자동화한다.  
• 점진적 호환 전략을 통해 리스크 없이 단계적으로 도입 가능하다.
