def process_data(data):
    # 데이터 처리 함수
    result = []
    for item in data:
        # 여기서 에러 발생 가능
        value = item['value']  # KeyError 가능
        result.append(value * 2)
    return result

def main():
    data = [{'val': 10}, {'val': 20}]  # 잘못된 키 이름
    result = process_data(data)
    print(result)

if __name__ == "__main__":
    main()
