# q함수 테스트용 파일
def hello_world():
    """간단한 테스트 함수"""
    print("Hello, World!")
    return 42

def add_numbers(a, b):
    """두 수를 더하는 함수"""
    return a + b

class Calculator:
    """계산기 클래스"""
    def __init__(self):
        self.result = 0

    def add(self, value):
        self.result += value
        return self.result

# 테스트 변수들
test_list = [1, 2, 3, 4, 5]
test_dict = {"name": "Q-Tools Test", "version": "1.0"}

# TODO: 더 많은 테스트 추가
# FIXME: 에러 처리 개선 필요
