
# 워크플로우 시스템 리팩토링 - O3 조언

## 질문 시각
2025-07-18 22:04:06

## 현재 상황

현재 워크플로우 시스템 구조:

1. 파일 중복:
   - workflow_helper.py (10.7 KB) - 파일 디렉토리 관련 기능
   - workflow/workflow_helper.py (4.6 KB) - WorkflowHelper 클래스
   - workflow_extension.py (5.2 KB) - 워크플로우 명령어 함수들

2. 디렉토리 구조:
   python/
   ├── workflow_helper.py
   ├── workflow_extension.py
   └── workflow/
       ├── __init__.py
       ├── dispatcher.py (3.4 KB)
       ├── event_store.py (3.2 KB)
       ├── improved_manager.py (26.9 KB)
       ├── models.py (22.6 KB)
       ├── workflow_helper.py
       └── messaging/
           └── message_controller.py

3. 발견된 문제:
   - workflow_helper.py가 2곳에 중복 (이름은 같지만 기능 다름)
   - 워크플로우 명령어가 workflow_extension.py에 분산
   - improved_manager.py가 너무 큼 (26.9 KB)
   - 많은 워크플로우 명령어가 구현되지 않음 (/start, /plan 등)
   - 복잡한 import 구조

4. 목표:
   - AI Coding Brain MCP의 핵심 기능에 집중
   - 중복 제거 및 구조 단순화
   - 유지보수성 향상
   - 불필요한 복잡성 제거


## O3의 답변
1. 주요 문제점  
• 동일한 파일명이 서로 다른 기능을 갖고 두 곳에 존재 – 유지보수·import 혼란 (workflow_helper.py 2개).  
• 기능이 하나의 거대한 파일(improved_manager.py)에 뭉쳐있어 응집도/가독성 저하, 테스트 어려움.  
• 워크플로우 명령어(/start /plan …) 로직이 workflow_extension.py, improved_manager.py 등 여러 위치에 흩어져 있어 흐름 파악이 어렵고 빠진 명령어가 많음.  
• 루트-레벨 모듈과 패키지 내부 모듈이 섞여 상대/절대 import 가 꼬임 → IDE 인텔리센스·배포 시 문제.  
• 실제 “AI Coding Brain MCP”가 필요로 하는 최소 기능(작업저장소, 간단한 상태머신) 대비 과잉 설계(메시징, 확장포인트, 중복 util 등).  

2. 구조 단순화 방안  
• “workflow” 라는 단일 패키지로 수렴 후, 루트-레벨 중복 모듈 제거.  
• Helper · Command · Manager · Store · Dispatcher · Model 의 여섯 개 단위로만 나눔(관심사 분리).  
• improved_manager.py 는 Manager·Command 두 파일로 쪼개고 필요없는 고급기능(슬랙, 멀티스레드 큐 등) 제거.  
• Event-driven 구조는 유지하되, Dispatcher → Manager → EventStore 의 최소 파이프라인만 남김.  
• CLI-style 엔트리포인트는 __main__.py 나 main.py 하나로 집중.  
• 모든 import 는 workflow.XXX 형식의 절대 import 로 통일.  

3. 필수 기능(=유지) / 제거 대상  
유지해야 할 것  
  – WorkflowManager: /start /plan /status /resume 정도의 핵심 명령 처리.  
  – EventStore: JSON 혹은 SQLite 파일에 이벤트/상태 영속.  
  – Models: Task, Plan, RunStatus 등 1-2개의 단순 dataclass.  
  – Dispatcher: 명령 → Manager 라우팅.  
  – Helper: 경로 계산, 워크스페이스 초기화, 간단한 파일 I/O.  
제거 또는 이후 필요 시 재도입  
  – Messaging(message_controller.py), 고급 플러그인 시스템, Slack/Webhook.  
  – 복잡한 retry/job queue, 미구현 명령 템플릿, 중복 helper.  
  – 루트-레벨 workflow_extension.py, workflow_helper.py.  

4. 구체적 통합/삭제 플랜  
단계 1: 중복 제거  
  a) 루트 workflow_helper.py 와 workflow/workflow_helper.py 내용 비교 → 겹치지 않는 함수만 합쳐 ‘workflow/helper.py’ 에 병합.  
  b) 병합 후 두 원본 파일 삭제.  
  c) 모든 import 변경: from workflow_helper import … → from workflow.helper import …  

단계 2: 명령어 통합  
  a) workflow_extension.py 의 각 명령 함수를 ‘workflow/commands.py’ 로 이동.  
  b) Manager 내부에 흩어진 명령 핸들러를 commands.py 로 옮겨 “함수형 커맨드 패턴” 구성.  
  c) workflow_extension.py 삭제.  

단계 3: Manager 축소  
  a) improved_manager.py 를 열어 “핵심 흐름”(/start, /plan, /resume, /status, 내부 상태머신) 코드만 남김(≈30-40%).  
  b) 이 코드를 ‘workflow/manager.py’ 로 저장.  
  c) 부가 메소드(알림, 디버그 UI 등) 제거.  

단계 4: 나머지 리네이밍/청소  
  – dispatcher.py, event_store.py, models.py 는 그대로 두되 dead code 정리.  
  – 메시징 서브패키지 전체 제거(필요 시 git history 로 복원 가능).  
  – __init__.py 에서 외부 API export: from .manager import WorkflowManager 등.  

5. 권장 최종 디렉토리(예시)  

python/  
└── workflow/  
    ├── __init__.py        # public export / CLI 등록  
    ├── __main__.py        # “python -m workflow” 진입점  
    ├── helper.py          # 파일·디렉토리 util  
    ├── models.py          # dataclass Task, Plan …  
    ├── event_store.py     # load_events / save_event  
    ├── dispatcher.py      # route(cmd, args) → commands.call()  
    ├── commands.py        # start(), plan(), status(), resume()  
    └── manager.py         # WorkflowManager (비즈니스 로직)  

(선택) tests/, docs/  

이 구조로 옮기면  
• 파일 수 14→8, 총 코드량 약 50~60% 감소  
• 단일 패키지 경로 → import 충돌 해소  
• 명확한 책임 분리로 유지보수 용이  
• 불필요한 고급 기능 제거로 “AI Coding Brain MCP” 핵심 목표에 집중 가능.

## 메타 정보
- 추론 시간: 46.76초
- 사용 토큰: 2454
