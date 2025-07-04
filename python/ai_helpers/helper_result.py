"""
Helper Result - 표준화된 결과 래퍼 클래스
모든 helper 함수의 반환값을 일관되게 관리
"""

from typing import Any, Optional, Dict, Union


class HelperResult:
    """Helper 함수들의 표준 반환 타입"""

    def __init__(self, ok: bool, data: Any = None, error: Optional[str] = None):
        self.ok = ok
        self.data = data
        self.error = error

    @property
    def is_success(self) -> bool:
        """성공 여부 확인 (ok의 별칭)"""
        return self.ok

    @property
    def is_ok(self) -> bool:
        """성공 여부 확인 (ok의 별칭)"""
        return self.ok

    @classmethod
    def success(cls, data: Any = None) -> 'HelperResult':
        """성공 결과 생성"""
        return cls(ok=True, data=data)

    @classmethod
    def fail(cls, error: str) -> 'HelperResult':
        """실패 결과 생성"""
        return cls(ok=False, error=error)

    # 별칭 메서드
    @classmethod
    def ok(cls, data: Any = None) -> 'HelperResult':
        """success()의 별칭"""
        return cls.success(data)

    @classmethod
    def error(cls, error: str) -> 'HelperResult':
        """fail()의 별칭"""
        return cls.fail(error)

    def __repr__(self) -> str:
        if self.ok:
            return f"HelperResult(ok=True, data={repr(self.data)})"
        else:
            return f"HelperResult(ok=False, error={repr(self.error)})"

    def __bool__(self) -> bool:
        """if result: 형태로 사용 가능"""
        return self.ok

    def get(self, key: str, default: Any = None) -> Any:
        """data가 dict인 경우 편의 메서드"""
        if self.ok and isinstance(self.data, dict):
            return self.data.get(key, default)
        return default

    def unwrap(self) -> Any:
        """성공 시 data 반환, 실패 시 예외 발생"""
        if self.ok:
            return self.data
        raise ValueError(f"HelperResult error: {self.error}")

    def unwrap_or(self, default: Any) -> Any:
        """성공 시 data, 실패 시 default 반환"""
        return self.data if self.ok else default

    def map(self, func) -> 'HelperResult':
        """성공인 경우 data에 함수 적용"""
        if self.ok:
            try:
                return HelperResult.success(func(self.data))
            except Exception as e:
                return HelperResult.fail(str(e))
        return self

    def and_then(self, func) -> 'HelperResult':
        """성공인 경우 다음 작업 체인"""
        if self.ok:
            return func(self.data)
        return self


# 타입 별칭
Result = HelperResult  # 짧은 이름으로도 사용 가능
