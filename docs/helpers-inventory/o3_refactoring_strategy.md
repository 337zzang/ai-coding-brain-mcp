# AI Helpers 리팩토링 전략 (o3 분석)

AI Helpers 리팩토링 전략 ‑ “한 번에 갈아엎지 말고, 안전하게 수축-확장(Constrict-Expand)”

──────────────────────────────
A. 리팩토링의 큰 그림
──────────────────────────────
1) Constrict: 중복 제거·핵심 축소  
   – 기능을 하나의 “정상 경로”로 몰아주고 불필요한 코드 경로 제거  
2) Expand: 모듈 경계를 명확히 한 뒤, 테스트·표준화·성능 최적화 등 확장

이를 4개의 단계(0~3)로 나누어 진행한다.  
모든 단계는 “테스트‧CI 통과 → 릴리즈 태그 → 다음 단계” 식의 단주기(1-2주) 스프린트로 관리한다.

──────────────────────────────
B. 단계별 구체 전략
──────────────────────────────
0단계) 사전 준비 (1주)
  · 현행 동작을 고스란히 ‘고정’시킬 E2E 테스트 스켈레톤 작성  
  · GitHub Actions(또는 기존 CI) + coverage 리포트 설치  
  · pyproject.toml 생성, Black/Isort/Fake8/MyPy (—strict) 합의

1단계) 중복 함수 통합 (2-3주)
  목표 : “한 이름-한 구현”  
  절차 :
  1. Canonical 모듈 결정  
     - parse          → code.parser.parse  
     - with_context   → flow.context.with_context  
     - decorator      → flow.context.decorator  
     - wrapper        → flow.context.wrapper  
     - record_flow_action / get_related_docs → flow.context.tracking  
     - to_dict / from_dict → domain.base_model.{to_dict, from_dict}  
     - create_flow / get_flow → flow.manager.{create, get}

  2. 각 중복 함수가 있는 모듈은  
     a) 내부 구현 삭제  
     b) from … import … as _alias 형태로 “통로”만 유지 (DeprecationWarning)  
     c) tests/legacy 경로에 호환성 테스트 추가

  3. Deprecation 정책  
     - vX.Y.Z → deprecated 경고만  
     - vX+2   → 삭제

2단계) Flow 계층 재설계 (3-4주)
  문제 : Flow/Context 모듈이 총 114개(79+35)로 과팽창
  목표 : Clean-/Hexagonal-Architecture 로 5개 서브패키지로 집약

  • 디렉터리 구조(예시)
    ai_helpers/
      flow/
        __init__.py
        core.py             # 상태·이벤트·전이 모델
        context.py          # with_context, tracker, decorator
        manager.py          # create/get/update 등 유스케이스
        repo.py             # 파일·DB 저장소 추상화
        adapters/           # 기존 legacy_adapter, cached_service 등
        plugins/            # 사용자 정의 확장 지점
      domain/
        base_model.py
        …
      infra/
        git.py, file.py, search.py …
      services/
        llm.py, project.py …
      presentation/
        cli.py, command_interface.py …
  
  • 핵심 원칙
    - flow.core 는 어떠한 IO도 직접 호출하지 않는다. (Domain Layer)
    - context.py 에 데코레이터·로깅·문맥기반 문서 추천 통합
    - adapter 는 새 repo.py 인터페이스를 구현
    - manager.py 만 public API 로 노출

  • 마이그레이션 전략
    1) flow.core + context 우선 완성 → 기존 함수들이 새 API 호출
    2) legacy_flow_adapter.py 는 adapter/legacy.py 로 이동 + deprecate
    3) circular import 방지를 위해 “상향식 의존” 금지 규칙 설정

3단계) 표준화·품질 향상 (2-3주)
  • PEP 8 + Black  → 스타일 통일  
  • Flake8 + MyPy → 정적 분석  
  • loguru or structlog → 통합 로깅  
  • Sphinx + mkdocs-material → API 문서화  
  • 패키징 : PEP 517 빌드 시스템, Semantic-Versioning

4단계) 성능·확장·위험 제거 (지속)
  • 캐시(Redis 등) → flow.repo.CacheLayer 로 옵셔널 지원  
  • 병렬/비동기 : asyncio + Trio Friendly (ask_o3_async 등)  
  • 모듈간 경량 이벤트 버스 도입으로 느슨한 결합 유지  
  • 대규모 리팩터 후 2-3주 ‘Hardening’ 기간 운영

──────────────────────────────
C. 우선순위 체크리스트
──────────────────────────────
1. (P0) E2E‧단위 테스트 확보 → 신뢰망 형성
2. (P0) 중복 제거에 필요한 공통 모듈 확정
3. (P1) flow.core / context 안정화
4. (P1) 나머지 모듈이 새 API 사용하도록 리라우팅
5. (P2) 코드 스타일·정적 검사 일괄 적용
6. (P2) 문서, 샘플, 데모 업데이트
7. (P3) 성능 최적화·플러그인 체계

──────────────────────────────
D. 예상 위험 요소 & 대응
──────────────────────────────
1) Breaking Changes  
   – 모든 삭제는 최소 1버전 전 Deprecation → 릴리즈 노트 강조

2) Legacy 코드와의 의존성 루프  
   – import-layer 규칙(Infra↘Domain 금지) + mypy-circular-checker

3) 테스트 누락으로 회귀 버그  
   – 변동 LOC 대비 커버리지 ↓   → PR 파이프라인 차단 규칙

4) 성능 회귀  
   – bench.py(airspeed-velocity) 기준선 기록 → PR마다 비교

5) 대규모 머지 충돌  
   – 단계별 작은 PR, feature-flag 브랜치 활용

6) 인적 리스크(지식 소실)  
   – ADR(Architecture Decision Record), 자동화된 코드 문서 주입

──────────────────────────────
E. 마일스톤 & 타임라인 (예시)
──────────────────────────────
• M0 (주0-1)  : CI + 테스트 스켈레톤 + 코딩 규칙  
• M1 (주2-4)  : duplicate 통합 완료, Deprecation 레이어  
• M2 (주5-8)  : flow 패키지 리디자인 & 전 모듈 마이그레이션  
• M3 (주9-11) : PEP/Black/Flake8/MyPy full pass, 문서화  
• M4 (주12+)  : 성능/플러그인/하드닝, 1.0.0 정식 릴리즈

──────────────────────────────
F. 핵심 Take-Away
──────────────────────────────
1. “한 기능-한 구현-한 진입점” 원칙이 첫걸음이다.  
2. Flow 모듈은 “Domain-Service-Adapter” 3단 분리로 재탄생시킨다.  
3. 테스트와 CI 없이는 어떤 리팩터링도 리스크 완화가 불가능하다.  
4. Deprecation → Migration → Removal 3-Step 으로 사용자 충격 최소화.