
# o3 워크플로우 문제 분석

## 질문

[상황 설명]
프로젝트: ai-coding-brain-mcp
목적: 워크플로우 시스템 리팩토링 후 전체 기능 테스트
문제: 모든 워크플로우 명령어가 "WorkflowV2가 로드되지 않았습니다" 오류 반환

[컨텍스트 제공]
현재 workflow 함수 구현 (일부):
```python
workflow 함수를 찾을 수 없음...
```

WorkflowV2 관련 코드 라인들:


테스트 결과:
- 프로젝트 전환(flow_project): ✅ 정상 작동
- /start 명령: ❌ WorkflowV2가 로드되지 않았습니다
- /task 명령: ❌ WorkflowV2가 로드되지 않았습니다
- /status 명령: ❌ WorkflowV2가 로드되지 않았습니다

시도한 방법:
1. helpers.workflow("/start ...") 직접 호출
2. 프로젝트 전환 후 재시도

제약 조건:
- 기존 helpers 구조 유지
- 세션 간 상태 유지 필요
- 백워드 호환성 유지

[구체적 요청]
1. WorkflowV2가 로드되지 않는 근본 원인 분석
2. WorkflowV2를 올바르게 초기화하는 방법
3. 현재 구조에서 최소한의 수정으로 해결하는 방법
4. 테스트를 위한 임시 해결책
5. 장기적인 개선 방향


## 답변
아래 내용은 현재 남아있는 코드 조각이 거의 없다는 점(helpers.workflow 내부, WorkflowV2 선언부 등 미제공)을 감안하여  
“가장 빈번하게 발생하는 패턴”을 기준으로 정리-제안한 것입니다.  
핵심은 ❶ 전역(또는 세션) 단일 인스턴스가 더 이상 만들어지지 않는다는 것이고, ❷ 명령 라우터가 그 인스턴스를 찾지 못해 `"WorkflowV2가 로드되지 않았습니다"` 예외를 던진다는 것입니다.

────────────────────────────────────────
1. 근본 원인(Root Cause)  
────────────────────────────────────────
• 초기화 사이드-이펙트 제거  
  ‑ 리팩터링 과정에서 `helpers`(혹은 `__init__.py`)가 import 될 때 자동으로  
    `WorkflowV2()`를 만들어 `_workflow_v2`(전역)이나 `app.state` 등에 넣던 코드가 빠졌습니다.  
  ‑ 따라서 `/start, /task, /status …` 모두 helpers.workflow → `_workflow_v2`를  
    찾지만 None → “로드되지 않음” 오류.

• 프로젝트 전환(flow_project)와 WorkflowV2 생성이 분리됨  
  ‑ 예전에는 `flow_project()`가 성공적으로 끝나면 내부에서  
    `WorkflowV2(config_of_project)`를 즉시 만들어 주었을 가능성이 큽니다.  
  ‑ 현재는 프로젝트 디렉터리만 바꾸고, 워크플로우 생성 트리거가 사라짐.

• 호환성 마커가 변경됨  
  ‑ helpers.workflow 내부가 “v1 → v2 브리지” 역할을 할 때,  
    `if _workflow_v2 is None: raise…` 형태가 남아 있어 오류 메시지를 그대로 출력.

────────────────────────────────────────
2. WorkflowV2를 올바르게 초기화하는 방법  
────────────────────────────────────────
(1) “지연 로딩(Lazy-loading) 싱글톤”으로 복원  
  helpers.py (또는 helpers/workflow.py)에 다음 가드를 삽입:

```python
# helpers.py
from workflows.v2.core import WorkflowV2          # 실제 위치에 맞게 수정
from .session import load_session_state           # 세션 복원 util (예시)

_workflow_v2: "WorkflowV2|None" = None            # 전역 캐시

def _ensure_wf_v2() -> "WorkflowV2":
    """필요하면 즉시 생성, 이미 있으면 그대로 리턴."""
    global _workflow_v2
    if _workflow_v2 is None:
        _workflow_v2 = WorkflowV2()
        # 세션/프로젝트 상태 복구(선택)
        _workflow_v2.restore(load_session_state())
    return _workflow_v2
```

(2) helpers.workflow 진입점 수정 (최소 변경)  
```python
def workflow(cmd: str, *args, **kwargs):
    wf = _ensure_wf_v2()
    return wf.dispatch(cmd, *args, **kwargs)
```

(3) 프로젝트 전환 훅 추가(선택)  
```python
def flow_project(path: str):
    _switch_project_dir(path)
    # 새 프로젝트라면 세션 초기화
    _ensure_wf_v2().reload_config(path)
```

위 세 줄만으로도 모든 `/start /task /status` 명령이 다시 동작합니다.

────────────────────────────────────────
3. “현재 구조”에서 최소-수정(Minimum patch) 시나리오  
────────────────────────────────────────
A. helpers 모듈만 수정  
  ‑ 위 10~15줄 추가로 끝.  
  ‑ 외부 API 시그니처/모듈 트리 일절 변동 없음 → 백워드 호환 만족.  
  ‑ 세션 전역 `_workflow_v2` 하나로 유지 → 다중 명령어 간 상태 보존.

B. 아무것도 건드리기 어려운 상황이라면  
  ‑ 프로젝트 시작 스크립트(main.py 등) 가장 위에  

    ```python
    import helpers; helpers.workflow("")  # 빈 호출로 강제 초기화
    ```

  ‑ 단, 장기적으로는 바람직하지 않음.

────────────────────────────────────────
4. 테스트 단계용 임시 해결책  
────────────────────────────────────────
pytest / unittest 기준 예시:

```python
# conftest.py
import pytest, helpers

@pytest.fixture(autouse=True, scope="session")
def init_workflow_v2():
    helpers._ensure_wf_v2()        # lazy-loader 직접 호출
```

또는 단순 스크립트 테스트라면 맨 앞에

```python
import helpers
helpers._ensure_wf_v2()
```

만 넣어주면 `"로드되지 않았습니다"` 메시지는 더 이상 나오지 않습니다.

────────────────────────────────────────
5. 장기적 개선 제안  
────────────────────────────────────────
• 명시적 “앱 라이프사이클” 도입  
  ‑ FastAPI/Flask라면 `startup` 이벤트, CLI라면 `main()` 시작 시점에  
    `WorkflowManager.init()` 을 호출하도록 패턴화(Dependency Injection).

• 전역 싱글톤 제거 → DI Container/Service Locator  
  ‑ helpers.workflow 대신 `get_workflow()` 에 컨테이너 주입.  
  ‑ 테스트 시 fixture 로 쉽게 갈아끼울 수 있어 Mocking 이 편해집니다.

• 버전 추상층 마련  
  ‑ `IWorkflow` 프로토콜(ABC) + `WorkflowV1, WorkflowV2` 구현체 등록.  
  ‑ `WorkflowRegistry.get(version="v2")` 로 분기 → 추후 V3도 손쉽게.

• 상태 영속화 모듈화  
  ‑ 현재 세션 pickling/pickle-json이 helpers 안에 섞여 있다면  
    `state_store.py` 로 분리 → hot-reload 시에도 세션 유실 감소.

• CI 체크리스트에 “/start-/status smoke test” 추가  
  ‑ 초기화 유무를 가장 먼저 잡아주므로 이번과 같은 사고 재발 방지.

이상과 같이 적용하시면 “백워드 호환 + 세션 유지 + 최소 코드 변경” 요건을 만족하면서  
전 프로젝트 명령어가 다시 정상 동작할 것입니다.

## 메타 정보
- 추론 시간: 70.87초
- 토큰 사용: 2687
- 분석 시각: 2025-07-18 23:38:47.598353
