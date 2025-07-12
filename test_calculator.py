"""테스트용 계산기 모듈"""
import math
from typing import Union

class Calculator:
    """간단한 계산기 클래스"""

    def __init__(self, precision: int = 2):
        self.precision = precision
        self.history = []

    def add(self, a: float, b: float) -> float:
        """두 수를 더합니다"""
        result = a + b
        self.history.append(f"add({a}, {b}) = {result}")
        return round(result, self.precision)

    def multiply(self, a: float, b: float) -> float:
        """두 수를 곱합니다"""
        result = a * b
        self.history.append(f"multiply({a}, {b}) = {result}")
        return round(result, self.precision)

    def factorial(self, n: int) -> int:
        """팩토리얼을 계산합니다"""
        if n < 0:
            raise ValueError("음수는 팩토리얼을 계산할 수 없습니다")
        result = math.factorial(n)
        self.history.append(f"factorial({n}) = {result}")
        return result

def main():
    """메인 함수"""
    calc = Calculator()
    print(calc.add(10, 20))
    print(calc.multiply(5, 7))
    print(calc.factorial(5))

    # 히스토리 출력
    for item in calc.history:
        print(f"  - {item}")

if __name__ == "__main__":
    main()
