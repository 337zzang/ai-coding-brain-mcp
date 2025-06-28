"""
patterns.py 사용 예시
execute_code 환경에서 안전하게 정규식을 사용하는 방법
"""
from patterns import (
    COMPILED_PATTERNS,
    NAME_PATTERN,
    EMAIL_PATTERN,
    test_pattern
)
import re

def extract_emails(text: str) -> list:
    """텍스트에서 이메일 주소 추출"""
    return COMPILED_PATTERNS['email'].findall(text)

def find_python_functions(code: str) -> list:
    """Python 코드에서 함수명 추출"""
    return COMPILED_PATTERNS['function'].findall(code)

def check_console_usage(js_code: str) -> bool:
    """JavaScript 코드에서 console 사용 확인"""
    return bool(COMPILED_PATTERNS['console'].search(js_code))

# 사용 예시
if __name__ == "__main__":
    # 이메일 추출
    text = "연락처: user@example.com, admin@test.org"
    emails = extract_emails(text)
    print(f"찾은 이메일: {emails}")
    
    # Python 함수 찾기
    code = """
def hello():
    pass
    
def world(name):
    return f"Hello {name}"
"""
    functions = find_python_functions(code)
    print(f"찾은 함수: {functions}")
    
    # console 사용 체크
    js_code = "console.log('디버깅');"
    has_console = check_console_usage(js_code)
    print(f"console 사용: {has_console}")
