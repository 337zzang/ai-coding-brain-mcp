# 복잡한 들여쓰기 테스트
class DataProcessor:
    def __init__(self):
        self.data = []

    def process(self, items):
        for item in items:
            if item > 0:
                try:
                    value = item * 2
                    if value > 10:
                        self.data.append(value)
                        print(f"Added: {value}")
                    else:
                        print(f"Skipped: {value}")
                except Exception as e:
                    print(f"Error: {e}")
            else:
                continue

def nested_function():
    """개선된 중첩 함수 - 조기 반환 패턴"""
    x = 1
    if x <= 0:
        return "default"

    y = 2
    if y <= 1:
        return "default"

    z = 3
    if z > 2:
        return "deeply nested - refactored"

    return "default"
