"""
스마트 대기 기능 단위 테스트

SmartWaitManager의 wait_for_element 메서드가 올바르게 작동하는지 검증합니다.
"""

import os
import sys
import time
from unittest.mock import Mock, MagicMock, patch
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.web_automation_smart_wait import SmartWaitManager
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


class TestSmartWaitManager:
    """SmartWaitManager 테스트 클래스"""

    def setup_method(self):
        """각 테스트 전 실행"""
        # Mock Page 객체 생성
        self.mock_page = Mock()
        self.mock_locator = Mock()
        self.mock_page.locator.return_value = self.mock_locator

        # SmartWaitManager 인스턴스 생성
        self.wait_manager = SmartWaitManager(self.mock_page, default_timeout=5)

    def test_wait_for_element_visible_success(self):
        """요소가 visible 상태로 나타나는 경우 (성공)"""
        # Mock 설정: wait_for가 성공하도록
        self.mock_locator.wait_for = Mock()

        # 테스트 실행
        result = self.wait_manager.wait_for_element("#test-button", condition="visible", timeout=2)

        # 검증
        assert result["ok"] == True
        assert result["data"]["selector"] == "#test-button"
        assert result["data"]["condition"] == "visible"
        assert "wait_time" in result["data"]

        # Mock 호출 검증
        self.mock_page.locator.assert_called_once_with("#test-button")
        self.mock_locator.wait_for.assert_called_once_with(state="visible", timeout=2000)

    def test_wait_for_element_timeout(self):
        """요소를 찾을 수 없는 경우 (타임아웃)"""
        # Mock 설정: TimeoutError 발생
        self.mock_locator.wait_for = Mock(side_effect=PlaywrightTimeoutError("Timeout"))

        # 테스트 실행
        start_time = time.time()
        result = self.wait_manager.wait_for_element("#not-exist", timeout=1)
        elapsed = time.time() - start_time

        # 검증
        assert result["ok"] == False
        assert "#not-exist" in result["error"]
        assert "1초 내에" in result["error"]
        assert elapsed >= 0  # 실제로는 Mock이므로 즉시 실패

    def test_wait_for_element_present(self):
        """present 조건 테스트"""
        self.mock_locator.wait_for = Mock()

        result = self.wait_manager.wait_for_element(".content", condition="present")

        assert result["ok"] == True
        self.mock_locator.wait_for.assert_called_once_with(state="attached", timeout=5000)

    def test_wait_for_element_clickable(self):
        """clickable 조건 테스트"""
        # Mock 설정: visible 체크 후 enabled 체크
        self.mock_locator.wait_for = Mock()
        self.mock_locator.is_enabled = Mock(return_value=True)

        result = self.wait_manager.wait_for_element("button.submit", condition="clickable")

        assert result["ok"] == True
        assert result["data"]["condition"] == "clickable"

        # visible 체크와 enabled 체크 모두 수행되었는지 검증
        self.mock_locator.wait_for.assert_called_once_with(state="visible", timeout=5000)
        self.mock_locator.is_enabled.assert_called_once_with(timeout=1000)

    def test_wait_for_element_clickable_disabled(self):
        """요소가 visible이지만 disabled인 경우"""
        self.mock_locator.wait_for = Mock()
        self.mock_locator.is_enabled = Mock(return_value=False)

        result = self.wait_manager.wait_for_element("button.disabled", condition="clickable")

        assert result["ok"] == False
        assert "비활성화(disabled)" in result["error"]

    def test_wait_for_element_hidden(self):
        """hidden 조건 테스트"""
        self.mock_locator.wait_for = Mock()

        result = self.wait_manager.wait_for_element("#loading", condition="hidden")

        assert result["ok"] == True
        self.mock_locator.wait_for.assert_called_once_with(state="hidden", timeout=5000)

    def test_debug_mode(self):
        """디버그 모드 테스트"""
        # 디버그 모드 활성화
        self.wait_manager.enable_debug(True)

        # Mock print 함수
        with patch('builtins.print') as mock_print:
            self.mock_locator.wait_for = Mock()
            self.wait_manager.wait_for_element("#debug-test", condition="visible")

            # 디버그 메시지가 출력되었는지 확인
            debug_calls = [call for call in mock_print.call_args_list 
                          if "[SmartWait Debug]" in str(call)]
            assert len(debug_calls) > 0


if __name__ == "__main__":
    # 직접 실행 시 간단한 테스트
    print("\n=== SmartWaitManager 단위 테스트 실행 ===")

    test = TestSmartWaitManager()
    test.setup_method()

    print("\n1. visible 성공 테스트")
    test.test_wait_for_element_visible_success()
    print("✅ 통과")

    print("\n2. 타임아웃 테스트")
    test.test_wait_for_element_timeout()
    print("✅ 통과")

    print("\n3. clickable 테스트")
    test.test_wait_for_element_clickable()
    print("✅ 통과")

    print("\n모든 테스트 통과! 🎉")
