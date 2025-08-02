아래 목록은 “실제-위험 여부 → 즉시 개선 필요 여부 → 수정 시 영향 범위”를 기준으로 추려 본, 가장 시급한 개선 과제 3-5 개입니다.

1. 리스트에 존재하지 않는 `h.append` 사용(전역)
   • 위험성  
     - `list` 객체에는 `h` 속성이 없으므로 실행 즉시 `AttributeError` 발생 → 해당 함수/모듈이 아예 동작하지 않음.  
   • 즉시 개선 필요 여부  
     - “예”. 실제 런타임 오류로 이어지는 치명적 버그. 문법 수준에서 막히므로 테스트·리팩터링 이전에 반드시 수정해야 함.  
   • 영향 범위  
     - project.py `_read_if_exists`  
     - code.py `ASTCollector` 내부  
     - utils/safe_wrappers.py 여러 곳  
     (모듈 간 의존이 없어도, 파싱·안전 호출 등 핵심 기능 전체가 멈춤)  

2. simple_flow_commands.flow()의 불완전한 반환 로직/구문 오류
   • 위험성  
     - `/list` 외 명령은 반환값이 없어 호출 측에서 KeyError, NoneType 오류 유발.  
     - 중괄호 미종결 `}` 로 파이썬 파싱 자체가 실패(파일 import 불가).  
   • 즉시 개선 필요 여부  
     - “예”. CLI·API를 막론하고 플로우 기능 전체가 사용 불가.  
   • 영향 범위  
     - simple_flow_commands.py 전체, UltraSimpleFlowManager 를 호출하는 상위 서비스.  

3. 플랫폼 하드코딩 및 경로 처리(project.flow_project_with_workflow)
   • 위험성  
     - 데스크톱 경로를 Windows(“바탕화면”)·macOS(“Desktop”) 두 가지만 가정. 서버·CI나 영문 윈도, Linux 계정 등에서 곧바로 실패.  
   • 즉시 개선 필요 여부  
     - “높음”. 실제 운영 환경이 다양하다면 기능이 자주 실패. 다만 치명적 런타임 오류는 아니므로 1,2번보단 우선순위가 낮음.  
   • 영향 범위  
     - 프로젝트 전환 기능 및 연동된 워크플로우 초기화.  

4. 전역 상태(_manager, _current_plan_id) 공유 설계
   • 위험성  
     - 다중 스레드/다중 세션 환경에서 레이스 컨디션·데이터 오염. CLI 단일 프로세스만 쓴다면 크리티컬하지 않지만 확장성이 막힘.  
   • 즉시 개선 필요 여부  
     - “중간”. 동시성 시나리오가 없다면 급하지 않으나, 앞으로 서비스를 확장(예: Web API)할 계획이면 구조적 변경이 필요.  
   • 영향 범위  
     - simple_flow_commands.py 와 UltraSimpleFlowManager, 나아가 플로우 관련 모든 모듈.  

5. 안전 래퍼에서 내부 모듈 의존 강제(import ai_helpers_new as h)
   • 위험성  
     - 순환 의존이나 부분 설치 환경에서 ImportError 발생 가능.  
   • 즉시 개선 필요 여부  
     - “낮음~중간”. 실행 시점까지 지연되지만, 배포/테스트 환경에 따라 터질 수 있음.  
   • 영향 범위  
     - utils/safe_wrappers.py 및 이를 이용하는 모듈.  

우선순위 요약
1) list.h.append → .append 치환(전역)  
2) simple_flow_commands.flow의 반환/구문 오류 수정  
3) 데스크톱 경로 하드코딩 개선  
4) 전역 상태 제거 또는 캡슐화  
5) 안전 래퍼의 모듈 의존성 완화