# 프로젝트 분석 파이프라인 결과

## 1단계: 구조 분석
아키텍처 개요  
──────────────────  
1) “AI Coding Brain” 이라는 상위 애플리케이션이 있고, 그 안에 다음과 같은 3-Layer 구조가 형성돼 있습니다.  

• Interface / Execution Layer  
  →  json_repl_session.py : 사용자가 보낸 파이썬 코드를 JSON-기반 REPL 세션으로 실행하면서 STDOUT/STDERR를 캡처해 다시 JSON으로 돌려줌.  
  →  대화형 UI·Bot 또는 터미널이 이 레이어를 호출합니다.

• Helper / Service Layer  
  →  ai_helpers_new 패키지 : util, file, code, search, llm, git, project 등 서브모듈을 하나로 묶은 “통합 헬퍼 라이브러리”.  
  →  json_repl_session이 최초 실행 때 지연-로딩(load_helpers)으로 이 모듈을 읽어들여 전역에 주입함.  
  →  OpenAI-O3 API, Git CLI, 파일시스템 등을 래핑해 상위 레이어가 단일 API로 접근하도록 해 줍니다.

• Orchestration / Persistence Layer  
  →  workflow_wrapper / flow_project_wrapper (외부 파일)  
  →  workflow.json : 영속 설정, 히스토리·체크포인트·크로스-챗 공유 여부 등을 담는 메타파일.  
  →  위 두 래퍼를 통해 “작업 단위(Workflow)”와 “프로젝트 단위(Project-Flow)”를 정의·실행하며, FILE_PERSISTENCE 프로토콜로 상태를 보존합니다.

데이터·제어 흐름  
──────────────────  
사용자 입력 → (UI) → json_repl_session.execute_code  
  └─ 첫 실행 시 load_helpers() → ai_helpers_new import & 전역 주입  
  └─ 코드 실행 중 필요 함수 호출  ➜  ai_helpers_new 서브모듈  
        ├─ LLM : ask_o3_async etc. → OpenAI-O3  
        ├─ Git : git_* 래퍼       → git CLI  
        ├─ File/Project/Grep 등  → 로컬 FS  
  └─ 실행 결과 캡처 후 JSON 직렬화  
  └─ Workflow / Flow-Project가 활성화돼 있으면  
        상태·로그를 workflow.json 및 체크포인트로 저장

핵심 컴포넌트 3개  
──────────────────  
1. AI Helpers v2.0 패키지 (python/ai_helpers_new)  
   • 여러 범용 기능(파일·코드 분석, LLM 호출, Git 조작 등)을 일관된 `{ok,data}` 인터페이스로 제공  
   • 상위 레이어는 이 모듈만 알면 대부분의 로컬/원격 작업을 수행 가능

2. JSON REPL Session 엔진 (python/json_repl_session.py)  
   • 대화형 실행 환경을 담당하며, 표준 입·출력을 가로채 JSON으로 변환  
   • 지연-로딩으로 Helpers를 연결하고, Execution Counter·글로벌 네임스페이스 관리, 예외-트레이스 캡처까지 처리

3. Workflow & Persistence 시스템 (workflow_wrapper, flow_project_wrapper, workflow.json)  
   • “행동 단위(Workflow)”와 “프로젝트 단위(Flow-Project)”를 정의하고 실행 순서를 조율  
   • history_tracking, checkpoint_system, cross_conversation, auto_recovery 등 영속 기능을 제공해 세션이 끊겨도 상태 복구 가능

요약  
이 프로젝트는 “실행 엔진(JSON REPL) ↔ 범용 헬퍼(API) ↔ 작업-오케스트레이션(Workflow)” 세 축으로 나뉜 3-계층 구조이며, 위의 세 컴포넌트가 시스템의 핵심 동력원입니다.

## 2단계: 개선 방안
(진행 중...)

---
*생성 시간: 2025-07-19 23:15:26*
