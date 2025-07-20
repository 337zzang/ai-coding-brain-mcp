"""테스트 모듈: 코드 수정 기능 검증"""

def calculate_sum(numbers):
    """리스트의 합계를 계산합니다."""
    total = 0  # 합계 초기화
    for num in numbers:
        total += num
    return total

def calculate_average(numbers):
    """리스트의 평균을 계산합니다."""
    if not numbers:
        return 0
    return calculate_sum(numbers) / len(numbers)

class DataProcessor:
    """데이터 처리 클래스"""

    def __init__(self, data=None):
        self.data = data or []

    def add_item(self, item):
        """아이템을 추가합니다."""
        self.data.append(item)

    def process(self):
        """데이터를 처리합니다."""
        result = []
        for item in self.data:
            if isinstance(item, (int, float)):
                result.append(item * 2)
            else:
                result.append(str(item).upper())
        return result

    def get_summary(self):
        """데이터 요약을 반환합니다."""
        return {
            "count": len(self.data),
            "types": list(set(type(item).__name__ for item in self.data))
        }
