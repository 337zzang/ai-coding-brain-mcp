# 워크플로우 분석 3

아래 내용은 “프로젝트별 완전 독립형 워크플로우 V2”를 목표로 한 제안서입니다.  
(예시는 Python으로 작성된 현재 코드 기반을 전제로 하지만, Node·Go 등 타 스택에서도 동일한 컨벤션을 유지할 수 있게 설계했습니다)

────────────────────────────────────────
1) .ai-brain 폴더 구조 최적화
────────────────────────────────────────
📁 <project-root>/  
 └─ 📁 .ai-brain/              # 모든 AI-메타데이터를 이곳에 고정  
     ├─ workflow.json          # 단일 마스터 파일(작업·히스토리·캐시 통합)  
     ├─ history/               # ‘아카이브’ 상태가 된 워크플로우 스냅샷  
     │    └─ 2024-03-20T13-00-34.json  
     ├─ cache/                 # 용량 큰 임시 데이터 (LLM 분석 결과, 벡터 등)  
     │    ├─ dir-scan.json  
     │    └─ embedding.bin  
     ├─ checkpoints/           # 메시지·상태 체크포인트(롤백용)  
     │    └─ cp_00023.json  
     ├─ logs/                  # 디버그·에러 로그  
     └─ README.md              # 폴더 설계 설명서(자동 생성)  

핵심 아이디어  
• “단일 진실 원천(workflow.json) + 목적별 세컨더리 저장소(history·cache·checkpoints)” 구조로 단순화  
• 파일/서브폴더 이름은 가급적 OS 호환 · Git Friendly(공백·한글 미사용)  
• .ai-brain 하위만 .gitignore => 코드와 데이터 분리  

────────────────────────────────────────
2) workflow.json 스키마 설계
────────────────────────────────────────
전체를 하나의 JSON에 넣되 ①런타임 상태, ②히스토리 메타, ③캐시/지표 를 명시적으로 구분합니다.

```jsonc
{
  "version": "2.1",
  /* ① 런타임 상태 (Stateless Service가 필요할 최소 데이터) */
  "session": {
    "status": "R",            // N=new, R=running, P=paused, D=done, X=cancelled
    "title": "Landing-page 리팩터링",
    "started_at": "2024-03-20T12:58:03Z",
    "current_task": 3         // id 값, null 이면 대기
  },

  /* ② 태스크 목록 */
  "tasks": [
    {"id":1,"name":"CSS reset 도입","tags":["style"],"done":true},
    {"id":2,"name":"Hero 섹션 컴포넌트화","tags":["react"],"done":true},
    {"id":3,"name":"접근성 감사","tags":["a11y"],"done":false}
  ],

  /* ③ 히스토리(요약본). 스냅샷 파일은 /history 폴더에 풀 백업 */
  "history": [
     {"at":"2024-02-01T11:22","title":"v1 배포","done":true,"tasks":14},
     {"at":"2024-02-10T09:15","title":"다국어화","done":true,"tasks":23}
  ],

  /* ④ 캐시/통계 (LLM 의사결정·UI 표시용, 삭제해도 무방) */
  "cache": {
    "dir_scan": { "total_files": 112, "scanned_at": "2024-03-20T12:00" },
    "embedding": { "vector_db": "sqlite", "updated": "2024-03-19T17:33" }
  }
}
```

설계 원칙  
• 상위 레벨 키를 `session / tasks / history / cache` 네 구역으로 고정  
• 미니멈 키 길이(축약)와 가독성의 균형 – 내부 속성은 1~2 글자로 압축 가능하지만 상위 블록은 명시적으로 둔다  
• 각 블록은 독립적으로 TTL(Time-to-Live) 정책 적용해 자동 정리 가능  

────────────────────────────────────────
3) fp() 함수와 wf() 함수의 상호작용
────────────────────────────────────────
• fp()  ⟶  “프로젝트 전환” 책임  
  1. 바탕화면 or 요청 경로에서 프로젝트 디렉토리 탐색  
  2. os.chdir() 후 .ai-brain/workflow.json 로딩 (없으면 init)  
  3. GlobalContextManager.save_project_context() 호출  
  4. 내부적으로 wf("/reload") 를 자동 호출해 워크플로우 매니저에 세션 바인딩  

• wf()  ⟶  “현재 세션 조작” 책임  
  – task / start / done / status / report 등 모든 명령은 현재 디렉토리의 .ai-brain/workflow.json 을 단일 소스 오브 트루스로 사용  
  – fp() 없이 wf() 단독 호출 시: 현재 working dir 에 .ai-brain 없으면 자동 생성하고 초기화  

구현 팁  
```python
def wf(cmd: str):
    session = WorkSession()          # 내부적으로 get_workflow_path() 사용
    return workflow_integrated(cmd, session=session)
```
・WorkSession 객체를 외부에서 주입 가능하게 해 테스트/REPL 용이  
・fp() 가 먼저 실행되어도 동일 객체를 가리키므로 레이스컨디션 없음  

────────────────────────────────────────
4) 히스토리 관리 및 캐시 전략
────────────────────────────────────────
(1) 히스토리 로테이션  
   • `session.status` 가 D(done) 또는 X(cancelled) 로 바뀌면  
     – 현재 workflow.json 을 /history/YYYY-MM-DDThh-mm-ss.json 으로 복사  
     – workflow.json → ‘history’ 배열에 summary push  
     – history 폴더는 최근 100개만 남기고 삭제(선택)  

(2) 캐시 TTL  
   • /cache 하위 모든 파일은 “마지막 사용 시각” 메타를 파일존재 또는 side-car 파일에 기록  
   • n일(예: 14일) 이상 접근 없으면 자동 삭제 – 캐시 미존재시 lazy rebuild  

(3) 체크포인트(대용량 정적)  
   • /checkpoints 는 워크플로우 진행 중 AI 대화·프롬프트 등을 full snapshot  
   • 번호·날짜 혼합 네이밍(cp_00042.json) => 정렬 용이  
   • Git 커밋 시점에 자동 청소 or 외부 S3 업로드 전략 선택 가능  

────────────────────────────────────────
5) 기존 workflow.json 마이그레이션
────────────────────────────────────────
기존 파일은 대부분 `tasks / history / usage_stats` 등 부분적으로만 존재합니다.  
마이그레이션 시나리오(한 번만 실행):

```python
def migrate_legacy_workflow(project_root="."):
    old_path = Path(project_root) / "workflow.json"
    new_dir  = Path(project_root) / ".ai-brain"
    new_dir.mkdir(exist_ok=True)
    new_path = new_dir / "workflow.json"

    if not old_path.exists() or new_path.exists():
        return "⚠️ 마이그레이션 불필요 또는 이미 완료"

    with open(old_path, encoding="utf-8") as f:
        old = json.load(f)

    # 1) session
    session = {
        "status": "R",
        "title": old.get("description") or old.get("name") or "Untitled",
        "started_at": datetime.now().isoformat(),
        "current_task": None
    }

    # 2) tasks (가능한 키 변환)
    raw_tasks = old.get("tasks") or []
    tasks = []
    for i, t in enumerate(raw_tasks, 1):
        tasks.append({
            "id": i,
            "name": t.get("name", f"task_{i}"),
            "tags": t.get("tags", []),
            "done": t.get("done", False)
        })

    # 3) history
    history = old.get("history", [])

    # 4) cache (usage_stats → cache.stats 로 이관)
    cache = {
        "stats": old.get("usage_stats", {}),
        "migrated": True,
        "migrated_at": datetime.now().isoformat()
    }

    new_data = {
        "version": "2.1",
        "session": session,
        "tasks": tasks,
        "history": history,
        "cache": cache
    }

    with open(new_path, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)

    # 백업 & 안내
    old_path.rename(old_path.with_suffix(".json.bak"))
    print(f"✅ 마이그레이션 완료 → {new_path}")
    return "migration_done"
```

• fp() 호출 시, 신규 구조가 없으면 위 migrate 함수가 **자동** 실행되도록 Hook  
• .bak 파일은 30일 후 자동 삭제(크론 or 첫 실행시 check)  

────────────────────────────────────────
요약
────────────────────────────────────────
• .ai-brain 디렉토리 한 곳에 “session + history + cache + checkpoints”를 모아 **프로젝트 완전 독립**을 달성  
• workflow.json은 4-블록(session/tasks/history/cache) 표준 스키마로 통일  
• fp() = 프로젝트 전환 핵 / wf() = 세션 액션 핵 → 서로 느슨하게 연결  
• 히스토리와 캐시는 LRU + TTL 기반 클리너로 자동 슬림화  
• 레거시 파일은 최초 전환 시 무중단 마이그레이션 → .bak 보존  

이 설계를 적용하면  
1) Git 레포지토리에 코드만 남고 AI-메타는 투명하게 격리되며  
2) 멀티 프로젝트·멀티 세션을 충돌 없이 다룰 수 있고  
3) 기존 사용자도 별다른 수작업 없이 V2로 업그레이드할 수 있습니다.