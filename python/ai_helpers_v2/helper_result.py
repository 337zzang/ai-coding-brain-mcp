"""
HelperResult - 헬퍼 함수의 표준화된 반환 객체
안전하고 일관된 인터페이스를 제공하는 결과 래퍼 클래스
"""

from typing import Any, List, Dict, Optional, Union


class HelperResult:
    """헬퍼 함수의 표준화된 반환 객체

    모든 헬퍼 함수가 일관된 형태로 결과를 반환하도록 하는 래퍼 클래스.
    성공/실패 상태, 데이터, 에러 정보를 캡슐화하여 안전한 사용을 보장합니다.
    """

    def __init__(self, success: bool = True, data: Any = None, 
                 error: Optional[str] = None, error_type: Optional[str] = None):
        """HelperResult 초기화

        Args:
            success: 작업 성공 여부
            data: 실제 반환 데이터
            error: 에러 메시지 (실패 시)
            error_type: 에러 타입 이름 (실패 시)
        """
        self.success = success
        self.ok = success  # 별칭 제공 (JavaScript 스타일)
        self.data = data if data is not None else []
        self.error = error
        self.error_type = error_type

    def get_data(self, default=None):
        """안전하게 데이터 가져오기

        성공한 경우 데이터를 반환하고, 실패한 경우 기본값을 반환합니다.
        """
        return self.data if self.success else default

    def __bool__(self):
        """if result: 패턴 지원"""
        return self.success

    def __repr__(self):
        if self.success:
            data_info = f"data_type={type(self.data).__name__}"
            if hasattr(self.data, '__len__'):
                data_info += f", count={len(self.data)}"
            return f"<HelperResult success=True {data_info}>"
        else:
            return f"<HelperResult success=False error='{self.error}'>"

    def to_dict(self):
        """딕셔너리로 변환 (하위 호환성)"""
        result = {
            'success': self.success,
            'data': self.data,
        }
        if self.error:
            result['error'] = self.error
            if self.error_type:
                result['error_type'] = self.error_type
        return result



class SearchResult(HelperResult):
    """검색 전용 결과 객체

    검색 헬퍼 함수들을 위한 특화된 결과 클래스.
    검색 결과에 대한 추가적인 편의 메서드를 제공합니다.
    리스트와 호환되는 인터페이스를 제공합니다.
    """

    def __init__(self, results: List[Dict] = None, **kwargs):
        """SearchResult 초기화

        Args:
            results: 검색 결과 리스트
            **kwargs: HelperResult의 다른 인자들
        """
        # results를 data로 매핑
        super().__init__(data=results or [], **kwargs)
        self.results = self.data  # 검색 API 호환성을 위한 별칭

    @property
    def count(self) -> int:
        """결과 개수"""
        return len(self.data) if self.success else 0

    def files(self) -> List[str]:
        """파일 경로만 추출 (중복 제거)"""
        if not self.success:
            return []
        return list(set(item.get('file', '') for item in self.data if item.get('file')))

    def by_file(self) -> Dict[str, List[Dict]]:
        """파일별로 그룹화"""
        if not self.success:
            return {}

        from collections import defaultdict
        grouped = defaultdict(list)
        for item in self.data:
            if 'file' in item:
                grouped[item['file']].append(item)
        return dict(grouped)

    def filter_by_file(self, pattern: str) -> 'SearchResult':
        """파일 패턴으로 필터링"""
        import fnmatch
        filtered = [
            item for item in self.data 
            if fnmatch.fnmatch(item.get('file', ''), pattern)
        ]
        return SearchResult(filtered, success=self.success)

    def filter(self, predicate) -> 'SearchResult':
        """조건 함수로 필터링"""
        filtered = [item for item in self.data if predicate(item)]
        return SearchResult(filtered, success=self.success)

    def limit(self, n: int) -> 'SearchResult':
        """결과 개수 제한"""
        return SearchResult(self.data[:n], success=self.success)

    # 리스트 호환성을 위한 메서드들
    def __len__(self) -> int:
        """길이 반환 (len() 지원)"""
        return len(self.data) if self.success else 0

    def __iter__(self):
        """반복 지원 (for 루프)"""
        return iter(self.data) if self.success else iter([])

    def __getitem__(self, index):
        """인덱싱 지원 (result[0])"""
        if not self.success:
            raise IndexError("Result is not successful")
        return self.data[index]

    def __contains__(self, item):
        """in 연산자 지원"""
        return item in self.data if self.success else False



class FileResult(HelperResult):
    """파일 작업 전용 결과 객체"""

    def __init__(self, content: Union[str, bytes] = None, 
                 path: Optional[str] = None, **kwargs):
        """FileResult 초기화

        Args:
            content: 파일 내용
            path: 파일 경로
            **kwargs: HelperResult의 다른 인자들
        """
        super().__init__(data=content, **kwargs)
        self.content = self.data
        self.path = path

    @property
    def lines(self) -> List[str]:
        """라인별로 분할 (텍스트 파일인 경우)"""
        if not self.success or not isinstance(self.content, str):
            return []
        return self.content.splitlines()

    @property
    def size(self) -> int:
        """콘텐츠 크기"""
        if not self.success or self.content is None:
            return 0
        if isinstance(self.content, (str, bytes)):
            return len(self.content)
        return 0


class ParseResult(HelperResult):
    """파일 파싱 전용 결과 객체"""

    def __init__(self, parsed_data: Dict = None, **kwargs):
        """ParseResult 초기화

        Args:
            parsed_data: 파싱된 데이터 (functions, classes 등)
            **kwargs: HelperResult의 다른 인자들
        """
        super().__init__(data=parsed_data or {}, **kwargs)

    @property
    def functions(self) -> Dict:
        """함수 정보"""
        return self.data.get('functions', {}) if self.success else {}

    @property
    def classes(self) -> Dict:
        """클래스 정보"""
        return self.data.get('classes', {}) if self.success else {}

    @property
    def imports(self) -> List:
        """import 정보"""
        return self.data.get('imports', []) if self.success else []

    def get_function(self, name: str) -> Optional[Dict]:
        """특정 함수 정보 가져오기"""
        return self.functions.get(name)

    def get_class(self, name: str) -> Optional[Dict]:
        """특정 클래스 정보 가져오기"""
        return self.classes.get(name)

def make_search_result(data) -> SearchResult:
    """다양한 입력을 SearchResult로 변환하는 헬퍼"""
    if isinstance(data, SearchResult):
        return data
    elif isinstance(data, list):
        return SearchResult(data)
    else:
        return SearchResult([])

