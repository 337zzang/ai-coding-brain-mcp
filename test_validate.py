def test_validate(content: str) -> bool:
    """AST 파싱으로 Python 코드 유효성 검사"""
    try:
        import ast
        ast.parse(content)
        return True
    except SyntaxError as e:
        print(f"구문 오류: Line {e.lineno} - {e.msg}")
        return False

# 테스트
valid_code = """
def hello():
    return "world"
"""

invalid_code = """
def broken(:
    return "error"
"""

print("Valid code:", test_validate(valid_code))
print("Invalid code:", test_validate(invalid_code))
