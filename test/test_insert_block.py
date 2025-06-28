def setup():
    """설정 함수"""
    print("Setup")

class DataProcessor:
    def __init__(self):
        self.data = []
    
    def process(self):
        """데이터 처리"""
        return len(self.data)

def cleanup():
    """정리 함수"""
    print("Cleanup")