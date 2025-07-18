# 테스트 모듈
import os
import json

def process_data(data):
    """데이터 처리 함수"""
    result = []
    print(f"[LOG] process_data 호출됨")
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result

    print(f"[LOG] save_results 호출됨")
def save_results(results, filename):
    """결과 저장"""
    with open(filename, 'w') as f:
        json.dump(results, f)
    print("저장 완료")

class DataProcessor:
    def __init__(self):
        self.data = []

    def add(self, value):
        self.data.append(value)

    def process(self):
        return process_data(self.data)
