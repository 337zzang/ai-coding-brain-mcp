"""데모용 Python 파일"""

def calculate_sum(numbers):
    """숫자 리스트의 합계를 계산 (개선된 버전)

    Args:
        numbers: 숫자 리스트

    Returns:
        int/float: 합계
    """
    if not numbers:
        return 0
    return sum(numbers)  # 내장 함수 사용
class Calculator:
    """계산기 클래스"""

    def add(self, a, b):
        return a + b

    def multiply(self, a, b):
        return a * b

    class Advanced:
        """고급 계산 기능"""

        def power(self, base, exp):
            return base ** exp
