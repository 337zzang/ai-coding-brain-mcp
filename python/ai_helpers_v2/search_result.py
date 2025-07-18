"""
SearchResult 클래스 - 검색 결과를 관리하는 향상된 인터페이스
"""
from typing import List, Dict, Any, Iterator, Optional
from collections import defaultdict


class SearchResult:
    """검색 결과를 관리하는 클래스

    리스트와 유사하게 동작하면서 추가 기능 제공
    """

    def __init__(self, results: List[Dict[str, Any]] = None):
        self._results = results or []
        self._by_file_cache = None

    # 리스트처럼 동작하게 하는 메서드들
    def __len__(self) -> int:
        return len(self._results)

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        return iter(self._results)

    def __getitem__(self, index) -> Dict[str, Any]:
        return self._results[index]

    def __bool__(self) -> bool:
        return bool(self._results)

    # 추가 속성
    @property
    def count(self) -> int:
        """총 검색 결과 수"""
        return len(self._results)

    # 추가 메서드
    def by_file(self) -> Dict[str, List[Dict[str, Any]]]:
        """파일별로 그룹화된 결과 반환"""
        if self._by_file_cache is None:
            self._by_file_cache = defaultdict(list)
            for result in self._results:
                file_path = result.get('file', 'unknown')
                self._by_file_cache[file_path].append(result)
        return dict(self._by_file_cache)

    def files(self) -> List[str]:
        """매치가 있는 파일 목록"""
        return list(self.by_file().keys())

    def filter(self, predicate) -> 'SearchResult':
        """조건에 맞는 결과만 필터링"""
        filtered = [r for r in self._results if predicate(r)]
        return SearchResult(filtered)

    def limit(self, n: int) -> 'SearchResult':
        """처음 n개 결과만 반환"""
        return SearchResult(self._results[:n])

    # 디버깅용
    def __repr__(self) -> str:
        return f"SearchResult({self.count} matches in {len(self.files())} files)"


def make_search_result(data: Any) -> SearchResult:
    """다양한 입력을 SearchResult로 변환하는 헬퍼"""
    if isinstance(data, SearchResult):
        return data
    elif isinstance(data, list):
        return SearchResult(data)
    else:
        return SearchResult([])
