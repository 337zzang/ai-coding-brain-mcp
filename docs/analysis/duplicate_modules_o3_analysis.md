아래 내용은 현재 제공된 메타정보(파일 목록, 크기, 역할 가정)를 바탕으로 중복/경합 모듈을 정리하고, 실제 사용 확인을 위한 빠른 점검 절차와 함께 통합 방향, 단계별 마이그레이션 계획, 리스크를 담았습니다.

요약 결론
- PROJECT 계열: project.py를 메인으로 유지하되, ProjectContext는 project_context.py에서 가져와 결합. project_improved.py / project_refactored.py는 변경점만 흡수하고 제거.
- REPLACE/코드수정 계열: code.py를 public API의 단일 진입점으로 유지. replace_block_final.py, improved_insert_delete.py의 고유 동작을 code.py에 통합. integrate_replace_block.py는 얇은 래퍼로 삭제. smart_replace_ultimate.py는 구문 오류가 있으면 폐기 또는 내용만 salvage.
- FLOW 계열: flow_api.py를 퍼사드(공개 API)로 고정. ContextualFlowManager를 기본 구현으로 채택하고 UltraSimpleFlowManager는 deprecated 경로로 격리. flow_context.py의 Context/ProjectContext 정리, flow_cli.py/flow_views.py는 별도 하위 패키지로 격리.
- 최종 구조: 도메인 단일화(프로젝트, 코드편집, 플로우), 명확한 퍼사드 1개(flow_api), 내부 구현 1개(ContextualFlowManager), 컨텍스트 1개(Project/FlowContext 통합), 코드 수정 API 1개(code_ops).
- 마이그레이션: 사용현황 측정 → 공용 인터페이스 확정 → 통합 구현 → 디프리케이션 래퍼 제공 → 점진적 치환 → 제거.

1) 어떤 파일이 실제로 사용되고 있는가? 빠른 진단 절차
실제 사용여부는 코드베이스 확인이 필요합니다. 아래 순서로 30분 내 파악 가능합니다.

- __init__.py 공개 표면 조사
  - rg -n "from ai_helpers_new.* import|import ai_helpers_new" ai_helpers_new/**/__init__.py
  - 출력에서 project, code, flow_* 중 어떤 심볼을 외부로 export하는지 확인.

- 교차 참조 검색
  - rg -n "from ai_helpers_new\.(project|code|flow_.*) import|import ai_helpers_new\.(project|code|flow_.*)" -S
  - 가장 많이 참조되는 파일/함수 순으로 집계.

- 런타임 임포트 추적(빠른 훅)
  - 테스트/애플리케이션 진입점에서 다음 스니펫 추가:
    - import builtins, traceback
    - _orig_import = builtins.__import__
    - def _trace_import(name, *a, **kw):
        if name.startswith("ai_helpers_new"):
            print("[IMPORT]", name)
        return _orig_import(name, *a, **kw)
      builtins.__import__ = _trace_import
  - 실제 실행에서 로드되는 모듈만 표시.

- 호출 커버리지
  - pytest/런너에 coverage를 걸고 다음 타겟만 측정:
    - coverage run -m pytest
    - coverage html --include="*/ai_helpers_new/*"
  - 함수 단위로 사용 흔적(라인 히트) 확인.

- 함수 호출자 정적 스캔(보너스)
  - rg -n "flow_project_with_workflow\(|replace_block\(|insert_v2\(|delete_lines\("

결과 해석 가이드
- project.py의 flow_project_with_workflow를 직접 호출하는 곳이 많고, flow_* 계열에서 이를 래핑한다면 project.py가 실제 메인일 가능성 높음.
- flow_api.py는 대체로 CLI/애플리케이션의 공개 퍼사드이므로 외부 진입점일 확률이 매우 높음.
- code.py가 메인 코드 수정 모듈이라는 설명과 크기(29KB)로 볼 때, replace_block_final.py나 improved_insert_delete.py는 실험/보조 모듈일 가능성이 큼.

2) 중복 제거 우선순위
- 1순위: PROJECT 계열의 flow_project_with_workflow 중복. 동일 함수명이 3개 파일에 존재하고 project.py 내부에 get_current_project 중복 정의까지 있음.
- 2순위: REPLACE 계열의 replace/insert/delete 변형 함수. 사용자 영향도가 크고, 실수 시 파일 파손 리스크가 높음.
- 3순위: FLOW 계열의 매니저 이중화(UltraSimple vs Contextual)와 Context 이원화(flow_context.py vs project_context.py). 확장성과 유지보수에 영향.

3) 권장 최적 구조(최종 상태)
- 패키지 표면
  - ai_helpers_new/
    - project/
      - context.py  (ProjectContext, resolve_project_path, 기타 경로/프로젝트 메타)
      - service.py  (flow_project_with_workflow, get_current_project 등 프로젝트 오케스트레이션)
    - code_ops/
      - api.py      (parse, view, replace, insert, delete, replace_block 통합된 단일 API)
      - engine.py   (텍스트/블록/범위 연산 엔진 구현, 파일 I/O 안전성, 백업/트랜잭션)
    - flow/
      - api.py      (FlowAPI 퍼사드, 외부 공개)
      - manager.py  (IFlowManager 인터페이스, ContextualFlowManager 기본 구현)
      - context.py  (FlowContext + ProjectContext 합친 컨텍스트 또는 상호 참조 제거)
      - session.py, utils.py
    - cli/
      - flow_cli.py (CLI는 독립 패키지로 격리, 내부 API만 사용)
    - ui/
      - flow_views.py (UI/표시 로직은 분리, API 호출만 수행)
    - __init__.py   (공개 심볼 최소화: FlowAPI, ProjectContext, code_ops.api 주요 함수만)

- 네이밍/책임
  - 퍼사드 1개(flow/api.py), 엔진 1개(manager.py), 컨텍스트 1개(context.py), 프로젝트 오케스트레이션 1개(service.py), 코드 편집 API 1개(code_ops/api.py).
  - 파일 이름에서 역할이 명확히 드러나도록 개선.

4) 파일별 유지/통합/제거 제안
PROJECT 그룹
- 유지(핵심)
  - project.py: 주 진입점. 단, get_current_project 중복 제거, ProjectContext 의존 주입으로 결합.
  - project_context.py: ProjectContext 및 resolve_project_path 등 컨텍스트 책임 유지.
- 통합/흡수
  - project_improved.py, project_refactored.py: flow_project_with_workflow의 차이점(diff)만 project.service에 병합. 이후 Deprecated 래퍼 제공(동일 시그니처로 내부에서 service 호출, DeprecationWarning).
- 제거 후보
  - 개선/리팩토링 파일 본체는 1~2 릴리스 뒤 삭제. 사유: 동일 책임, 함수명 동일로 혼란 유발.

보존해야 할 고유 기능
- project_improved/refactored에만 있는
  - 에러 복구/재시도 로직
  - 비동기/병렬 처리 최적화
  - 로깅/Telemetry 강화
  - 경로 해석 개선(resolve_project_path 고도화)
- 모든 개선점을 project.service에 흡수하고, 단일 flow_project_with_workflow를 표준으로.

REPLACE/코드수정 그룹
- 유지(핵심)
  - code.py: 공개 API 통합. 단, 내부를 code_ops/api.py로 옮기고 기존 code.py는 thin facade로 유지하며 DeprecationWarning.
- 통합/흡수
  - replace_block_final.py: replace_block의 고급 매칭 옵션(문맥 앵커, 다중 블록, 보수적 모드 등) 흡수.
  - improved_insert_delete.py: insert_v2, delete_lines의 경계 처리/멱등성/인덱스 안정성 흡수.
- 제거 후보
  - integrate_replace_block.py: 얇은 래퍼는 code_ops.api에 직접 구현 후 삭제.
  - smart_replace_ultimate.py: 구문 오류면 즉시 제외. 다만 알고리즘 아이디어(토큰/AST 기반 치환, fuzzy 매칭)가 유일하면 테스트 케이스와 함께 engine.py에 옵션화해 흡수.
- 보존해야 할 고유 기능
  - 백업/롤백(atomic write, temp file, fsync)
  - 인코딩/개행 통합 처리(utf-8-sig, CRLF/LF, 끝줄 개행)
  - 멱등성 보장(동일 작업 반복 적용해도 안전)
  - Dry-run/diff 미리보기
  - 범위 지정 및 다중 파일 글롭 처리
  - 에러 시 부분 커밋 방지(트랜잭션)
  - 대용량 파일 성능 최적화(스트리밍/메모리 맵 옵션)

FLOW 그룹
- 유지(핵심)
  - flow_api.py: 외부에서 쓰는 퍼사드. IFlowManager에만 의존하도록 정리.
  - contextual_flow_manager.py: 기본 구현으로 채택.
  - flow_context.py: FlowContext와 ProjectContext의 중복을 해소. ProjectContext는 project/context.py에서 가져오고 FlowContext는 이를 포함/참조.
  - flow_session.py, flow_manager_utils.py: 유틸은 이름 충돌 정리.
- Deprecated/격리
  - ultra_simple_flow_manager.py: examples/ 또는 legacy/로 이동, ImportError 가이던스/DeprecationWarning.
  - simple_flow_commands.py: flow_api에서 동일 기능 제공 시 래퍼화 후 점진 폐기.
  - flow_views.py, flow_cli.py: 각각 ui/, cli/ 하위로 격리. API와 구현 분리.
- 보존해야 할 고유 기능
  - ContextualFlowManager만의 컨텍스트 인지형 의사결정 로직
  - UltraSimple에만 있던 디버그/학습용 간소 플로우는 예제로 이전

5) 리팩토링 우선순위와 단계별 계획
1단계: 가시성/사용 현황 측정(0.5~1일)
- 위의 rg/임포트 추적/커버리지로 사실관계 수집.
- 각 함수별 호출 수, 실제 배포 경로에서 사용되는 모듈 기록.

2단계: Public API 확정 및 안정화(0.5일)
- 외부 공개 표면 정하기: flow_api.FlowAPI, project.service.flow_project_with_workflow, code_ops.api의 replace/insert/delete/replace_block/parse/view.
- __init__.py에서 노출되는 심볼 최소로 통일.

3단계: 구현 통합(2~3일)
- project_improved/refactored의 개선점 diff 병합, unit test 작성.
- replace_block_final/improved_insert_delete의 동작/옵션 흡수. 공통 예외 타입 정의.
- ContextualFlowManager를 IFlowManager로 정리, flow_api는 인터페이스만 의존.

4단계: 호환 래퍼/디프리케이션(0.5일)
- 기존 모듈 경로와 함수명에 대해 동일 시그니처 래퍼 제공, 내부에서 새 API 호출.
- DeprecationWarning + 로깅 남김.

5단계: 코드모드/임포트 치환(0.5~1일)
- rg + sed 혹은 codemod로 내부 호출부를 새 API로 전환.
- 래퍼는 외부(서드파티/확장) 호환용으로만 남김.

6단계: 제거/정리(차기 릴리스)
- 사용률/로그 확인 후 legacy 모듈 제거.
- 문서/예제 업데이트.

6) 제거 가능한 파일 목록과 이유(가안)
- project_improved.py, project_refactored.py: 동일 기능의 변형. 변경점 흡수 후 제거.
- integrate_replace_block.py: 얇은 래퍼. api로 흡수.
- smart_replace_ultimate.py: 구문 오류. 유니크 알고리즘만 salvage, 본 파일 제거.
- ultra_simple_flow_manager.py: 기본 구현과 중복. legacy/examples로 이동 후 제거 예정.
- simple_flow_commands.py: flow_api로 통합되면 제거 가능.
- 주의: 제거 전 Deprecation 기간과 호환 래퍼 유지 필요.

7) 예상 위험 요소와 대응
- 미묘한 동작 차이로 인한 회귀
  - 대응: 골든 테스트(실제 리포/대상 파일 셋)로 회귀 방지. 멱등성/개행/인코딩/경계 조건 테스트 강화.
- 외부 스크립트가 특정 모듈 경로에 하드코딩
  - 대응: 동일 경로의 래퍼 + DeprecationWarning + 마이그레이션 가이드. 한 릴리스 유지.
- 병행 개발 브랜치 충돌
  - 대응: 통합 브랜치에 코드 프리즈 윈도우, 머지 전략 사전 합의.
- 성능 저하
  - 대응: 대용량 파일 벤치 전후 비교, 필요 시 옵션(스트리밍/메모리 맵) 노출.
- Windows/CRLF/UTF-8-SIG 등 환경차
  - 대응: 통합 I/O 레이어에서 개행/인코딩 표준화, 테스트 매트릭스 포함.

8) 단기 수행 체크리스트(실무용)
- rg/커버리지로 사용 모듈/함수 톱 N 확인
- project.flow_project_with_workflow와 improved/refactored diff 비교표 작성
- replace_block_final과 code.py의 replace_block 시그니처/옵션/동작 차이 정리
- insert_v2/delete_lines의 경계 케이스 테스트 작성
- ContextualFlowManager와 UltraSimple의 기능 비교표 작성
- 새 패키지 구조 디렉터리와 파일 생성, 기존 구현 단계적 이동
- Deprecation 래퍼 추가, 로깅 삽입
- codemod로 내부 임포트 경로 치환, CI/테스트 통과 확인

9) 추후 방지 가이드
- 실험/개선 버전은 feature flag나 브랜치로 유지하고, 파일명으로 변형을 중첩 생성하지 않기.
- 단일 퍼사드와 내부 구현 클래스로 아키텍처 고정.
- 변경은 RFC + 테스트 우선, 안정 표면(API) 먼저 합의.
- 중복 감지 스크립트(같은 이름 함수 AST 유사도 0.9 이상 경고) CI에 추가.

필요 시, 위 계획에 맞춘 구체적인 diff/PR 계획서와 테스트 목록(케이스명/입출력/경계조건)도 작성해 드리겠습니다. 실행 전 실제 사용현황 결과만 공유해 주시면 결정을 확정본으로 업데이트하겠습니다.