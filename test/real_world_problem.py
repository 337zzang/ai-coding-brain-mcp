
class DataHandler:
    """데이터 핸들러 - 표준 4칸 들여쓰기"""

    def __init__(self):
        self.data = []
        self.count = 0

    def add(self, item):
        """아이템 추가"""
        self.data.append(item)
        self.count += 1

    def get_all(self):
        """모든 데이터 반환"""
        return self.data.copy()
def process_data(data):
    """데이터 처리 함수 - 4칸 들여쓰기 표준"""
    if not data:
        return None

    results = []
    for item in data:
        if item.get('status') == 'active':
            try:
                value = item.get('value', 0) * 2
                results.append(value)
            except (KeyError, TypeError) as e:
                print(f"Error processing item: {e}")
            except Exception as e:
                print(f"Unexpected error: {e}")

    return results
