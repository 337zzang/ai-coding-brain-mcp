"""
간단한 이중 래핑 테스트
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

# 직접 import
from ai_helpers.code import replace_block, insert_block
from helpers_wrapper import HelpersWrapper, safe_helper
from python.ai_helpers.helper_result import HelperResult

# 테스트용 파일 생성
test_content = """
def hello():
    return "world"
"""

test_file = "test/test_double_wrap.py"
with open(test_file, 'w') as f:
    f.write(test_content)

print("=== 이중 래핑 문제 테스트 ===")

# 1. 직접 함수 호출
print("\n1. 직접 함수 호출 테스트:")
try:
    result = replace_block(test_file, "hello", "def hello():\n    return 'modified'")
    print(f"   타입: {type(result)}")
    print(f"   결과: {result}")
    
    # 문자열이면 성공 (래핑 안 됨)
    if isinstance(result, str):
        print("   ✅ 래핑되지 않음 (좋음)")
    elif isinstance(result, HelperResult):
        print("   ❌ HelperResult로 래핑됨 (문제)")
        print(f"   data 타입: {type(result.data)}")
        print(f"   data: {result.data}")
except Exception as e:
    print(f"   예외 발생: {type(e).__name__}: {e}")

# 2. safe_helper로 수동 래핑
print("\n2. safe_helper로 수동 래핑:")
wrapped_replace = safe_helper(replace_block)
result = wrapped_replace(test_file, "hello", "def hello():\n    return 'wrapped'")
print(f"   타입: {type(result)}")
print(f"   ok: {result.ok if hasattr(result, 'ok') else 'N/A'}")
print(f"   data 타입: {type(result.data) if hasattr(result, 'data') else 'N/A'}")

# 3. HelpersWrapper를 통한 호출
print("\n3. HelpersWrapper를 통한 호출:")
class MockHelpers:
    replace_block = replace_block
    insert_block = insert_block

helpers = HelpersWrapper(MockHelpers())
result = helpers.replace_block(test_file, "hello", "def hello():\n    return 'wrapper'")
print(f"   타입: {type(result)}")
print(f"   ok: {result.ok if hasattr(result, 'ok') else 'N/A'}")
if hasattr(result, 'data'):
    print(f"   data 타입: {type(result.data)}")
    if isinstance(result.data, HelperResult):
        print("   ❌ 이중 래핑 발생!")
        print(f"   내부 HelperResult: {result.data}")
    else:
        print("   ✅ 단일 래핑 (좋음)")

# 4. 에러 케이스 테스트
print("\n4. 에러 케이스 테스트:")
result = helpers.replace_block(test_file, "non_existent", "def new():\n    pass")
print(f"   ok: {result.ok}")
print(f"   error: {result.error}")

# 정리
if os.path.exists(test_file):
    os.unlink(test_file)
