# AI Helpers 전체 구조 개선안

## O3 분석 결과

아래 제안은 223 개의 함수/클래스를 가진 “AI Helpers” 코드를 전면적으로 정리하면서도, 단계적으로 적용할 수 있도록 설계되었습니다.  

────────────────────  
1. 모듈 구조 최적화 (디렉터리/패키지 리팩터링)  
────────────────────
권장 구조 (PEP 420 네임스페이스 패키지 사용 가능):

ai_helpers/                     # 배포 단위 (pip install ai-helpers)
│
├─ core/                        # 순수 로직 ‑ 재사용·테스트 용이
│   ├─ fs.py                   # 기존 file.py ⇒ 입출력·OS 의존
│   ├─ code.py                 # 코드 파싱/리팩터링
│   ├─ search.py               # 텍스트·코드 검색
│   ├─ git.py                  # Git low-level 래퍼
│   └─ __init__.py             # public symbol export
│
├─ services/                    # 외부 시스템, 고수준 비즈니스 규칙
│   ├─ llm_service.py          # LLM (provider adapter + 캐시)
│   ├─ project_service.py      # 프로젝트 스캐닝, 빌드 파이프라인
│   └─ __init__.py
│
├─ workflows/                   # Flow/Orchestration 레벨
│   ├─ ultra_simple_flow.py    # ultra_simple_flow_manager.py 리네임
│   └─ __init__.py
│
├─ facade.py                    # 단일 진입점 (Facade 패턴) ★
│
├─ wrappers.py                  # 응답/로거/트레이싱 데코레이터 모음
├─ cache.py                     # 캐싱 전략 구현 (disk, memory, TTL)
├─ exceptions.py                # 커스텀 예외 계층
├─ config.py                    # 환경변수·설정 로딩
├─ utils/                       # 범용 툴
│   ├─ decorators.py           # 타입-안전 데코레이터
│   ├─ concurrency.py          # async, ThreadPool 공통 헬퍼
│   └─ logging.py              # 구조적 로그 (json-logger 등)
└─ tests/                       # pytest 패키지 / fixtures / e2e

장점  
• “core ⇢ services ⇢ workflows” 계층이 명확해져 내부 변경이 외부 호출부에 전파되지 않음.  
• facade.py 가 모든 외부 API 를 노출 ‑ 모듈 전개(Dependency Graph)가 단순해짐.  
• utils 와 core 가 순환참조 없이 평면적으로 분리.

────────────────────
2. 네이밍 컨벤션 통일 (snake_case)  
────────────────────
규칙  
• 함수/변수/모듈 ⇒ snake_case (PEP 8).  
• 클래스 ⇒ PascalCase.  
• 상수 ⇒ UPPER_SNAKE_CASE.  

적용 절차  
① ruff, black, isort, pep8-naming 플러그인을 pyproject.toml 에 선언.  
② “실제 이름 ↔ 문서” 동시 치환을 위해 bowler/refactor 또는 rope로 일괄 리네임 (CI 통합).  
③ deprecated 경로는 facade.py 에서 shim export + DeprecationWarning 으로 1~2 버전 유지.  

────────────────────
3. 중복 함수 통합 전략  
────────────────────
1) 탐지  
   • vulture or pylint-duplicate-code → 유사 함수 후보 수집  
   • 튀는 시그니처는 pygrep + difflib 활용  

2) 정리 가이드  
   • “core” 계층에 canonical API 단일화  
   • 논리적으로 완전히 동일 → 직접 삭제  
   • 부분 중복 → 공통 로직을 private _helper(…)로 분리 후 public API 둘 다 호출 (점진적 이주).  

3) 릴리즈 노트  
   • semver 기준 minor ↑, Deprecated list 자동 생성 스크립트.  

────────────────────
4. 에러 처리 표준화  
────────────────────
1) 예외 계층 (exceptions.py)

class AIHelpersError(Exception): ...
class FileSystemError(AIHelpersError): ...
class GitError(AIHelpersError): ...
class LLMError(AIHelpersError): ...
class ValidationError(AIHelpersError): ...

2) wrappers.wrap_output 개선

from typing import TypeVar, Callable, ParamSpec, Generic, Dict, Any
P = ParamSpec("P")
T = TypeVar("T")

def wrap_output(func: Callable[P, T]) -> Callable[P, Dict[str, Any]]:
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs):
        try:
            result: T = func(*args, **kwargs)
            if isinstance(result, dict) and result.get("ok") is not None:
                return result
            return {"ok": True, "data": result, "error": None}
        except AIHelpersError as e:
            logging.error("AIHelpersError", exc_info=e)
            return {"ok": False, "error": str(e), "data": None}
        except Exception as e:   # 미분류 예외
            logging.exception("Unhandled error")
            return {"ok": False, "error": "UnhandledError: " + str(e), "data": None}
    return wrapper

• 모든 public API (facade.py) 에 @wrap_output 적용 → 일관된 반환.  
• 내부 로직은 예외를 자유롭게 throw; 호출부는 wrapper 가 전환.

────────────────────
5. 성능 최적화 포인트  
────────────────────
① I/O 병목  
   • core.fs.scan_directory → asyncio + aiopath or anyio (CPU-bound walk 는 ThreadPool)  
   • git 명령 다중 호출 → dulwich 라이브러리로 로컬 파싱 or ‑-batch 변경  

② 캐싱  
   • llm_service.get_completion(prompt, **kw)  
     - prompt hash + model + kwargs 기준으로 diskcache/redis TTLCache  
     - 결과 1 시간 유지, hit 률 기록 → prometheus metrics.  
   • search.index_directory 결과 역시 LRU 캐시  

③ 비용이 큰 정규식 / AST 연산  
   • py_gtrie or ahocorasick index → O(N) 스캔 감축  
   • 멀티-코어 병렬화: concurrent.futures.ProcessPoolExecutor(auto chunk size)  

④ 로깅  
   • json-logger + lazy formatting (%s 대신 %s) => CPU 낭비 최소화.  

────────────────────
6. 테스트 커버리지 향상 방안  
────────────────────
• pytest + pytest-cov 목표 90 %  
• 구분
  1. 유닛: core.*  (pure function)  
  2. 서비스: llm mocking (vcrpy · responses)  
  3. e2e: facade.* 호출 → 샘플 리포지토리 FIXTURE  
• Hypothesis(quickcheck)로 fs.search 경계값 Random 테스트  
• Mutation testing: mutmut 또는 cosmic-ray 로 “죽지 않는 코드” 탐지  
• CI : GitHub Actions / pre-commit (black, isort, ruff, mypy, pytest -q)  

────────────────────
7. Facade 예시 코드 (facade.py)  
────────────────────
from .wrappers import wrap_output
from .core.fs import scan_directory
from .services.llm_service import get_completion

@wrap_output
def list_files(path: str, *, ignore: list[str] | None = None):
    return scan_directory(path, ignore=ignore)

@wrap_output
def ask_llm(prompt: str, **kwargs):
    return get_completion(prompt, **kwargs)

__all__ = ["list_files", "ask_llm"]

────────────────────
8. 단계별 마이그레이션 로드맵  
────────────────────
Step 0  (1 주)  
• 패키지 skeleton 생성, 기존 코드 이동, 기존 import 경로 shim 제공  

Step 1  (2 주)  
• ruff/black 적용, 네이밍 일괄변경, 예외 계층 도입  

Step 2  (2-3 주)  
• 중복 함수 제거, unit test 보강, 70 % 커버리지 달성  

Step 3  (1 주)  
• 캐시·async 도입 (fs, git, llm) → 벤치마크로 회귀 검증  

Step 4  (1 주)  
• 문서 재생성 (mkdocs + mkdocstrings), API reference 자동화  

Step 5  (지속)  
• mutation-testing / 릴리즈 자동화 (semver + changelog)  

────────────────────
요약  
• “core → services → workflows → facade” 4 계층으로 복잡도 은닉.  
• snake_case + 커스텀 예외 + wrap_output 데코레이터로 외부 계약 통일.  
• LRU/TTL 캐싱·비동기 I/O · 멀티프로세싱으로 성능 향상.  
• ruff/pytest/hypothesis 로 품질·테스트 커버리지 강화.  

위 계획을 따라가면, 코드 가독성과 유지비용이 크게 줄고, 신규 기능(추가 LLM provider, 확장 workflow) 도입이 훨씬 수월해집니다.

## 메타 정보
- Reasoning Effort: high
- Usage: {'prompt_tokens': 501, 'completion_tokens': 3003, 'total_tokens': 3504, 'reasoning_tokens': 0}
