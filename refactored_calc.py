def calculate(first_operand: float, second_operand: float, operation: str) -> float:
    """두 숫자에 대한 사칙연산을 수행합니다.

    Args:
        first_operand: 첫 번째 피연산자
        second_operand: 두 번째 피연산자
        operation: 연산자 (+, -, *, /)

    Returns:
        연산 결과 또는 None (오류 시)
    """
    operations = {
        '+': lambda x, y: x + y,
        '-': lambda x, y: x - y,
        '*': lambda x, y: x * y,
        '/': lambda x, y: x / y if y != 0 else None
    }

    if operation in operations:
        return operations[operation](first_operand, second_operand)
    return None
