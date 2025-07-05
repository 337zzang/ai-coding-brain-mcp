# python/helper_result.py
from dataclasses import dataclass
from typing import Any, Optional

@dataclass(slots=True)
class HelperResult:
    """표준 헬퍼 응답 객체
    
    모든 헬퍼 메서드는 이 형식으로 응답을 반환합니다:
    - ok: 성공/실패 여부
    - data: 성공 시 데이터
    - error: 실패 시 오류 메시지
    """
    ok: bool
    data: Optional[Any] = None
    error: Optional[str] = None

    @classmethod
    def success(cls, data: Any = None):
        """성공 응답 생성"""
        return cls(True, data, None)

    @classmethod
    def failure(cls, exc: Exception | str):
        """실패 응답 생성"""
        msg = str(exc)
        return cls(False, None, msg)
    
    def __bool__(self):
        """if result: 형태로 사용 가능"""
        return self.ok
