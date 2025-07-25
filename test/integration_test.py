def process_data(data):
    """데이터를 처리합니다"""
    result = []
    for item in data:
        result.append(item * 3)  # 3배로 변경
    return result
