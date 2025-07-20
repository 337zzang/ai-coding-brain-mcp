# 워크플로우 분석 1

워크플로우 관련 파일을 “무엇을 하고, 어디가 겹치며, 어디가 문제인지” 중심으로 정리했습니다.  
(코드 일부가 잘려 있지만, 보이는 범위 내에서 최대한 추론했습니다.)

────────────────────────────────────────
1) 각 파일의 역할과 책임
────────────────────────────────────────
• python/workflow_wrapper.py  
  - ‘workflow’ 패키지(WorkflowV2) 를 로딩-랩핑하는 어댑터.  
  - task / start / done / status / report / wf 등을 전역 함수로 노출하고,  
    helpers 객체에 붙일 WorkflowHelpers 클래스도 제공.  
  - 간이 별칭(wt, ws, wd)과 파일/커밋 자동-추적용 훅(wrapper) 포함.  

• python/workflow/__init__.py  
  - WorkflowV2 의 “공식” 퍼사드.  
  - 내부의 integration / helper 모듈을 다시 감싸 동일한 task, start, wf … API를 제공.  
  - 초기화(init) 자동 호출.  

• python/session_workflow.py  
  - “WorkSession” 클래스로 이루어진 초경량 워크플로우(파일: memory/workflow.json 저장).  
  - add_task / complete_task / skip_task … 등 기본 기능 전부 자체 구현.  
  - WorkflowV2 와 독립적으로 존재(= 동일 문제를 두 번 해결).  

• python/flow_project_wrapper.py  
  - 바탕화면 폴더를 탐색해 프로젝트 디렉터리로 cd,  
    글로벌 컨텍스트(GlobalContextManager) 갱신,  
    workflow_wrapper.wf(“/start …”) 호출로 프로젝트-별 워크플로우도 전환.  

• python/workflow/global_context.py  
  - 사용자의 홈(~/.ai-coding-brain)에 프로젝트 단위 컨텍스트를 저장/조회.  
  - 최근 프로젝트, AI context(markdown) 파일 생성 등 “시스템 전역” 범위.  

• python/ai_helpers_new/project.py  
  - 현재 디렉터리 기준 프로젝트 메타 감지, 디렉터리 스캔/생성 유틸리티.  
  - 워크플로우와 직접 의존성은 없음.  

• memory/workflow.json, memory/workflow_history.json  
  - session_workflow.py 전용 데이터 파일. (WorkflowV2 와는 포맷이 다름)  

────────────────────────────────────────
2) 중복(혹은 충돌)된 기능/심볼
────────────────────────────────────────
A. “wf” 함수  
   1. workflow_wrapper.wf           ← helpers 친화적 래퍼  
   2. workflow.__init__.wf           ← helper.workflow_v2 직접 래핑  
   3. workflow.integration.workflow_integrated 내부 엔트리(직접 import)  
   ⇒ import 에 따라 서로 다른 객체가 노출됨. (flow_project_wrapper 는 ①을 임포트함)

B. task / start / done / status / report 동일 함수가  
   - workflow_wrapper 전역 갱신용 심볼  
   - workflow/__init__.py 의 퍼사드  
   - workflow.integration 모듈 내부 실구현  
   세 군데서 정의.  

C. 워크플로우 엔진 두 개  
   - WorkflowV2 (workflow 패키지)  
   - session_workflow.WorkSession  
   기능/저장 방식/명령이 유사하지만 완전히 별개.  

D. 컨텍스트 시스템 두 개  
   - 프로젝트 내부 memory/workflow.json (session_workflow)  
   - 홈 디렉터리 .ai-coding-brain/projects/* (global_context)  

────────────────────────────────────────
3) 사용되지 않는 코드/데드 코드
────────────────────────────────────────
• workflow_wrapper.hook_file_creation / hook_git_commit 내부에서 호출하는  
  auto_track_file_creation, auto_track_git_commit 함수가 정의된 곳이 없음.  
• _manager.start_next_task 존재 확인 but WorkflowV2Manager 클래스에 실제 메서드가  
  없으면 분기문이 항상 “태스크를 시작합니다” 반환.  
• print(f"[INFO] WorkflowV2 Wrapper 로드 …") 가 잘려 있어 정상 실행 불가(문법 오류 가능).  
• workflow_wrapper 의 sys.path 삽입 로직이 두 번 반복(import sys 재작성).  
• session_workflow.WorkSession 내부 _mcp_message, _track_git… 등 호출되는 메서드가  
  파일에 정의돼 있지 않음(아마도 TODO).  
• global_context._add_to_history 구현부 하단이 잘려 있음—실제 저장 안 될 가능성.  

────────────────────────────────────────
4) 순환 의존성/설계상 문제점
────────────────────────────────────────
1. workflow_wrapper → workflow.integration → (내부에서) workflow_wrapper 를  
   다시 임포트할 가능성 → 런타임 순환 위험.  
2. flow_project_wrapper  ─→ workflow_wrapper.wf ─→ workflow.integration…  
   flow_project_wrapper 내부에서 global_context 를 호출 →  
   global_context 가 다시 프로젝트 정보를 적재할 때 helpers 를 호출한다면  
   간접 순환 가능성.  
3. sys.path 조작이 여러 파일에서 중복으로 수행되어 모듈 임포트 순서가 비결 determinism.  
4. WorkSession 과 WorkflowV2 가 서로를 인식하지 못해서  
   동일 프로젝트에서 두 JSON 파일이 병행 생성 → 상태 불일치.  
5. global_context 가 “tasks_count” 를 자체 필드로 보유하지만  
   실제 태스크 소스(WorkflowV2 or WorkSession)와 동기화 로직이 없음.

────────────────────────────────────────
5) global_context ↔ 프로젝트별 컨텍스트 충돌
────────────────────────────────────────
• 프로젝트 내부 파일(memory/workflow.json) 과  
  홈 디렉터리(.ai-coding-brain/projects/<proj>/context.json) 가  
  서로 다른 스키마, 다른 책임을 가짐.  

• flow_project_wrapper 는 프로젝트 전환 시  
  a) global_context 에 recent_work, path 등을 기록  
  b) workflow_wrapper.wf(“/start …”) 호출 → WorkflowV2 로 새 워크플로우 시작  
    (그러나 WorkSession 은 관여 안 함).  

• 만약 사용자 코드가 session_workflow.py API 를 직접 사용해 파일을 갱신하면  
  global_context 와 WorkflowV2 양쪽 모두 최신 작업/태스크 수가 틀어짐.  

• global_context ‘tasks_count’ 는 외부에서 전달받은 숫자를 그대로 저장할 뿐  
  실제 워크플로우 파일을 다시 읽어 검증하지 않음 → 쉽게 부정확해짐.  

────────────────────────────────────────
요약 / 권장 리팩토링 방향
────────────────────────────────────────
1. “엔진 하나” 원칙  
   - WorkflowV2 를 메인으로 정하고 session_workflow.py 는 기능 통합 후 제거.  
   - 또는 반대로 WorkSession 을 남기더라도 중복 API(task/start/…) 는 한 군데로.  

2. 진입점 단일화  
   - wf / task / start / done / status / report 는 workflow 패키지만 제공하도록 하고  
     workflow_wrapper 의 전역-삽입, 별칭 함수(wt/ws/wd) 등은 helper 레이어나  
     IPython 확장으로 분리.  

3. 글로벌 컨텍스트와 프로젝트 컨텍스트 스키마 통일  
   - memory/workflow.json 을 global_context 가 직접 읽어서  
     tasks_count·recent_work 등을 동기화하도록 통합.  
   - “current_project” 의 위치(path)도 한 곳에서만 관리.  

4. 데드 코드/미구현 후크 제거 또는 실제 구현 추가  
   - auto_track_file_creation / auto_track_git_commit 구현하거나 코드 삭제.  
   - 잘린 print/메서드 정의 보강.  

5. sys.path 핸들링 정리  
   - 최상위 진입점 하나에서만 path 조작 후, 나머진 절대 임포트 사용.  

이상은 코드 베이스를 작동 가능한 “하나의 일관된 워크플로우 시스템”으로  
정리하기 위해 우선 파악해야 할 겹침·누락·문제점입니다.