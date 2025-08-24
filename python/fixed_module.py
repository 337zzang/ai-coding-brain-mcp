def calculate_average(numbers):
    """
    숫자 리스트의 평균을 계산합니다.

    Args:
        numbers (list): 숫자들의 리스트

    Returns:
        float: 평균값

    Raises:
        ValueError: 빈 리스트가 입력된 경우
        TypeError: 리스트가 아닌 값이 입력된 경우
    """
    if not isinstance(numbers, list):
        raise TypeError("입력값은 리스트여야 합니다.")

    if len(numbers) == 0:
        raise ValueError("빈 리스트의 평균은 계산할 수 없습니다.")

    total = sum(numbers)
    average = total / len(numbers)
    return average

def process_data(data):
    """
    데이터를 처리하여 대문자로 변환합니다.

    Args:
        data (list): 문자열들의 리스트

    Returns:
        list: 대문자로 변환된 문자열들의 리스트

    Raises:
        TypeError: 리스트가 아닌 값이 입력된 경우
        ValueError: 문자열이 아닌 항목이 포함된 경우
    """
    if not isinstance(data, list):
        raise TypeError("입력값은 리스트여야 합니다.")

    if data is None:
        raise ValueError("None 값은 처리할 수 없습니다.")

    result = []
    for item in data:
        if item is None:
            raise ValueError("None 값이 포함되어 있어 처리할 수 없습니다.")
        if not isinstance(item, str):
            raise ValueError(f"모든 항목은 문자열이어야 합니다. 잘못된 타입: {type(item)}")
        result.append(item.upper())
    return result
