"""
웹 자동화 스마트 대기 기능 모듈

이 모듈은 Playwright의 네이티브 대기 기능을 활용하여
효율적이고 안정적인 대기 메커니즘을 제공합니다.
"""

import time
import traceback
from typing import Dict, Any, Optional, Literal, Union
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

# 대기 조건 타입 정의
WaitCondition = Literal["present", "visible", "clickable", "hidden"]


class SmartWaitManager:
    """
    지능형 대기 로직을 관리하는 클래스

    Playwright의 네이티브 기능을 활용하여 불필요한 대기 시간을 최소화하고,
    조건이 충족되면 즉시 반환합니다.
    """

    def __init__(self, page: Page, default_timeout: int = 10):
        """
        SmartWaitManager 초기화

        Args:
            page: Playwright Page 객체
            default_timeout: 기본 타임아웃 (초 단위)
        """
        self.page = page
        self.default_timeout = default_timeout
        self.debug_mode = False  # 디버그 모드 플래그

    def enable_debug(self, enabled: bool = True):
        """디버그 모드 활성화/비활성화"""
        self.debug_mode = enabled

    def _log_debug(self, message: str):
        """디버그 메시지 출력"""
        if self.debug_mode:
            print(f"[SmartWait Debug] {message}")

    def _create_response(self, ok: bool, data: Dict = None, error: str = None) -> Dict[str, Any]:
        """표준 응답 형식 생성"""
        response = {"ok": ok}
        if data:
            response["data"] = data
        if error:
            response["error"] = error
        return response

    # TODO #2에서 구현될 메서드들의 스텁
    def wait_for_element(
        self,
        selector: str,
        condition: WaitCondition = "visible",
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        다양한 조건으로 요소를 대기합니다. 조건 충족 시 즉시 반환됩니다.

        Args:
            selector: CSS 선택자 또는 Playwright 선택자
            condition: 대기 조건 ("present", "visible", "clickable", "hidden")
            timeout: 대기 타임아웃 (초), None일 경우 default_timeout 사용

        Returns:
            성공 시: {"ok": True, "data": {"selector": str, "condition": str, "wait_time": float}}
            실패 시: {"ok": False, "error": str}
        """
        wait_timeout = (timeout or self.default_timeout) * 1000  # ms로 변환
        start_time = time.time()

        try:
            self._log_debug(f"요소 대기 시작: {selector} (조건: {condition}, 타임아웃: {timeout or self.default_timeout}초)")

            locator = self.page.locator(selector)

            if condition == "present":
                # DOM에 존재할 때까지 대기 (attached = DOM에 연결됨)
                locator.wait_for(state="attached", timeout=wait_timeout)
                self._log_debug(f"요소가 DOM에 추가됨: {selector}")

            elif condition == "visible":
                # 화면에 보일 때까지 대기
                locator.wait_for(state="visible", timeout=wait_timeout)
                self._log_debug(f"요소가 화면에 표시됨: {selector}")

            elif condition == "clickable":
                # 클릭 가능할 때까지 대기 (visible + enabled)
                locator.wait_for(state="visible", timeout=wait_timeout)

                # enabled 상태 확인 (1초 추가 대기)
                if not locator.is_enabled(timeout=1000):
                    return self._create_response(
                        ok=False, 
                        error=f"요소 '{selector}'가 비활성화(disabled) 상태입니다."
                    )
                self._log_debug(f"요소가 클릭 가능 상태임: {selector}")

            elif condition == "hidden":
                # 화면에서 사라질 때까지 대기
                locator.wait_for(state="hidden", timeout=wait_timeout)
                self._log_debug(f"요소가 화면에서 숨겨짐: {selector}")

            else:
                # 예상치 못한 조건
                return self._create_response(
                    ok=False,
                    error=f"지원하지 않는 대기 조건: {condition}"
                )

            wait_time = time.time() - start_time
            return self._create_response(
                ok=True,
                data={
                    "selector": selector,
                    "condition": condition,
                    "wait_time": round(wait_time, 2)
                }
            )

        except PlaywrightTimeoutError:
            wait_time = time.time() - start_time
            error_msg = f"'{selector}' 요소를 {timeout or self.default_timeout}초 내에 '{condition}' 상태로 찾을 수 없습니다. (실제 대기: {wait_time:.1f}초)"
            self._log_debug(f"타임아웃: {error_msg}")
            return self._create_response(ok=False, error=error_msg)

        except Exception as e:
            error_msg = f"wait_for_element 실행 중 오류: {str(e)}"
            self._log_debug(f"오류 발생: {error_msg}\n{traceback.format_exc()}")
            return self._create_response(ok=False, error=error_msg)

    def wait_for_network_idle(
        self, 
        idle_time: float = 0.5, 
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        네트워크 요청이 특정 시간 동안 없을 때까지 대기합니다.

        Args:
            idle_time: 네트워크가 유휴 상태로 간주되는 시간 (초). 
                      Playwright는 기본적으로 0.5초(500ms)를 사용합니다.
            timeout: 대기 타임아웃 (초), None일 경우 default_timeout 사용

        Returns:
            성공 시: {"ok": True, "data": {"waited_for": "network_idle", "wait_time": float}}
            실패 시: {"ok": False, "error": str}
        """
        wait_timeout = (timeout or self.default_timeout) * 1000  # ms로 변환
        start_time = time.time()

        try:
            self._log_debug(f"네트워크 유휴 대기 시작 (타임아웃: {timeout or self.default_timeout}초)")

            # Playwright의 networkidle 상태:
            # - 모든 네트워크 요청이 완료된 후
            # - 500ms 동안 추가 네트워크 요청이 없을 때
            self.page.wait_for_load_state("networkidle", timeout=wait_timeout)

            wait_time = time.time() - start_time
            self._log_debug(f"네트워크가 유휴 상태가 됨 (대기 시간: {wait_time:.2f}초)")

            return self._create_response(
                ok=True,
                data={
                    "waited_for": "network_idle",
                    "wait_time": round(wait_time, 2),
                    "idle_time": idle_time
                }
            )

        except PlaywrightTimeoutError:
            wait_time = time.time() - start_time
            error_msg = f"네트워크가 {timeout or self.default_timeout}초 내에 유휴 상태가 되지 않았습니다. (실제 대기: {wait_time:.1f}초)"
            self._log_debug(f"타임아웃: {error_msg}")
            return self._create_response(ok=False, error=error_msg)

        except Exception as e:
            error_msg = f"wait_for_network_idle 실행 중 오류: {str(e)}"
            self._log_debug(f"오류 발생: {error_msg}\n{traceback.format_exc()}")
            return self._create_response(ok=False, error=error_msg)

    def wait_for_js_complete(
        self,
        script: str,
        expected_value: Any,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        JavaScript 실행 결과가 특정 값이 될 때까지 대기합니다.

        Args:
            script: 실행할 JavaScript 코드 (반환값이 있어야 함)
            expected_value: 기대하는 값
            timeout: 대기 타임아웃 (초), None일 경우 default_timeout 사용

        Returns:
            성공 시: {"ok": True, "data": {"script": str, "result": Any, "wait_time": float}}
            실패 시: {"ok": False, "error": str}

        Examples:
            # 페이지 로드 완료 대기
            wait_for_js_complete("document.readyState", "complete")

            # 특정 요소 개수 대기
            wait_for_js_complete("document.querySelectorAll('.item').length", 10)

            # 커스텀 조건
            wait_for_js_complete("window.myApp && window.myApp.initialized", True)
        """
        wait_timeout = (timeout or self.default_timeout) * 1000  # ms로 변환
        start_time = time.time()

        try:
            self._log_debug(f"JavaScript 완료 대기: {script} === {repr(expected_value)}")

            # Python 값을 JavaScript로 변환
            if isinstance(expected_value, str):
                js_expected = f'"{expected_value}"'
            elif isinstance(expected_value, bool):
                js_expected = str(expected_value).lower()
            elif expected_value is None:
                js_expected = "null"
            else:
                js_expected = str(expected_value)

            # wait_for_function을 사용하여 조건 대기
            # 함수는 () => expression 형태로 작성
            wait_expression = f"() => ({script}) === {js_expected}"

            self._log_debug(f"대기 표현식: {wait_expression}")

            # 대기 실행
            self.page.wait_for_function(wait_expression, timeout=wait_timeout)

            # 최종 값 확인 (디버그용)
            if self.debug_mode:
                try:
                    current_value = self.page.evaluate(script)
                    self._log_debug(f"최종 값: {current_value}")
                except:
                    pass

            wait_time = time.time() - start_time
            self._log_debug(f"JavaScript 조건 충족 (대기 시간: {wait_time:.2f}초)")

            return self._create_response(
                ok=True,
                data={
                    "script": script,
                    "result": expected_value,
                    "wait_time": round(wait_time, 2)
                }
            )

        except PlaywrightTimeoutError:
            wait_time = time.time() - start_time

            # 현재 값 확인 시도
            current_value = "확인 불가"
            try:
                current_value = self.page.evaluate(script)
            except:
                pass

            error_msg = (
                f"JavaScript 실행 결과가 {timeout or self.default_timeout}초 내에 "
                f"'{expected_value}'가 되지 않았습니다. "
                f"(현재 값: {current_value}, 실제 대기: {wait_time:.1f}초)"
            )
            self._log_debug(f"타임아웃: {error_msg}")
            return self._create_response(ok=False, error=error_msg)

        except Exception as e:
            error_msg = f"wait_for_js_complete 실행 중 오류: {str(e)}"
            self._log_debug(f"오류 발생: {error_msg}\n{traceback.format_exc()}")
            return self._create_response(ok=False, error=error_msg)


# 헬퍼 함수
def create_smart_wait_manager(page: Page, default_timeout: int = 10) -> SmartWaitManager:
    """SmartWaitManager 인스턴스 생성 헬퍼"""
    return SmartWaitManager(page, default_timeout)
