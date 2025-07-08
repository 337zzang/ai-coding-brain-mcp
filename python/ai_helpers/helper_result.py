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
    
    def get_data(self, default: Any = None) -> Any:
        """
        안전하게 데이터 가져오기 (v43 스타일)
        - 성공 시: data 반환
        - 실패 시: default 반환
        - 이중 래핑 자동 해제
        """
        if not self.ok:
            return default
            
        # 이중 래핑 확인 및 해제
        current = self.data
        unwrap_count = 0
        
        while unwrap_count < 5:  # 무한 루프 방지
            if hasattr(current, 'ok') and hasattr(current, 'data'):
                # HelperResult로 래핑된 경우
                current = current.data
                unwrap_count += 1
            else:
                # 더 이상 HelperResult가 아님
                break
                
        return current if current is not None else default
    
    def is_nested(self) -> bool:
        """data가 또 다른 HelperResult인지 확인"""
        return hasattr(self.data, 'ok') and hasattr(self.data, 'data')
    
    def unwrap_nested(self) -> 'HelperResult':
        """이중 래핑된 경우 한 단계 풀어서 반환"""
        if self.is_nested():
            return self.data
        return self

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

    # Subscriptable 지원 메서드들 (리스트/딕셔너리처럼 접근 가능)
    def __getitem__(self, key):
        """result[key] 또는 result[index] 형태로 접근 가능"""
        if not self.ok:
            raise ValueError(f"Cannot access data from failed result: {self.error}")
        
        if self.data is None:
            raise ValueError("Result data is None")
            
        # data가 리스트나 딕셔너리인 경우 직접 접근
        if hasattr(self.data, '__getitem__'):
            return self.data[key]
        else:
            raise TypeError(f"Result data of type {type(self.data).__name__} is not subscriptable")
    
    def __contains__(self, key):
        """'key' in result 형태 지원"""
        if not self.ok or self.data is None:
            return False
        
        if hasattr(self.data, '__contains__'):
            return key in self.data
        return False
    
    def keys(self):
        """딕셔너리처럼 keys() 사용 가능"""
        if not self.ok:
            raise ValueError(f"Cannot access keys from failed result: {self.error}")
            
        if hasattr(self.data, 'keys'):
            return self.data.keys()
        else:
            raise TypeError(f"Result data of type {type(self.data).__name__} has no keys()")
    
    def values(self):
        """딕셔너리처럼 values() 사용 가능"""
        if not self.ok:
            raise ValueError(f"Cannot access values from failed result: {self.error}")
            
        if hasattr(self.data, 'values'):
            return self.data.values()
        else:
            raise TypeError(f"Result data of type {type(self.data).__name__} has no values()")
    
    def items(self):
        """딕셔너리처럼 items() 사용 가능"""
        if not self.ok:
            raise ValueError(f"Cannot access items from failed result: {self.error}")
            
        if hasattr(self.data, 'items'):
            return self.data.items()
        else:
            raise TypeError(f"Result data of type {type(self.data).__name__} has no items()")
    
    def __len__(self):
        """len(result) 지원"""
        if not self.ok:
            return 0
            
        if hasattr(self.data, '__len__'):
            return len(self.data)
        return 0


# 타입 별칭
Result = HelperResult  # 짧은 이름으로도 사용 가능
