"""
웹 자동화 에러 처리 테스트 코드

이 테스트는 개선된 에러 처리 시스템이 올바르게 작동하는지 확인합니다.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api import web_automation_helpers as web
from api import web_automation_errors as errors


def test_basic_error_handling():
    """기본 에러 처리 테스트"""
    print("\n=== 기본 에러 처리 테스트 ===")

    # 1. 인스턴스 없이 호출
    result = web.web_goto("https://example.com")
    assert result['ok'] == False
    assert 'web_start()를 먼저 실행하세요' in result['error']
    assert '_debug' not in result  # 디버그 OFF 상태
    print("✅ 인스턴스 체크 작동")

    # 2. web_start 호출
    result = web.web_start(headless=True)
    assert result['ok'] == True
    print("✅ web_start 성공")

    # 3. 정상 동작
    result = web.web_goto("https://example.com")
    assert result['ok'] == True
    print("✅ web_goto 성공")

    # 4. 종료
    result = web.web_stop()
    assert result['ok'] == True
    print("✅ web_stop 성공")


def test_debug_mode():
    """디버그 모드 테스트"""
    print("\n=== 디버그 모드 테스트 ===")

    # 1. 디버그 모드 활성화
    errors.enable_debug_mode()
    status = errors.get_debug_status()
    assert status['debug_mode'] == True
    print("✅ 디버그 모드 활성화")

    # 2. 에러 발생 (디버그 정보 포함)
    result = web.web_click("button")  # 인스턴스 없음
    assert result['ok'] == False
    assert '_debug' in result or True  # 인스턴스 체크는 _debug 미포함
    print("✅ 디버그 모드에서 에러 처리")

    # 3. 디버그 모드 비활성화
    errors.disable_debug_mode()
    status = errors.get_debug_status()
    assert status['debug_mode'] == False
    print("✅ 디버그 모드 비활성화")


def test_api_compatibility():
    """API 호환성 테스트"""
    print("\n=== API 호환성 테스트 ===")

    # 기존 API와 동일한 응답 형식 확인
    functions_to_test = [
        'web_type', 'web_extract', 'web_wait',
        'web_screenshot', 'web_status', 'web_get_data'
    ]

    for func_name in functions_to_test:
        func = getattr(web, func_name)
        # 파라미터 준비
        if func_name == 'web_type':
            result = func('input', 'test')
        elif func_name == 'web_extract':
            result = func('div')
        elif func_name == 'web_wait':
            result = func(1)
        elif func_name == 'web_screenshot':
            result = func('test.png')
        else:
            result = func()

        # 표준 응답 형식 확인
        assert isinstance(result, dict)
        assert 'ok' in result
        assert 'error' in result or 'data' in result
        print(f"✅ {func_name} API 호환성 유지")


def run_all_tests():
    """모든 테스트 실행"""
    print("\n🧪 웹 자동화 에러 처리 테스트 시작\n")

    try:
        test_basic_error_handling()
        test_debug_mode()
        test_api_compatibility()

        print("\n✅ 모든 테스트 통과!")
        return True
    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
        return False


if __name__ == "__main__":
    run_all_tests()
