────────────────────────────────────────────────────────
A. 제안된 개선안의 타당성
────────────────────────────────────────────────────────
1. 전역 변수 제거 → BrowserManager 집중
   • 이미 helpers 쪽에서 BrowserManager 우선-조회 → 하위 호환 레이어만 남은 상태  
   • BrowserManager는 다중-프로젝트·스레드 대응·메타데이터 보유 등 구조적으로 “전역 싱글톤 변수”보다 확실히 낫다.  
   • 단, list_instances 내부 오타(instances.h.append)-수정 필요.  
   ⇒ 전반적으로 “전역 변수 → BrowserManager” 전환은 합리적이고 큰 이득(동시성·테스트 용이성)을 기대할 수 있다.  

2. ai_helpers_new와 통합
   • ai_helpers_new 쪽은 Flow(플래너) 기능만 담당하며 웹자동화 모듈을 직접 참조하지 않음.  
   • 따라서 “웹 모듈이 Flow 측을 임포트한다” ‑> 순환 의존 가능성 O  
     – web.py에서 Flow API 호출 시 or ‘스크린샷 경로에 프로젝트 정보 요청’ 시 import path 주의.  
   • 해결책:  
     ‑ web.py → Flow 관련 객체를 “런타임 주입” (get_current_session()을 함수 내부에서 import)  
     ‑ 최상위 import 에선 Flow 관련 모듈을 전혀 탑재하지 않도록.

3. 프로젝트 경로 통합  
   • 스크린샷·다운로드 등 동일한 “프로젝트 컨텍스트” 디렉터리를 쓰면 관리 편의성이 크다.  
   • 현재 Flow 쪽은 .ai-brain/flow, 웹 쪽은 산발적(default=./screenshots 등).  
   • “ContextualPathProvider” 같은 경량 util 클래스에 모든 서브모듈이 의존하도록 하면 충돌/중복 방지.

────────────────────────────────────────────────────────
B. 잠재적 위험·부작용
────────────────────────────────────────────────────────
1. 광범위한 전역-변수 치환
   • 60여 곳 수정 → 미처리된 참조는 즉시 AttributeError ⇢ 런타임 실패.  
   • 테스트 커버리지 불충분 시 회귀 위험이 크다.

2. Singleton-Manager의 단점
   • 다중 파이썬 프로세스(멀티-프로세싱, 노트북 커널 재시작) 환경에서는 프로세스 간 공유가 되지 않는다.  
   • stop() 미호출 시 BrowserManager 내부 딕셔너리에 “유령 인스턴스”가 남는다(메모리 누수).  
     – WeakValueDictionary + atexit 등록 권장.

3. 순환 의존 가능성
   • web.py → get_current_session() 호출(→ ai_helpers_new)  
   • ai_helpers_new 내부에서 web.py에 접근하려 하면 순환.  
   → 호출 방향을 단방향으로 유지(웹 → 플로우 정보 읽기까지만).

4. 브레이킹 체인지
   • 기존 코드에서 globals()['_web_instance'] 직접 접근하는 패턴이 사라짐  
   • Deprecation Warning -> 차기 메이저 릴리스에서 제거하기 전에 문서/마이그레이션 가이드 필요.

5. Thread Dead-Lock
   • BrowserManager 안쪽과 REPLBrowserWithRecording 둘 다 자체 lock 사용  
   • 웹 함수들이 두 락을 중첩 획득할 때 락 순서가 달라지면 교착 가능.  
   → “획득 순서” 규칙(or re-entrant lock) 명시.

────────────────────────────────────────────────────────
C. 구현 시 주의사항
────────────────────────────────────────────────────────
1. list_instances 버그 수정 (instances.h.append → instances.append).  
2. remove_instance 호출 시 실제 Selenium/Playwright 인스턴스 stop() 호출(try/except).  
3. _get_web_instance · _set_web_instance  
   ‑ 첫 단계에서는 “soft-deprecation” : 내부에서 BrowserManager 사용 후 여전히 global 변수도 write.  
   ‑ 다음 단계에서 globals() 경로 제거 예정.  
4. JS Executor 등 다른 서브모듈이 _web_instance 사용 여부 확인.  
5. 테스트 순서가 꼬여도 BrowserManager.clear_all() 으로 완전히 초기화하도록 전역 reset helper 추가.

────────────────────────────────────────────────────────
D. 대안/개선 아이디어
────────────────────────────────────────────────────────
1. 싱글톤 대신 ContextVar
   – async/await 환경에서 프로젝트마다 다른 브라우저 세션 필요할 때 ContextVar가 더 유연.  
2. Dependency-Injection(Factory) 패턴  
   – BrowserSessionProvider 인터페이스를 두고, 테스트에서는 FakeProvider 주입.  
3. WeakValueDictionary + Finalizer로 “닫힌” 브라우저 객체 자동 청소.  
4. ai_helpers_new ↔ 웹 통합은 “Event-bus” 모델(예: ‘browser_started’ 이벤트 발생 → Flow 측 로그 기록)로 느슨하게 묶기.

────────────────────────────────────────────────────────
E. 우선순위 재조정 제안
────────────────────────────────────────────────────────
1. Task 1 전역 제거(2h)와 Task 3 프로젝트 경로 통합(0.5h)을 먼저 묶어서 진행  
   → 파일경로 변경까지 한 번에 끝내야 레거시 경로 혼재 방지.  
2. 이후 Task 2(ai_helpers_new 통합)를 착수  
   → 웹모듈 안정성 확보 후 Flow 쯥 연결하는 편이 위험도↓.  
3. 문서/가이드/Deprecation Warning 강화(0.5h)  
   → 실제 마이그레이션 비용 절감 효과 큼.

────────────────────────────────────────────────────────
F. 예상되는 기술적 난제
────────────────────────────────────────────────────────
• 60여 call-site 롤링하면서 테스트 격리/병렬 실행이 깨질 가능성.  
• BrowserManager 싱글톤이 노트북 환경(셀 다시 실행)에서 “이미 종료된 핸들”을 재사용하려다 예외 발생.  
• Flow 세션이 초기화되지 않았을 때 web.py가 get_current_session()을 호출하면 임시 프로젝트 디렉터리 생성 → 사용자가 의도치 않은 경로에 파일 생성.  
• (Windows) 경로 길이/인코딩 문제: .ai-brain/flow/ 와 screenshots/ 가 합쳐질 때 — pathlib 사용.

────────────────────────────────────────────────────────
G. 단계별 구현 전략(예상 일정 3 단계)
────────────────────────────────────────────────────────
1️⃣ PREP (½ day)
   • BrowserManager.list_instances 버그 수정  
   • add BrowserManager.close_instance(project) → 내부에서 instance.stop() 시도  
   • helpers._get/_set → BrowserManager 우선 + Deprecation Warning 확실히 노출  
   • unit-test: start→goto→stop → clear_all

2️⃣ PHASE A (1 day) – 전역 제거
   • 코드베이스 grep → _web_instance 참조 모두 helpers._get/_set 사용하도록 통일  
   • helpers 내부에서만 _web_instance 유지, 외부에는 직접 노출 금지  
   • docs 업데이트, CHANGELOG “global instance deprecated”

3️⃣ PHASE B (1 day) – ai_helpers_new 연결
   • /api/web.py 작성:  
     – get_current_session() 런타임 import  
     – screenshots path = session.project_context.screenshot_path  
   • 단방향 참조 확인(웹→ai_helpers_new only)  
   • end-to-end test: flow plan 생성 → web_start → click → stop → flow task 완료

4️⃣ PHASE C (½ day) – 클린-업
   • globals()['_web_instance'] 완전 제거, fallback raise RuntimeError(다음 메이저)  
   • atexit hook → BrowserManager.clear_all()  
   • 릴리스 노트 / 마이그레이션 가이드 배포.

────────────────────────────────────────────────────────
결론
────────────────────────────────────────────────────────
• 전역 상태 제거와 BrowserManager 집중은 타당하고 유지보수성이 크게 향상된다.  
• BrowserManager 구조는 경미한 수정(list bug, WeakRef, close_instance 추가)만 하면 목적에 적합.  
• ai_helpers_new와의 통합은 “런타임-의존, 단방향 임포트”를 지키면 순환 참조 문제는 피할 수 있다.  
• 우선순위는 “안정화(전역 제거+경로 통합)” → “Flow 통합” 순이 더 안전하다.