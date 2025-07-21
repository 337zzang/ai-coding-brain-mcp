# o3_task_0013 분석 결과

────────────────────────────────────────
Flow Project v2 – context.json 기반
AI 세션 컨텍스트 “완전 복원” 설계·구현 가이드
────────────────────────────────────────

1. 파일 구조와 책임
─────────────────
.ai-brain/
 ├─ workflow.json   ← 장기 워크플로우(Plans·Tasks)
 ├─ context.json    ← 세션 단기 컨텍스트(=Memory)
 └─ …               ← 문서·스냅샷 등

workflow.json = 프로젝트 전역 상태  
context.json = “직전 대화”부터 이어받기 위한 세션 메모리

2. context.json 스키마
─────────────────
필수 정보만 담고, 나머지는 workflow.json·코드베이스에서 조회하도록 분리한다.

{
  "version": "1.0",
  "created_at": "2024-05-27T11:03:52Z",
  "updated_at": "2024-05-27T14:42:18Z",
  "memory": {
    "active_plan_id": "plan_001",
    "active_task_id": "task_004",
    "last_decisions": [                // 의사결정 로그(요약)
      "API 호환성 유지하기로 결정",
      " /flow 명령 패턴은 단수형 유지"
    ],
    "open_files": ["app/workflow.py", "docs/cli.md"],
    "working_directory": "/repo"
  },
  "conversation": {
    "running_summary": "…400자 이내 오토요약…",
    "recent_window": [                 // 토큰 한계 내 최근 N줄
      {"role": "user",      "content": "...", "ts": "2024-05-27T14:23:00Z"},
      {"role": "assistant", "content": "...", "ts": "…"}
    ],
    "vector_cache": [                  // 선택 (RAG)
      {"id": "msg_034", "embedding": [0.21, …]}
    ]
  },
  "stats": {
    "dialog_turns": 34,
    "total_tokens": 8920
  }
}

3. 핵심 알고리즘
─────────────────
A. ContextManager 클래스(새로 추가)
-----------------------------------
class ContextManager:
    PATH = ".ai-brain/context.json"
    TOKEN_LIMIT = 4096
    WINDOW_KEEP = 800           # ‘최근 대화’ 토큰 예산
    SUMMARY_MAXLEN = 400        # chars

    def __init__(self):
        self.data = self._load()

    # ---------- I/O ----------
    def _load(self):
        if not Path(self.PATH).exists():
            return self._bootstrap()
        return json.load(open(self.PATH))

    def save(self):
        self.data["updated_at"] = iso_now()
        json.dump(self.data, open(self.PATH, "w"), indent=2)

    # ---------- API ----------
    def register_message(self, role, content):
        msg = {"role": role, "content": content, "ts": iso_now()}
        self.data["conversation"]["recent_window"].append(msg)
        self._trim_window()
        self._update_summary(content, role)
        self.save()

    def hydrate_prompt(self) -> list[str]:
        """
        새 LLM 세션이 시작될 때 호출.
        반환: system-prompt용 문자열 리스트
        """
        meta   = self.data["memory"]
        conv   = self.data["conversation"]
        wf     = WorkflowManager.load()  # workflow.json

        return [
            f"PROJECT: {wf.project_name}",
            f"ACTIVE PLAN: {wf.plan(meta['active_plan_id']).title}",
            f"ACTIVE TASK: {wf.task(meta['active_task_id']).title}",
            f"DECISIONS: {', '.join(meta['last_decisions'])}",
            f"SUMMARY: {conv['running_summary']}",
            "RECENT DIALOG:",
            *[f\"{m['role'].upper()}: {m['content']}\" for m in conv['recent_window']]
        ]

    # ---------- 내부 ----------
    def _trim_window(self):
        """토큰 수가 WINDOW_KEEP 초과 시 앞쪽부터 pop 및 summary 갱신."""
        if num_tokens(self.data["conversation"]["recent_window"]) <= self.WINDOW_KEEP:
            return
        # 과거 메시지를 summary에 합치고 window에서 제거
        removed = self.data["conversation"]["recent_window"][:-1 * self.WINDOW_KEEP]
        summary_add = summarizer(removed)
        self.data["conversation"]["running_summary"] = merge_summary(
            self.data["conversation"]["running_summary"], summary_add,
            maxlen=self.SUMMARY_MAXLEN
        )
        self.data["conversation"]["recent_window"] = \
            self.data["conversation"]["recent_window"][-1 * self.WINDOW_KEEP:]

    def _update_summary(self, content, role):
        """assistant 메시지는 reasoning을 포함하므로 summary 업데이트 강도 ↑."""
        if role == "assistant":
            add = summarizer([{"role": role, "content": content}])
            self.data["conversation"]["running_summary"] = merge_summary(
                self.data["conversation"]["running_summary"], add,
                maxlen=self.SUMMARY_MAXLEN
            )

B. WorkflowManager ↔ ContextManager 연동 지점
------------------------------------------
• LLM 응답 직후: ContextManager.register_message("assistant", answer)  
• 사용자 입력 직후(LLM 호출 전): ContextManager.register_message("user", msg)  
• 새 대화 세션 진입 시:
    startup_prompt = ContextManager.hydrate_prompt()
    llm(system=CONSTANT_SYSTEM, messages=startup_prompt)

4. 데이터 흐름 시나리오
─────────────────
(1) 평상시 대화  
   user → register_message → LLM → assistant 답변 → register_message → save

(2) 중단 후 재접속  
   • 앱이 context.json 존재 확인  
   • ContextManager.hydrate_prompt() 로 부트  
   • LLM 은 ‘요약 + 최근 대화’ + ‘프로젝트 메타’가 합쳐진 프롬프트로 즉시 과거 맥락 인지

(3) Plan 전환 or Task 완료  
   • WorkflowManager 가 current_plan_id / task_id 변경  
   • ContextManager.data.memory 업데이트 후 save  
   • 필요 시 conversation.running_summary를 새 plan 초기 설명으로 리셋

5. 구현 팁 & 베스트 프랙티스
─────────────────
• Token / char 단위 계산은 openai-tiktoken 등으로 정확히.  
• running_summary 는 “한글 400자·영문 700자 이하”등 가이드 규격을 둔다.  
• summary 알고리즘은 ➊ map-reduce summarize, ➋ sentence-bert Rake 키워드 추출 후 재조합 등 경량화 가능.  
• 멀티 세션 충돌 방지: context.json 잠금(lockfile) 혹은 timestamp 비교로 갱신 우선권 결정.  
• 비밀 데이터(Access key 등)는 context.json 에 두지 않는다 → secrets.json 별도.  
• snapshots/ 에 일정 주기(예: 30 min)로 context.json 의 시점 복제 → 복구 가능.  
• 대화 내용이 Git 로그 등에 노출되지 않도록 .gitignore 에 .ai-brain/ 포함.

6. 완전 복원 체크리스트
─────────────────
[✔] 대화 요약(running_summary)  
[✔] 최근 N턴(recent_window)  
[✔] 활성 Plan/Task + 워크플로우 상태  
[✔] 마지막 결정·열린 파일·경로 등 작업 맥락  
[✔] 토큰 초과 시 자동 roll-up & summary 갱신  
[✔] 신규 세션 LLM 프라이밍 함수(hydrate_prompt)

이 구조·알고리즘으로 context.json 만 있으면 “어제 어디까지 이야기했더라?”가 사라집니다.