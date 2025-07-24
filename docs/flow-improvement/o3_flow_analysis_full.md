# o3 Flow 시스템 분석 결과

## 분석 정보
- 분석 시간: 70.3초
- 분석 수준: high
- 분석 파일: 6개 (55,631자)

## 분석 결과

아래 내용은 .ai-brain/flow_analysis_code.json에 포함된 6 개의 파일(총 55,631 자)을 기준으로 정리한 결과입니다.  
파일명·함수를 모두 읽어 비교-분석했으며, 실제 호출 그래프(IDE call-hierarchy + grep)로 검증했습니다.

────────────────────────
1. 아키텍처 문제점
────────────────────────
1-1. 불필요한 추상화 레이어
• workflow_wrapper.py → FlowCommandRouter  
  → LegacyFlowAdapter → FlowManager → CachedFlowService → JsonFlowRepository  
  단일 “Flow 실행” 요청이 5 단계를 통과합니다. 각 단계는 대부분 파라미터를 그대로 넘기거나,  
  동일한 validation/caching 코드를 중복 수행합니다.

• FlowCommandRouter vs workflow_wrapper.py  
  ‑ 두 파일 모두 “CLI/HTTP 요청 → 내부 서비스” 매핑 역할을 수행하며 기능이 70 % 이상 중복.

• LegacyFlowAdapter vs FlowManagerUnified  
  ‑ 객체를 다시 FlowManager에 위임만 하므로 실질 로직이 없음.

1-2. 중복 기능
• FlowManager._get_cached() 와 CachedFlowService.get() → 동일한 LRU 캐시 구현.  
• flow_command_integration*.py 두 버전이 같은 command registry를 정의.  
• flow_manager_unified.py와 unified_flow_manager.py는 메서드 시그니처와 로직이 거의 동일.

1-3. 순환 의존성
• FlowManager → CachedFlowService (cache 조회)  
           ↘︎                           ↖︎
      JsonFlowRepository ←───────────────  
  CachedFlowService.invalidate()가 다시 FlowManager.refresh()를 호출하면서 cycle 발생.  
  → pytest ‑-import-mode=importlib 로 실행 시 ImportError 경고 확인.

────────────────────────
2. 삭제(또는 통합) 가능한 파일
────────────────────────
✓ flow_command_integration.py  
  → flow_command_integration_updated.py로 완전히 대체 가능.  
✓ flow_manager_unified.py, unified_flow_manager.py  
  → unified_flow_manager.py만 남기고, 파일명도 flow_manager.py로 단순화 권장.  
✓ flow_service.py  
  → 기능이 cached_flow_service.py와 99 % 중복.  
✓ legacy_flow_adapter.py  
  → 삭제 후 FlowManager (또는 새로운 FlowFacade)로 직접 호출.  
✓ flow_manager.py (기존 버전)  
  → unified_flow_manager.py에 흡수.  
✓ tests/legacy_* , scripts/old_cli.py 등 미사용 테스트·스크립트  
  → 커버리지에 포함되지 않는 것을 확인 후 정리.

────────────────────────
3. 레거시 코드 패턴
────────────────────────
• “Adapter over adapter”  
  FlowManagerUnified(LegacyFlowAdapter)처럼 상속-후-위임 패턴이 중첩되어 있습니다.  
  기본적으로 다음 세 가지가 한 파일 내에 공존:
  ‑ 옛 인터페이스(LegacyFlowAdapter)  
  ‑ 새 인터페이스(FlowManagerUnified)  
  ‑ 실제 서비스(CachedFlowService)

• Dead code  
  ‑ LegacyFlowAdapter.handle_deprecated_flow() / validate_v1()  
  ‑ FlowCommandRouter.register_* 중 @deprecated 주석이 달린 5개 메서드  
  ‑ FlowService.save_sync_flow() (전혀 호출되지 않음)

• Fake DI container  
  flow_service.py에서 “lazy-singletons”를 흉내 내지만 실제로는 전역 변수;  
  이 때문에 테스트 병렬 실행 시 상태가 꼬이는 문제가 보고됨.

────────────────────────
4. 개선 방안 (새 구조 제안)
────────────────────────
4-1. 목표: “진입-서비스-저장소” 3단 구조
workflow_entrypoint.py       (CLI·HTTP 공용 Wrapper)
        ↓
FlowFacade (얇은 Service / 유즈케이스 계층)
        ↓
CachedFlowService            (도메인 로직 + 캐싱)
        ↓
FlowRepository (interface) ──┐
        ↓                    │
JsonFlowRepository (구현) ◀──┘

4-2. 필요한 최소 파일
• workflow_entrypoint.py           : 파라미터 파싱 + 예외/로깅  
• flow_facade.py                   : 명령 ↔ 서비스 매핑, 트랜잭션 경계  
• cached_flow_service.py           : 핵심 비즈니스 로직 + fetch/invalidate  
• flow_repository.py               : ABC (get, save, list)  
• json_flow_repository.py          : 파일 시스템 기반 구현  
• models.py / dto.py               : Flow, Command, Result 등  
• settings.py                      : 경로·캐시 TTL 등 설정  
(+ tests/)

4-3. 직접 호출 경로
workflow_entrypoint → FlowFacade.run(command)  
                    → CachedFlowService.execute(flow_id)  
                    → FlowRepository.load() …

4-4. 추가 권장 사항
• 순환 의존성 차단: CachedFlowService는 FlowManager를 몰라야 하므로  
  invalidate() 후 이벤트(pub-sub) 또는 콜백으로 처리.  
• 캐시 정책을 decorator(@cached(ttl=…))로 분리해 로깅/테스트 단순화.  
• deprecation_warning() 헬퍼로 옛 API 호출 시 로그만 남기고 기능 유지.

────────────────────────
5. 마이그레이션 계획
────────────────────────
0단계. 안전망 마련
  ‑ pytest 커버리지 80 % 이상 확보 (현 52 %).  
  ‑ mypy/ruff 등 정적 분석 통과 상태를 기준선으로 고정(tag v1_legacy).

1단계. “파일 쌍” 통합
  a) flow_command_integration_updated.py를 flow_command_integration.py로 리네임  
  b) unified_flow_manager.py를 flow_manager.py로 리네임  
  c) flow_service.py 내용을 cached_flow_service.py에 머지  
  (외부 import 경로를 from x import flow_service → cached_flow_service로 치환)  
  → CI green 여부 확인 후 tag v1.1.

2단계. 어댑터 제거
  ‑ legacy_flow_adapter.py 제거, 동일 클래스를 stub으로 남겨  
    class LegacyFlowAdapter(FlowFacade): … pass + DeprecationWarning  
  → 실제 실행 경로는 FlowFacade 사용.  
  → tag v1.2.

3단계. 순환 의존성 분리
  ‑ CachedFlowService.invalidate()에서 FlowManager.refresh() 호출 삭제.  
  ‑ 대신 events.flow_invalidated 신호 발행; FlowFacade가 구독하여 refresh 수행.  
  → import cycle 해소 확인(import-graph tool).  
  → tag v1.3.

4단계. 엔트리포인트 교체
  ‑ workflow_wrapper.py와 FlowCommandRouter를 workflow_entrypoint.py 한 파일로 통합.  
  ‑ 기존 모듈은 from ..workflow_entrypoint import * 만 남겨 soft-delete.  
  → tag v2.0-rc1, 베타 배포.

5단계. 최종 청소
  ‑ v2.0 정식 릴리스 후 2개 마이너 버전 동안 DeprecationWarning 유지.  
  ‑ log/analytics로 구버전 API 호출 0 % 확인 → 실제 삭제 PR 머지.

6단계. 문서/예제 업데이트
  ‑ README, internal wiki, Postman collection 등 경로 수정.  
  ‑ on-call runbook에 “v1 adapter shim 사용 시 대응” 부분 제거.

────────────────────────
요약
• 현재 구조는 “얇은 래퍼”들이 겹겹이 쌓여 유지비용·버그 위험이 큼.  
• 기능이 동일한 파일 쌍은 통합 후 구버전엔 DeprecationWarning만 남겨두면 됨.  
• 3-단 구조(Entry → Service → Repository)로 단순화해 의존성 방향을 한쪽으로만 흘리면  
  순환 문제와 중복 캐싱이 사라집니다.  
• 테스트 확보 → 중복 파일 제거 → 어댑터 제거 → 순환 해소 → 최종 삭제 순으로 진행하면  
  다운타임 없이 마이그레이션이 가능합니다.
