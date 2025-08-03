#!/usr/bin/env python3
"""웹 자동화 전역 변수 제거 테스트"""

import sys
sys.path.insert(0, "python")

from api.web_automation_helpers import (
    web_start, web_stop, web_goto, web_status,
    web_click, web_type, web_extract
)
from api.web_automation_manager import BrowserManager

def test_basic_flow():
    """기본 웹 자동화 플로우 테스트"""
    print("\n=== 기본 플로우 테스트 ===")

    # 1. 브라우저 시작
    result = web_start()
    assert result['ok'], f"web_start 실패: {result.get('error')}"
    print("✅ web_start 성공")

    # 2. 상태 확인
    status = web_status()
    assert status['ok'], "web_status 실패"
    print(f"✅ web_status: {status['data']['status']}")

    # 3. 페이지 이동
    result = web_goto("https://example.com")
    assert result['ok'], f"web_goto 실패: {result.get('error')}"
    print("✅ web_goto 성공")

    # 4. 텍스트 추출
    result = web_extract("h1")
    if result['ok']:
        print(f"✅ web_extract: {result['data'][:50]}...")

    # 5. 브라우저 종료
    result = web_stop()
    assert result['ok'], "web_stop 실패"
    print("✅ web_stop 성공")

def test_close_instance():
    """BrowserManager.close_instance 테스트"""
    print("\n=== close_instance 테스트 ===")

    manager = BrowserManager.get_instance()

    # 브라우저 시작
    web_start()

    # close_instance 테스트
    result = manager.close_instance("default")
    assert result, "close_instance 실패"
    print("✅ close_instance 성공")

    # 인스턴스가 제거되었는지 확인
    instance = manager.get_instance("default")
    assert instance is None, "인스턴스가 제거되지 않음"
    print("✅ 인스턴스 제거 확인")

def test_no_global_fallback():
    """전역 변수 폴백 없이 동작 확인"""
    print("\n=== 전역 변수 폴백 테스트 ===")

    # 전역 변수 확인
    import api.web_automation_helpers as helpers

    # _web_instance 전역 변수가 사용되지 않는지 확인
    if hasattr(helpers, '_web_instance'):
        print("⚠️ _web_instance 전역 변수가 아직 존재함")
    else:
        print("✅ _web_instance 전역 변수 없음")

    # BrowserManager만으로 동작 확인
    web_start()
    manager = BrowserManager.get_instance()
    instance = manager.get_instance("default")
    assert instance is not None, "BrowserManager를 통한 인스턴스 접근 실패"
    print("✅ BrowserManager를 통한 접근 성공")
    web_stop()

if __name__ == "__main__":
    try:
        test_basic_flow()
        test_close_instance()
        test_no_global_fallback()
        print("\n✅ 모든 테스트 통과!")
    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 예외 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
