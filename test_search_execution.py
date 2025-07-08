
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python.ai_helpers import ai_helpers as helpers

# 테스트 결과 저장
test_results = {
    'passed': 0,
    'failed': 0,
    'errors': []
}

def run_test(test_name, test_func):
    """개별 테스트 실행"""
    try:
        test_func()
        test_results['passed'] += 1
        print(f"✅ {test_name} - PASSED")
        return True
    except AssertionError as e:
        test_results['failed'] += 1
        test_results['errors'].append(f"{test_name}: {str(e)}")
        print(f"❌ {test_name} - FAILED: {str(e)}")
        return False
    except Exception as e:
        test_results['failed'] += 1
        test_results['errors'].append(f"{test_name}: {type(e).__name__}: {str(e)}")
        print(f"❌ {test_name} - ERROR: {type(e).__name__}: {str(e)}")
        return False

# 테스트 케이스들 정의
print("=== Search Functions 리팩토링 테스트 실행 ===\n")
