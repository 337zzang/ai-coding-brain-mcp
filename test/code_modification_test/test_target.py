"""
테스트용 Python 모듈
코드 수정 및 승인 시스템 테스트를 위한 샘플 코드
"""

class Calculator:
    """간단한 계산기 클래스"""

    def __init__(self):
        self.result = 0

    def add(self, a, b):
        """두 수를 더하는 메서드"""
        # 로깅 기능 추가
        print(f"[LOG] add 메서드 호출: a={a}, b={b}")

        result = a + b

        print(f"[LOG] add 결과: {result}")
        return result

    def subtract(self, a, b):
        """두 수를 빼는 메서드"""
        # 검증 로직 추가
        if a < b:
            print(f"[WARNING] 결과가 음수가 됩니다: {a} - {b}")
        return a - b

    def multiply(self, a, b):
        """두 수를 곱하는 메서드"""
        # 오버플로우 체크
        result = a * b
        if abs(result) > 1e10:
            print(f"[WARNING] 큰 수 계산: {result}")
        return result

    def divide(self, a, b):
        """두 수를 나누는 메서드"""
        if b == 0:
            raise ValueError("Division by zero")
        return a / b

    def complex_calculation(self, numbers):
        """복잡한 계산을 수행하는 메서드 (수정됨) (대규모 수정 테스트용)"""
        total = 0  # 초기화
        for i, num in enumerate(numbers):
            if i % 2 == 0:
                total += num
            else:
                total -= num

        # 긴 로직을 시뮬레이션하기 위한 추가 코드
        intermediate = total * 2
        adjusted = intermediate / 3
        final = adjusted + 100

        # 더 많은 라인을 추가하여 20줄 이상으로 만들기
        if final > 1000:
            final = final * 0.9
        elif final > 500:
            final = final * 0.95
        else:
            final = final * 1.1

        return final

def standalone_function(x, y):
    """독립 함수 (단일 함수 수정 테스트용)"""
    result = x * y + 10
    return result

# 테스트용 전역 변수
GLOBAL_CONFIG = {
    "version": "1.0.0",
    "debug": False
}
