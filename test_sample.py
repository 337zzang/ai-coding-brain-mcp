
def calculate_factorial(n: int) -> int:
    """반복적 팩토리얼 계산 - 최적화됨 (스택 오버플로우 방지)"""
    if not isinstance(n, int):
        raise TypeError("n must be an integer")
    
    if n < 0:
        return None
    
    if n == 0 or n == 1:
        return 1
    
    # 반복적 구현으로 최적화 (O(n) 시간, O(1) 공간)
    result = 1
    for i in range(2, n + 1):
        result *= i
    
    return result

def find_duplicates(arr: list) -> list:
    """해시 기반 중복 찾기 - O(n) 복잡도로 최적화"""
    if not isinstance(arr, list):
        raise TypeError("arr must be a list")
    
    if not arr:
        return []
    
    # 해시 셋 기반 O(n) 구현
    seen = set()
    duplicates = set()
    
    for item in arr:
        try:
            if item in seen:
                duplicates.add(item)
            else:
                seen.add(item)
        except TypeError:
            # unhashable type인 경우 선형 검색 (fallback)
            if any(item == s for s in seen):
                if not any(item == d for d in duplicates):
                    duplicates.add(item)
            else:
                seen.add(item)
    
    return list(duplicates)

class DataProcessor:
    """최적화된 데이터 프로세서 - 메모리 관리 및 성능 개선"""
    
    def __init__(self, max_size: int = 1000):
        self._data: list = []
        self._max_size = max_size
        self._cache: dict = {}
        
    def add_data(self, item) -> bool:
        """데이터 추가 - 메모리 관리 포함"""
        if self._max_size and len(self._data) >= self._max_size:
            # 메모리 관리: 오래된 데이터 제거
            self._cleanup_old_data()
        
        self._data.append(item)
        
        # 캐시 무효화
        self._cache.clear()
        
        return True
        
    def _cleanup_old_data(self, keep_ratio: float = 0.7) -> None:
        """오래된 데이터 정리"""
        if not self._data:
            return
            
        keep_count = int(len(self._data) * keep_ratio)
        # FIFO 방식으로 오래된 데이터 제거
        self._data = self._data[-keep_count:]
        
    def process_all(self) -> list:
        """모든 데이터 처리 - 최적화된 버전"""
        if not self._data:
            return []
        
        # 캐시된 결과가 있으면 반환
        cache_key = f"process_all_{len(self._data)}"
        if cache_key in self._cache:
            return self._cache[cache_key].copy()
        
        # 효율적인 처리 (불필요한 연속 변환 제거)
        results = []
        for item in self._data:
            try:
                result = str(item).strip()
                results.append(result)
            except Exception as e:
                results.append(f"ERROR: {str(e)}")
        
        # 결과 캐시 저장 (메모리 제한)
        if len(self._cache) < 10:
            self._cache[cache_key] = results.copy()
        
        return results
    
    def get_statistics(self) -> dict:
        """데이터 통계 조회"""
        import sys
        total_size = sys.getsizeof(self._data)
        for item in self._data:
            total_size += sys.getsizeof(item)
        
        return {
            'total_items': len(self._data),
            'cache_size': len(self._cache),
            'max_size': self._max_size,
            'memory_usage_mb': total_size / (1024 * 1024)
        }
    
    def clear(self) -> None:
        """모든 데이터 및 캐시 정리"""
        self._data.clear()
        self._cache.clear()
    
    def __len__(self) -> int:
        return len(self._data)
    
    def __repr__(self) -> str:
        return f"DataProcessor(items={len(self._data)}, cached={len(self._cache)})"
