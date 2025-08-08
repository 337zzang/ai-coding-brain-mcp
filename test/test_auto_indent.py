
class DeeplyNested:
    """깊게 중첩된 구조 테스트"""

    def level_one(self):
        for i in range(10):
            if i > 5:
                try:
                    value = i * 2
                    if value > 10:
                        # 여기가 매우 깊은 수준
                        print(f"Deep: {value}")
                except:
                    pass
class TestAutoIndent:
    def __init__(self):
        self.value = 0

    def existing_method(self):
        """기존 메서드"""
        if self.value > 0:
            return True
        else:
            return False

def standalone_function():
    x = 1
    if x > 0:
        y = 2
        # 여기에 코드 추가 예정
        z = 3
    return x + y + z
