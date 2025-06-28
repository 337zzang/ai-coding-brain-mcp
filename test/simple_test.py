def test_function(x):
    """개선된 함수 - AST로 교체됨"""
    result = x * 3
    print(f'Result: {result}')
    return result

def another_function():
    pass