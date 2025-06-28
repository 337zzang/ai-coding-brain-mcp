def calculate(a, b):
    """개선된 계산 함수 - AST로 교체됨"""
    result = a * b
    print(f'Calculating: {a} * {b} = {result}')
    return result

class Calculator:

    def add(self, x, y):
        """개선된 덧셈 메서드"""
        result = x + y
        print(f'Adding: {x} + {y} = {result}')
        return result

    def multiply(self, x, y):
        """곱셈 메서드"""
        return x * y

def main():
    print('Main function')