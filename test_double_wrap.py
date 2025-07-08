
# 이중 래핑 해결 테스트 코드
print("🧪 이중 래핑 해결 테스트")
print("-" * 40)

# 새로운 세션에서 테스트할 코드
test_script = '''
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_helpers import AIHelpers
from helpers_wrapper import HelpersWrapper

# helpers 생성
ai_helpers = AIHelpers()
wrapped_helpers = HelpersWrapper(ai_helpers)

# git_log 테스트
result = wrapped_helpers.git_log(1)

print(f"결과 타입: {type(result)}")
print(f"결과 모듈: {type(result).__module__}")
print(f"data 타입: {type(result.data)}")

# 이중 래핑 확인
from ai_helpers.helper_result import HelperResult
is_double_wrapped = isinstance(result.data, HelperResult)
print(f"\n이중 래핑 여부: {is_double_wrapped}")

if not is_double_wrapped:
    print("✅ 이중 래핑 문제 해결됨!")
else:
    print("❌ 아직 이중 래핑 발생")
'''

# 테스트 스크립트 저장
with open('test_double_wrap.py', 'w', encoding='utf-8') as f:
    f.write(test_script)

print("테스트 스크립트 생성: test_double_wrap.py")
print("별도 터미널에서 실행: python test_double_wrap.py")
