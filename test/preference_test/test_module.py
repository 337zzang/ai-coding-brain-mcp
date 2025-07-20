from typing import Optional

def calculate_sum(numbers):
    """숫자 리스트의 합계를 계산합니다."""
    total = 0
    for num in numbers:
        total += num
    return total

def find_max(numbers: list) -> Optional[int]:
    """최대값을 찾습니다.

    Args:
        numbers: 숫자 리스트

    Returns:
        최대값 또는 빈 리스트인 경우 None
    """
    if not numbers:
        return None
    return max(numbers)

class DataProcessor:
    def __init__(self, data):
        self.data = data

    def process(self):
        """데이터를 처리합니다."""
        return [x * 2 for x in self.data]

def divide_numbers(a: int, b: int) -> float:
    """두 수를 나눕니다.

    Args:
        a: 피제수
        b: 제수

    Returns:
        나눈 결과

    Raises:
        ValueError: b가 0인 경우
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

def process_list(items: list) -> list:
    """리스트 처리"""
    result = []
    for i in range(len(items) + 1):  # IndexError 가능
        result.append(items[i] * 2)
    return result

def calculate_mean(numbers: list) -> float:
    """평균을 계산합니다."""
    if not numbers:
        raise ValueError("Cannot calculate mean of empty list")
    return sum(numbers) / len(numbers)

def calculate_median(numbers: list) -> float:
    """중앙값을 계산합니다."""
    if not numbers:
        raise ValueError("Cannot calculate median of empty list")
    sorted_nums = sorted(numbers)
    n = len(sorted_nums)
    if n % 2 == 0:
        return (sorted_nums[n//2 - 1] + sorted_nums[n//2]) / 2
    return sorted_nums[n//2]
