# O3 리팩토링 분석 보고서 (전체)

생성일: 2025-08-09 22:49:53
Task ID: o3_task_0001

## O3 분석 결과

다음은 현재 정보를 바탕으로 한, 안전하고 실행 가능한 Python 리팩토링 단계 계획입니다. 목표는 87개 파일을 약 25개로 줄이되, 기능을 안정적으로 유지하고 중복/의존성 문제를 제거하는 것입니다.

1) 최종 구조(안)과 보존/통합 방침
- 유지(핵심 API)
  - __init__.py: 외부에는 facade_safe만 노출
  - facade_safe.py: Facade 패턴의 유일한 엔트리 포인트
  - flow_api.py: 플로우 정의/실행 API
  - ultra_simple_flow_manager.py: 플로우 실행기(오케스트레이터)
  - file.py, code.py, search.py, git.py, llm.py: 인프라 모듈
  - domain/, repository/, service/: 비즈니스 계층
- 삭제/통합
  - search_improved*.py(6개) → search.py에 흡수
  - facade.py, facade_minimal.py → facade_safe.py로 통합
  - flow_cli.py, flow_context.py, 기타 flow_* → flow_api.py(+ ultra_simple_flow_manager.py)로 흡수
  - replace_block_final.py 등 code 조작 유틸 → code.py로 흡수
- 임시 호환 레이어(삭제 전 단계)
  - 삭제 예정 파일들은 동일 모듈명에 re-export + DeprecationWarning만 남김
    - 예: search_improved_v2.py → “from .search import *; import warnings; warnings.warn('deprecated', DeprecationWarning, stacklevel=2)”
- 레이어드 아키텍처 규칙(순환 방지)
  - core(infra): file, code, search, git, llm
  - domain → service → facade_safe → flow_api/ultra_simple_flow_manager
  - 규칙: core는 domain/service/facade/flow를 import하지 않는다. flow는 facade를 사용할 수 있지만, facade가 flow를 import해서는 안 된다.

2) 안전성: import 관계 파괴 위험과 대응
- 주요 위험
  - 기존 경로를 import하는 코드가 많을 가능성
  - flow와 facade 사이, service와 core 사이의 교차 import로 인한 순환 참조
  - __init__.py가 과도하게 심볼을 노출하거나 import 시점 부작용
- 대응
  - 1차로 모든 삭제 대상 파일을 “deprecation re-export 모듈”로 변환해 외부 import를 깨지 않음
  - 순환 우려 지점에선
    - 타입 전용 import는 from typing import TYPE_CHECKING 뒤에서 처리
    - 지연 import(함수 내부 import)로 사이클 절단
    - 교차 참조되는 데이터 구조는 domain/types.py(또는 flow_api 내부 types)로 단일화
  - __init__.py는 facade_safe만 노출. 다른 모듈을 상단에서 import하지 않음

3) 통합 방법: flow 관련 9개 파일
- 목표: flow_api.py를 플로우 정의/조립/실행의 단일 진입점으로, ultra_simple_flow_manager.py를 실제 실행기로.
- 표준화할 핵심 개념
  - Flow: Step의 시퀀스(또는 DAG). id, name, steps, on_error 정책 등
  - Step: name, action(callable 또는 enum+디스패치), inputs/outputs, retry/backoff 옵션
  - Context(기존 flow_context 기능): run_id, variables(dict), artifacts(paths), logger. flow_api 내부에서 경량 구현
  - FlowResult/StepResult: status(success/fail/skip), outputs, logs, timings
- 통합 절차
  - flow_context.py → flow_api.Context로 흡수
  - flow_cli.py 기능(파라미터 파싱, run 명령)은 유지 필요 시 별도 CLI 진입점으로 분리하거나, 최소한 flow_api.run(flow, ctx) 호출만 남기고 CLI는 프로젝트 외부 스크립트로 이동
  - 기타 flow_* 유틸 함수는 flow_api의 내부 헬퍼 또는 ultra_simple_flow_manager로 이전
  - flow_api는 다음만 노출: define_flow(...), run_flow(flow, context=None), Step/Flow/Context/Result 클래스. 실행 로직은 ultra_simple_flow_manager에 위임
  - ultra_simple_flow_manager는 run(step|flow, ctx)와 hooks(before_step, after_step)만 유지
  - 기존 flow_* 모듈들은 모두 re-export + DeprecationWarning만 남김

4) 우선순위와 단계별 실행 계획
0. 프리플라이트(0.5일)
   - Python 버전 고정, 포매터/린터/타입체커 도입: black(or ruff format), ruff, mypy
   - CI에서 pytest + coverage 세팅. cloc로 파일 수 기준선 기록
   - import 그래프와 사이클 파악: pydeps ai_helpers_new --show-cycles 또는 grimp/import-linter 사용
   - 현재 동작 스냅샷 테스트 추가(최소): facade_safe의 대표 public API, flow 실행 스모크, search 기본 케이스

1. 호환 레이어 적용(1일)
   - 삭제 예정 파일을 모두 re-export 모듈로 변경
     - search_improved*.py → from .search import *
     - facade.py, facade_minimal.py → from .facade_safe import *
     - flow_cli.py, flow_context.py 및 기타 → from .flow_api import *
     - replace_block_final.py → from .code import *
     - 각 파일 첫 줄에 DeprecationWarning 발행
   - 이 단계에서 외부 import는 깨지지 않음. CI 통과 확인

2. search 통합(0.5~1일)
   - search_improved*의 기능/시그니처 비교 → search.py에 상위 호환 API로 흡수
   - 중복 알고리즘은 옵션 플래그나 전략 파라미터로 통합
   - 모든 내부 호출부를 search.py API로 교체
   - 단위 테스트: 개선 전/후 결과 동등성 A/B 테스트(샘플 입력 셋), 경계 케이스(0개 결과, 대용량 텍스트)

3. facade 통합(0.5일)
   - facade_safe를 유일한 Facade로 확정
   - 내부 참조에서 facade.py, facade_minimal.py를 사용 중이면 일괄 교체 → facade_safe로
   - facade 전용 통합 테스트: 대표 공개 메서드가 기존과 동일하게 동작하는지 확인

4. flow 통합(1.5~3일)
   - flow_api에 Flow/Step/Context/Result 표준 타입 정의
   - ultra_simple_flow_manager를 실행 엔진으로 단순화(실행/훅/에러정책/리트라이)
   - flow_context, flow_cli, 기타 flow_*의 로직을 flow_api 또는 ultra_simple_flow_manager로 이관
   - 기존 flow_* 모듈들은 re-export만 유지
   - 순환 참조 처리: flow는 facade_safe만 참조하고, facade_safe는 flow를 참조하지 않도록 정리
   - 통합 테스트: 대표 플로우 2~3개를 end-to-end로 실행. 실패/리트라이/중단 시나리오 포함

5. code 유틸 통합(0.5~1일)
   - replace_block_final.py 및 변형 로직을 code.py로 흡수
   - 호출부 모두 code.py API로 교체
   - 단위 테스트: 코드 조각 치환, 경계(중복 패턴/멀티라인/UTF-8), idempotency

6. 정리 및 경량화(0.5~1일)
   - dead code 탐지(vulture), 중복 코드 검사(ruff SIM/PLR, radon cc)
   - 불필요 import/유틸 제거, 모듈 상단 부작용 제거
   - ai_helpers_new/__init__.py는 facade_safe만 노출 확인
   - import-linter로 아키텍처 규칙 추가(레이어 규칙, no-cycles)

7. 호환 레이어 제거(0.5일)
   - 사용처 검색하여 더 이상 옛 경로를 쓰지 않는지 확인(grep -R)
   - re-export 모듈 제거. 파일 수 최종 감축
   - Semver 기준 마이너/메이저 릴리스로 커뮤니케이션

5) 위험 요소와 대응
- 순환 참조
  - 가장 흔한 사이클: flow ↔ facade, service ↔ core
  - 해결책: 타입은 TYPE_CHECKING 블록에서만 import, 런타임 참조는 문자열 타입 힌트 또는 Protocol 사용
  - 실행 의존은 의존 방향을 단방향으로 강제(flow → facade, service → core)
- 내부 모듈 이름 충돌/함수 시그니처 상이
  - 통합 전에 공용 API를 명확히 정의하고, 구버전 시그니처는 어댑터로 흡수(인자 기본값/kwargs 흡수)
- import 시 부작용
  - 상단 실행 로직 제거(환경변수 읽기/네트워크 호출 금지), 팩토리 함수 내부로 이동
- 성능/메모리 회귀
  - importtime, 실행 시간 측정(baseline 대비), 큰 데이터 로딩 지연화

6) 테스트 전략(단계별)
- 공통
  - pytest + coverage, 최소 70% 목표(핵심 경로 우선)
  - 외부 의존성 격리: llm.py, git.py는 인터페이스화/주입. 테스트에서 fake/stub 사용
- 1단계(호환 레이어)
  - 모듈 import 스모크 테스트: 삭제 예정 경로로도 import 성공해야 함 + DeprecationWarning 캡처
- 2단계(search)
  - 동일 입력셋에 대해 search_improved* vs search 결과 동등성 비교(A/B 테스트)
  - 성능 회귀 없는지 간단 벤치(샘플 100건, 시간 측정)
- 3단계(facade)
  - 퍼블릭 API 계약 테스트(입력/출력 타입, 예외, 부수효과)
- 4단계(flow)
  - 통합(E2E) 시나리오: 정상 플로우, 중간 실패 후 재시도, 중단/롤백
  - 단위: Step/Context 직동작, 훅(before/after), 에러정책
- 5단계(code)
  - 텍스트 변환 골든 테스트(입력→출력 고정), 다국어/인코딩/멀티라인
- 회귀 방지
  - import-linter로 no-cycles와 레이어 규칙 강제
  - CI에서 deprecation warning을 허용하되 기록. 제거 단계에서 경고가 0이 되는지 확인

7) 구체 작업 예시 체크리스트
- 임시 호환 모듈 생성
  - search_improved*.py: from .search import * + DeprecationWarning
  - facade.py, facade_minimal.py: from .facade_safe import * + DeprecationWarning
  - flow_cli.py, flow_context.py: from .flow_api import * + DeprecationWarning
  - replace_block_final.py: from .code import * + DeprecationWarning
- flow_api 표준화
  - 제공: Step, Flow, Context, StepResult, FlowResult
  - 함수: define_flow(steps, ...), run_flow(flow, context=None)
  - ultra_simple_flow_manager.run(step|flow, ctx)로 실제 실행 위임
- __init__.py
  - 외부 노출 최소화: from .facade_safe import Facade(또는 필요한 공개 심볼만)
- 아키텍처 린팅(import-linter 예)
  - Layers: core -> service -> facade -> flow, domain은 독립적으로 service/facade가 import
  - Contracts: forbid cyc import between any layers

8) 성공 기준과 종료
- 파일 수 25±2, 중복 모듈 제거
- import-linter no cycles
- CI green, 커버리지 기준선 유지/상승
- Deprecation 경로 제거 전후 모두 배포 태그 기록
- 간단한 성능 스모크(대표 플로우 실행 시간 ±10% 이내)

권장 일정(참고)
- 0~1일: 프리플라이트/호환 레이어
- 1~2일: search/facade 통합
- 2~4일: flow 통합
- 4~5일: code 통합/정리
- 5일차: 호환 레이어 제거 및 마감

요약
- 먼저 “깨지지 않는” 호환 레이어를 깐 뒤, search → facade → flow → code 순으로 통합합니다.
- 레이어 규칙을 설정해 순환을 원천 차단하고, 타입 전용 import와 지연 import로 남은 사이클을 절단합니다.
- 각 단계마다 A/B 테스트와 스모크/통합 테스트로 회귀를 잡고, 마지막에 호환 레이어를 제거합니다.

## 실행 권장사항

Based on O3 analysis, 다음 순서로 진행:
1. 백업 필수
2. 브랜치에서 작업
3. 단계별 테스트
4. 점진적 통합
