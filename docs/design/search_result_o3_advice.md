# SearchResult 타입 문제 해결 방안 - o3 조언

## 질문

[상황 설명]
프로젝트: ai-coding-brain-mcp
문제: search_code 함수의 반환 타입 불일치로 인한 AttributeError 발생
목적: 일관된 SearchResult 타입 시스템 구축

[컨텍스트 제공]
현재 search_code 구현:
---
def search_code(base_path: str, pattern: str, file_pattern: str = "*", 
                case_sensitive: bool = False, max_results: int = 100) -> List[Dict[str, Any]]:
    results = []
    # ... 검색 로직 ...
    results.append({
        'file': relative_path,
        'line_number': line_number,
        'line': line.rstrip(),
        'context': context_lines
    })
    return results  # 단순 리스트 반환
---

사용 코드에서의 기대:
---
result = helpers.search_code(".", "pattern", "*.py")
# 다음과 같은 사용을 기대
if result.count > 0:  # AttributeError: 'list' has no attribute 'count'
    for file, matches in result.by_file().items():  # AttributeError
        print(f"{file}: {len(matches)} matches")
---

현재 상황:
- search_code는 List[Dict]를 반환
- 사용자는 SearchResult 객체(count 속성, by_file() 메서드 등)를 기대
- SearchResult 클래스가 정의되어 있지 않음
- safe_search_code 메서드도 구현되지 않음

문서화된 인터페이스:
- result.count: 총 매치 수
- result.by_file(): 파일별로 그룹화된 결과
- result.files(): 매치가 있는 파일 목록

[구체적 요청]
1. SearchResult 클래스 설계 방안
2. 기존 코드와의 호환성 유지 방법
3. 점진적 마이그레이션 전략
4. 타입 안정성 보장 방법
5. 성능 고려사항
6. 테스트 전략

특히 다음 사항에 대한 조언:
- 기존 리스트 반환과 새 객체 반환의 공존 방법
- Python의 덕 타이핑을 활용한 호환성 레이어
- 명확한 타입 힌트 제공 방법
- 헬퍼 함수들 간의 일관성 확보


## o3의 답변
아래 내용은 “ai-coding-brain-mcp” 프로젝트에서 search_code 의 반환 타입을 List → SearchResult 로 바꾸면서도
기존 호출부를 최대한 깨뜨리지 않는 방법을 정리한 것입니다.  
(예시는 Python 3.9+ 기준)

────────────────────────────────────────────
1. SearchResult 클래스 설계
────────────────────────────────────────────
필수 기능
• list 처럼 순회·슬라이싱 가능  
• result.count, result.by_file(), result.files() 제공  
• 타입 힌트와 IDE 지원  
• 필요 시 지연(lazy) 계산, 캐싱

구체적 설계 예

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Generic, TypeVar

Match = Dict[str, Any]          # 검색 1건
T = TypeVar("T", bound=Match)

class SearchResult(List[T]):    # list 를 상속하면 “기존 for x in result:” 그대로 동작
    """
    List[T]를 상속해 기본 list 행동을 그대로 가지면서
    count / by_file / files 같은 헬퍼를 추가한다.
    """

    # ────────── 생성 ──────────
    def __init__(self, matches: Iterable[T] | None = None) -> None:
        super().__init__(matches or [])

        # _by_file 는 실제로 요청될 때 한 번만 계산
        self._by_file_cache: Dict[str, List[T]] | None = None

    # ────────── 핵심 API ──────────
    @property
    def count(self) -> int:
        return len(self)

    def by_file(self, refresh: bool = False) -> Dict[str, List[T]]:
        if self._by_file_cache is None or refresh:
            groups: Dict[str, List[T]] = defaultdict(list)
            for m in self:
                groups[m["file"]].append(m)
            self._by_file_cache = dict(groups)
        return self._by_file_cache      # 캐시 반환

    def files(self) -> List[str]:
        return list(self.by_file().keys())

    # ────────── 표현/디버그 ──────────
    def __repr__(self) -> str:                         # 보기 좋게 출력
        return f"<SearchResult {self.count} matches in {len(self.files())} files>"

주요 포인트
• list를 상속했으므로 기존  
    for m in result: …  
  또는 len(result) 는 그대로 된다.  
• by_file / files 는 내부 캐시를 사용해 O(1) 재호출.  
• 필요한 경우 append, extend 등 list 메서드도 그대로 사용 가능.

────────────────────────────────────────────
2. 기존 코드와의 호환성 유지
────────────────────────────────────────────
(1) search_code 시그니처 확장

from typing import Union

def search_code(
        base_path: str,
        pattern: str,
        file_pattern: str = "*",
        case_sensitive: bool = False,
        max_results: int = 100,
        *,
        as_object: bool = True      # 디폴트=새로운 방식
) -> Union[List[Match], SearchResult]:
    raw: List[Match] = []

    …  # 기존 검색 로직

    return SearchResult(raw) if as_object else raw

(2) 완전히 호환이 필요한 경우

def safe_search_code(*args, **kwargs) -> SearchResult:
    """
    오래된 호출부가 helpers.safe_search_code 를 임포트하도록 가이드.
    내부적으로 search_code(..., as_object=True) 를 호출해 항상 SearchResult를 보장.
    """
    kwargs["as_object"] = True
    return search_code(*args, **kwargs)

(3) Deprecation 경로
• search_code(as_object=False) 사용 시 warnings.warn 로 경고
• 문서에 “vX.Y 에서 as_object 인자 제거 예정” 안내

────────────────────────────────────────────
3. 점진적 마이그레이션 전략
────────────────────────────────────────────
1단계 – 추가  
    • SearchResult 구현 + as_object 파라미터 추가  
    • 기존 테스트 전혀 수정 안 해도 통과해야 함.  

2단계 – 래퍼 도입  
    • safe_search_code 를 새로운 호출부에 사용하도록 PR 분할.  

3단계 – 호출부 업데이트  
    • 프로젝트 전역에서 helpers.search_code → helpers.safe_search_code 교체  
    • 패턴: result = helpers.safe_search_code(…)  

4단계 – 디프리케이트  
    • search_code(as_object=False) 호출 시 DeprecationWarning  

5단계 – 제거  
    • 메이저 버전 업 시 as_object 제거, search_code 가 SearchResult 만 반환.  

────────────────────────────────────────────
4. 타입 안정성 보장
────────────────────────────────────────────
• typing alias Match = Dict[str, Any] 로 검색 결과 한 건을 명시.  
• SearchResult(List[Match]) 로 제네릭 구현해 IDE 에 list 행동 및
  추가 메서드 모두 노출.  
• as_object 파라미터 반환 타입을 Union[ List[Match], SearchResult ] 로
  명시해 컴파일러(mypy/pyright) 경고 최소화.  
• 팀 내 mypy strict 옵션 (―strict 또는 ―disallow-untyped-calls 등) 활성화 권장.

────────────────────────────────────────────
5. 성능 고려 사항
────────────────────────────────────────────
• by_file, files 계산은 호출 시점까지 미룬 뒤 결과를 인스턴스 변수에 캐시.  
  대규모 결과셋에서도 한 번만 groupby 실행.  
• SearchResult 가 list 를 상속하므로 추가적인 메모리 오버헤드는
  (소규모 인스턴스 변수를 제외하면) 거의 없음.  
• 검색 자체가 I/O bound 이므로 SearchResult 변환 비용은 무시 가능.  
• 아주 큰 결과(수십만 건) 처리 시 lazy generator 버전
  (e.g., search_code_iter) 도 별도 제공 고려.

────────────────────────────────────────────
6. 테스트 전략
────────────────────────────────────────────
단위 테스트
• search_code(as_object=True) → isinstance(res, SearchResult)  
• len(res) == res.count  
• set(res.files()) == set(res.by_file().keys())  
• res.by_file()[some_file][0]["line_number"] == … 기대값  

호환성 회귀 테스트
• search_code(as_object=False) 가 List 반환하는지 확인  
• 기존 로직 (for m in search_code(..., as_object=False)) 문제없이 통과  

속도/부하 테스트
• 10만 라인 / 1만 매치 데이터셋에서 search_code 수행 시간 측정  
• by_file 첫 호출 시점과 두 번째 호출 시점 성능 비교  
  (두 번째 호출은 캐시로 100µs 이하)  

통합 테스트
• 실제 리포 디렉터리에서 helpers.safe_search_code 로 검색 → 예상 출력 비교.  

────────────────────────────────────────────
요약
• SearchResult 를 list 를 상속한 경량 래퍼로 설계하면
  기존 list-like 사용 코드는 그대로, 새 코드에는 풍부한 API 제공.  
• search_code() 는 as_object 플래그로 두 가지 타입을 모두 지원하며
  권장 경로(safe_search_code) 를 통해 점진적 이전.  
• 타입 힌트, DeprecationWarning, 캐싱, 단위·통합 테스트를 통해
  안정성과 성능을 모두 확보할 수 있다.

## 메타 정보
- 추론 시간: 42.22초
- 토큰 사용: 2954
