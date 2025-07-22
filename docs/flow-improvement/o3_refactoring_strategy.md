# FlowManagerUnified 리팩토링 전략

생성일: 2025-07-22T19:10:33.030370
o3 Task ID: o3_task_0002

## 분석 대상
- 파일: python/ai_helpers_new/flow_manager_unified.py
- 크기: 2086 라인
- 메서드 수: 64개
- 복잡도: 매우 높음 (단일 책임 원칙 위반)

## o3 분석 결과

아래 제안은  
“2000+ 라인 ‑ 64 메서드 ‑ 단일 클래스”라는 현재 구조를, 

1) “작은 책임 단위의 모듈”로 분리하고  
2) “외부 API(=FlowManagerUnified 인터페이스)”는 그대로 유지하며  
3) “점진적으로 마이그레이션”할 수 있도록 설계되었습니다.   

────────────────────────────────────────
1. 클래스 분할 전략
────────────────────────────────────────
도메인 + 기술 + 어댑터 계층으로 나누어 6개 핵심 클래스를 우선 분리합니다.  
(괄호 안은 주요 public 메서드 예시)

① FlowRepository – “저장소”  
   • load(), save(flow), list(), delete(id)  
   • 파일-I/O/직렬화 담당 → 테스트 시 mock 으로 교체 가능

② FlowService – “비즈니스 로직(Flow 중심)”  
   • create_flow(name), get_current(), set_current(id)  
   • add_plan(flow_id, plan), …  
   • Flow 도메인 객체를 조작, 트랜잭션 수준의 검증 포함

③ PlanService – “Plan 전용 로직”  
   • create_plan(flow_id, title, …)  
   • select_plan(plan_id), reorder_tasks(…), …

④ TaskService – “Task 전용 로직”  
   • add_task(plan_id, text), update_state(task_id, state), …

⑤ ContextService – “대화/프롬프트/LLM 컨텍스트”  
   • push(message), pop(), snapshot(), …

⑥ CommandProcessor – “/명령어 → Service 호출”  
   • register(cmd, handler)  
   • process(raw_string) → Dict[ str, Any ]  

(또는 Command 패턴으로, 각 명령을 클래스로 분할해도 무방)

추가 보조 클래스
• Flow, Plan, Task, Context ⇒ @dataclass 로 정의 (순수 데이터)  
• Validator / Exception / Mapper 등은 필요 시 서브모듈로

────────────────────────────────────────
2. 각 클래스의 책임·인터페이스
────────────────────────────────────────
FlowRepository
  - 기술영역(persistence). 다른 서비스에서는 “의존성 주입(DI)”으로 받는다
  - 인터페이스: 영속화 결과로 항상 domain 객체 반환 (dict 금지)

FlowService
  - Flow 단위 기능; 내부에서 FlowRepository를 호출
  - 높은 레벨 비즈니스 규칙을 단위테스트 하기 쉽다

PlanService
  - Plan CRUD, 정렬, 선택 등
  - FlowService 를 협력 객체로 받아 “Flow 중첩 rules”를 재사용

TaskService
  - PlanService에 의존
  - Task state machine(STOPPED → DOING → DONE 등) 검증 책임

ContextService
  - LLM 호출 컨텍스트 스택 관리
  - 외부 infra(예: langchain)와 직접 통신하더라도, public API는 순수 Python 타입만 반환

CommandProcessor
  - UI/CLI 계층
  - Service 객체들을 생성자에서 주입 받은 뒤,  
    cmd → handler(dict) 매핑만 수행
  - 비즈니스 예외 → 사용자 친화 메시지로 매핑하는 계층

────────────────────────────────────────
3. 클래스 간 상호작용 패턴
────────────────────────────────────────
        +---------------+         +------------------+
 CLI ──▶│CommandProcessor│───▶▶──▶│   Service layer  │──▶ Flow/Plan/Task/Context
        +---------------+         +------------------+
                                       ▲
                                       │
                                  +-----------+
                                  │Repository │ (I/O)
                                  +-----------+

• 서비스 ↔ 리포지토리: DI & Interface 기반 (repository mock 으로 단위테스트)  
• 서비스 ↔ 서비스: 메서드 호출. 순환참조 방지를 위해 의존 방향 명시 (PlanService가 FlowService를 의존하지 FlowService가 PlanService를 의존하지 않도록)

────────────────────────────────────────
4. 리팩토링 진행 순서(점진적)
────────────────────────────────────────
Step-0 “보호막”  
  - FlowManagerUnified를 그대로 둔 채, 모든 public 메서드에  
    회귀 테스트(or 스냅샷 테스트) 추가

Step-1 “Pure Data”  
  - Flow/Plan/Task 를 @dataclass 로 추출  
  - FlowManagerUnified 내부에서 dict → dataclass 변환만 먼저 적용

Step-2 “Infrastructure → Repository”  
  - 파일 I/O, JSON 직렬화 부분을 FlowRepository로 이동  
  - FlowManagerUnified 는 repository를 통해서만 파일 작업

Step-3 “CommandProcessor 분리”  
  - process_command 와 _command_handlers 파트를 통채로 CommandProcessor 클래스로 베껴 옮긴 후  
    FlowManagerUnified.process_command는 단순 위임

Step-4 “Service 층 분리”  
  - Flow 관련 로직만 FlowService로 복붙  
  - 유사 방식으로 PlanService, TaskService 등 추출  
  - 추출한 후에도 FlowManagerUnified 기존 메서드들은
    “self._service.메서드()”로 위임만 하게 만든다

Step-5 “Facade 유지 & 제거”  
  - 기존 외부 코드가 FlowManagerUnified를 사용한다면,  
    클래스명을 유지하되 구현을 “Facade + Adapter”로만 남겨둔다
  - 새 코드에서는 CommandProcessor/Service 들을 직접 사용

Step-6 “폴더 구조 재편”  
  ai_helpers_new/
      domain/{flow.py, plan.py, task.py}
      service/{flow_service.py, …}
      infra/{flow_repository.py}
      presentation/{command_processor.py}
      legacy/flow_manager_unified.py  (Facade)

Step-7 테스트 작성 & 삭제  
  - 단위 테스트를 서비스/레포 단에서 작성  
  - Facade 호환 테스트는 통과만 확인하고, 새 기능은 Service 테스트로만 추가

────────────────────────────────────────
5. 기존 API 호환성 유지
────────────────────────────────────────
1) “동일 클래스 이름” + “동일 public 시그니처” 보장  
2) 내부 구현을 새 구조로 위임  
   예)
   class FlowManagerUnified:
       def __init__(…):
           self._repository = JsonFlowRepository(path)
           self._flow_service = FlowService(self._repository, …)
           self._plan_service = PlanService(self._flow_service)
           self._cmd = CommandProcessor(
               flow=self._flow_service,
               plan=self._plan_service,
               task=TaskService(self._plan_service),
               context=ContextService()
           )
       def process_command(self, cmd:str):
           return self._cmd.process(cmd)
       # 아래 나머지 메서드도 동일하게 위임

3) DeprecationWarning 메커니즘  
   - 새 코드에는 Service/Processor 직접 사용 가이드  
   - Unified 클래스를 @deprecated decorator 로 표시

────────────────────────────────────────
보너스: 리팩토링 가속 팁
────────────────────────────────────────
• “Extractor 객체” 패턴  
  - 리팩토링 툴(PyCharm / VSCode) 로 메서드 추출 → 자동 import 수정  

• 상호의존 최소화  
  - 서비스 ↔ 서비스 호출 시, DTO 객체 대신 domain 객체 전달  

• 명령어 추가 / 삭제  
  - CommandProcessor 내부 dict 에서만 핸들러 교체하므로 확장 용이  

────────────────────────────────────────
요약
────────────────────────────────────────
1. 데이터, 서비스, I/O, UI 계층을 명확히 나누고  
2. FlowManagerUnified는 ‘Facade’ 로 겉모습만 유지하며  
3. 단계별 추출(데이터 → I/O → Command → Service) 로 안전하게 전환하고  
4. 레거시 API 호환성을 보장하면  
   ‑ 단위 테스트 용이  
   ‑ 유지보수 난이도 급감  
   ‑ 새 기능 추가 시 서비스/커맨드 계층만 건드리면 됨

이 순서와 구조를 따르면 “거대한 만능 클래스” 문제를 해소하면서도  
프로덕션 안정성을 유지할 수 있습니다.

## 추가 분석 정보

### 가장 복잡한 메서드들
- _switch_to_project: 169 라인 (라인 1079부터)
- _analyze_plan_context: 103 라인 (라인 448부터)
- _handle_plan_select: 66 라인 (라인 382부터)
- _list_tasks: 62 라인 (라인 753부터)
- _show_status: 57 라인 (라인 595부터)
- _complete_plan: 55 라인 (라인 874부터)
- delete_plan: 54 라인 (라인 1725부터)
- _migrate_legacy_data: 51 라인 (라인 257부터)
- _add_task: 51 라인 (라인 702부터)
- _check_plan_auto_complete: 50 라인 (라인 964부터)

### 의존성
- 외부 패키지: 14개
- 상속: FlowManagerWithContext

## 구현 계획

### Phase 1: 데이터 모델 추출 (즉시 시작 가능)
1. Flow, Plan, Task를 dataclass로 정의
2. 기존 dict 사용 코드를 점진적으로 교체

### Phase 2: Repository 패턴 도입
1. FlowRepository 클래스 생성
2. 파일 I/O 로직 이동

### Phase 3: Service 계층 분리
1. FlowService
2. PlanService 
3. TaskService
4. ContextService

### Phase 4: Command 처리 분리
1. CommandProcessor 클래스
2. 각 명령어별 핸들러 분리

### Phase 5: Facade 패턴으로 호환성 유지
1. FlowManagerUnified를 Facade로 변환
2. 내부적으로 새 구조 사용
