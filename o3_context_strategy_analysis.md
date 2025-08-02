──────────────────────── 1. “Context를 어떻게 들고 다닐 것인가?” ────────────────────────
현재 코드 특성
• 전역 상태   : _manager / _current_plan_id / _current_project_path  
• 상태 전환   : get_manager() 가 os.getcwd() 로 매번 ‘현재 Project’를 추론  
• 사용 패턴   : REPL-like(=동시 사용자 거의 없음) → “지금 딱 한 개”의 Context만 필요  
• 의존 깊이   : 이미 많은 모듈이 manager = get_manager() 방식에 의존

명시적 전달(A) vs 중앙 Session(B)

A. 명시적 전달  
   장점 : 순수 함수·테스트 용이, 병렬 실행 쉬움  
   단점 : 서명을 모조리 고쳐야 함 ‑> 기존 호출부 수십 곳 수정 필요  
         REPL 사용자는 매번 인자를 넘겨야 해서 UX↓  

B. 중앙 Session(전역-ish 객체)  
   장점 : 기존 get_manager() 패턴을 Session.get_manager() 로 치환만 해도 95 % 호환  
         REPL·CLI에서 훨씬 자연스러움  
   단점 : 테스트 시 전역 오염 위험 → contextvars 또는 with session.override() 필요

C. Hybrid (B + A)  
   • 내부적으로는 Session에 저장  
   • 모든 핵심 API의 첫 파라미터를 선택적 context=None 으로 열어 둠  
   • 값이 없으면 Session에서 꺼내 쓰도록 해서  
     ─ 프로덕션/CLI → 암묵적 Session  
     ─ 테스트/멀티스레드 → 명시적 context 주입

현재 구조와 리팩토링 비용을 합치면  
“중앙 Session(B)을 기본으로, 필요 시 명시적 주입을 허용하는 Hybrid(C)”가 가장 실용적입니다.  
(완전 A로 가려면 함수/메서드 시그니처 변경폭이 너무 큽니다.)

──────────────────────── 2. ProjectContext – FlowContext 관계 ────────────────────────
용어 정의
• ProjectContext : “어느 폴더가 활성 프로젝트인가?” + 메타 정보  
• FlowContext    : “그 프로젝트 안에서 현재 어떤 Plan·Task를 보고 있는가?”

관계 모델
1 ProjectContext ──┐               (소유)
                   │ has-a
                   └──> FlowContext   (1 Project에 최대 1 활성 FlowContext)
이유
• Flow 데이터(.ai-brain/flow)는 프로젝트 폴더에 종속 → Project가 상위 의미단위  
• 프로젝트를 바꾸면 FlowContext는 초기화/폐기되어야 하므로 “종속”이 자연스러움  
• 추후 여러 Flow를 동시에 열 계획이 생기면  
  ProjectContext.flow_pool: Dict[flow_id, FlowContext] 로 확장 가능

Session 설계 (Thread-local)
dataclasses 로 예시:

```python
# context.py
from dataclasses import dataclass, field
from contextvars import ContextVar
from pathlib import Path
from typing import Optional

@dataclass
class ProjectContext:
    root: Path
    name: str
    type: str
    has_git: bool

@dataclass
class FlowContext:
    manager: UltraSimpleFlowManager
    current_plan_id: Optional[str] = None

@dataclass
class Session:
    project: ProjectContext
    flow: FlowContext

_current_session: ContextVar[Session] = ContextVar("_current_session")
def get_session() -> Session:
    return _current_session.get()          # RuntimeError -> 아직 세션 없음
def set_session(sess: Session):
    _current_session.set(sess)
```

호환 래퍼:

```python
# 기존 코드와의 브릿지
def get_manager() -> UltraSimpleFlowManager:
    return get_session().flow.manager
```

──────────────────────── 3. 안전한 리팩토링 순서 ────────────────────────
(1) Stage-0 : “세션 껍데기” 추가  
    • context.py / session.py 에 위 dataclass + get_session, set_session 제공  
    • get_manager(), _current_plan_id 등 기존 전역을 세션 속성으로 ‘읽고-쓰기’만 위임  
      ‑> 기존 코드가 그대로 동작

(2) Stage-1 : 프로젝트 전환 로직 이관  
    • project.flow_project_with_workflow() 안에서  
      a) 새 ProjectContext 생성  
      b) 새 UltraSimpleFlowManager(project_path) 준비  
      c) FlowContext 구성 → Session 에 set_session()  
    • os.chdir() 는 유지해도 되지만 가능하면 제거

(3) Stage-2 : 명시적 context 가능하도록 서명 확장  
    핵심 API(create_plan, list_plans …)에
      def create_plan(self, name, *, ctx: Optional[Session] = None):  
      if ctx is None: ctx = get_session()  
    • 호출부는 그대로, 테스트에서는 ctx 주입 가능

(4) Stage-3 : 전역 변수 제거  
    • _manager, _current_plan_id 등의 실제 저장소를 Session 으로만 유지  
    • 전역 이름은 deprecated alias 로 남겨 두었다가 단계적으로 삭제

(5) Stage-4 : 순환 의존 정리  
    • session.py 만 import 최소화 (typing import only)  
    • 나머지 모듈은 from .session import get_session 만 참조 → 의존 방향 단방향  
    • util 계층 → domain → infrastructure 방향으로 계층 고정

(6) Stage-5 : 테스트 추가 & 병렬 시나리오 검증  
    • contextvars 는 Thread 和 asyncio-task 단위 격리 → 간단 병행 테스트 작성  
    • with override_session(tmp_sess): context manager 로 세션 임시 교체 테스트

이 과정을 따르면
• 기능 깨짐 없이 단계별 커밋 가능  
• CLI/REPL UX 유지  
• 향후 멀티 스레드 또는 웹 API 로 확장할 때 explicit context 주입도 이미 준비됨

──────────────────────── 4. 요약 ────────────────────────
1. 전역 난립 → “Hybrid 중앙 Session” 전략이 가장 호환성이 좋다.  
2. ProjectContext ⊃ FlowContext 구조(1:1; 필요 시 N으로 확장)를 권장.  
3. 리팩토링 단계  
   0) Session 껍데기 도입 → 1) 전환 함수에서 Session 설정 → 2) 선택적 ctx 파라미터 추가  
   3) 전역 제거 → 4) 의존 방향 정리 → 5) 병렬/테스트 보강.