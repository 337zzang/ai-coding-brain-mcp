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
