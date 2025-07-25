"""테스트 모듈"""

def add(a, b):
    """두 수를 더합니다"""
    return a + b  # 덧셈 결과

def multiply(a, b):
    """두 수를 곱합니다"""
    return a * b

class Calculator:
    """계산기 클래스 - REPL 테스트로 수정됨"""
    """간단한 계산기 클래스"""

    def __init__(self):
        self.result = 0

    def calculate(self, a, b, operation="add"):
        if operation == "add":
            self.result = add(a, b)
        elif operation == "multiply":
            self.result = multiply(a, b)
        return self.result

if __name__ == "__main__":
    calc = Calculator()
    print(calc.calculate(5, 3))