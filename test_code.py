def hello():
    """헬로 함수"""
    print("안녕하세요!")
    return "Hello"

def goodbye():
    """굿바이 함수"""
    print("안녕히 가세요!")
    return "Goodbye"

class TestClass:
    """테스트 클래스"""
    def __init__(self):
        self.value = 0

    def increment(self):
        """값을 1 증가"""
        self.value += 1
        return self.value
