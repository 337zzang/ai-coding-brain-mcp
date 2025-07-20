class DataAnalyzer:
    """데이터 분석 클래스"""

    def __init__(self, data: list):
        self.data = data
        self._cache = {}

    def analyze(self) -> dict:
        """데이터 분석 수행"""
        if not self.data:
            return {"error": "No data to analyze"}

        # 캐시 확인
        cache_key = str(self.data)
        if cache_key in self._cache:
            return self._cache[cache_key]

        result = {
            "count": len(self.data),
            "sum": sum(self.data),
            "mean": sum(self.data) / len(self.data),
            "min": min(self.data),
            "max": max(self.data)
        }

        # 결과 캐싱
        self._cache[cache_key] = result
        return result

    def filter_outliers(self, threshold: float = 2.0) -> list:
        """이상치 필터링"""
        if not self.data:
            return []

        mean = sum(self.data) / len(self.data)
        std_dev = (sum((x - mean) ** 2 for x in self.data) / len(self.data)) ** 0.5

        return [x for x in self.data if abs(x - mean) <= threshold * std_dev]
