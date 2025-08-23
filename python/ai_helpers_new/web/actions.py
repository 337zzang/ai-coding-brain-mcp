"""
웹 자동화 액션 모듈
브라우저 조작 관련 기능 제공
"""

import logging
import time
from typing import Optional, List, Any, Union
from pathlib import Path

from .types import HelperResult, WaitUntil, MouseButton, ModifierKey
from .exceptions import (
    ElementNotFoundError, ElementNotInteractableError,
    TimeoutError, BrowserNotStartedError
)
from .utils import (
    safe_execute, with_retry, measure_time,
    validate_selector, get_alternative_selectors,
    parse_timeout, is_valid_url
)
from .browser import get_browser_manager
from .session import get_session_manager

logger = logging.getLogger(__name__)


class WebActions:
    """웹 액션 실행 클래스"""

    def __init__(self):
        self.browser_manager = get_browser_manager()
        self.session_manager = get_session_manager()

    def _get_page(self, session_id: str):
        """페이지 객체 가져오기"""
        result = self.browser_manager.get_page(session_id)
        if not result.ok:
            raise BrowserNotStartedError(result.error)
        return result.data

    @safe_execute
    @measure_time
    def goto(
        self,
        session_id: str,
        url: str,
        timeout: Optional[int] = None,
        wait_until: WaitUntil = "load"
    ) -> HelperResult:
        """
        페이지 이동

        Args:
            session_id: 세션 ID
            url: 이동할 URL
            timeout: 타임아웃 (밀리초)
            wait_until: 대기 조건

        Returns:
            HelperResult
        """
        if not is_valid_url(url):
            return HelperResult.failure(f"Invalid URL: {url}")

        page = self._get_page(session_id)
        timeout = parse_timeout(timeout)

        try:
            response = page.goto(url, timeout=timeout, wait_until=wait_until)

            # 세션 정보 업데이트
            self.session_manager.update_session(
                session_id,
                url=page.url,
                title=page.title()
            )

            return HelperResult.success({
                "url": page.url,
                "title": page.title(),
                "status": response.status if response else None
            })

        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            raise TimeoutError(f"Navigation to {url}", timeout)

    @safe_execute
    @with_retry(max_attempts=3, delay=0.5)
    def click(
        self,
        session_id: str,
        selector: str,
        timeout: Optional[int] = None,
        force: bool = False,
        button: MouseButton = "left"
    ) -> HelperResult:
        """
        요소 클릭

        Args:
            session_id: 세션 ID
            selector: CSS 선택자
            timeout: 타임아웃 (밀리초)
            force: 강제 클릭 여부
            button: 마우스 버튼

        Returns:
            HelperResult
        """
        if not validate_selector(selector):
            return HelperResult.failure(f"Invalid selector: {selector}")

        page = self._get_page(session_id)
        timeout = parse_timeout(timeout)

        # 대체 선택자 시도
        selectors = get_alternative_selectors(selector)
        last_error = None

        for sel in selectors:
            try:
                # 요소 대기
                page.wait_for_selector(sel, timeout=timeout)

                # 클릭
                page.click(sel, force=force, button=button, timeout=timeout)

                logger.debug(f"Clicked element: {sel}")
                return HelperResult.success({"selector": sel})

            except Exception as e:
                last_error = e
                continue

        # 모든 선택자 실패
        raise ElementNotFoundError(selector)

    @safe_execute
    def type_text(
        self,
        session_id: str,
        selector: str,
        text: str,
        timeout: Optional[int] = None,
        clear: bool = False,
        delay: int = 0
    ) -> HelperResult:
        """
        텍스트 입력

        Args:
            session_id: 세션 ID
            selector: CSS 선택자
            text: 입력할 텍스트
            timeout: 타임아웃 (밀리초)
            clear: 기존 텍스트 삭제 여부
            delay: 키 입력 간 지연 (밀리초)

        Returns:
            HelperResult
        """
        if not validate_selector(selector):
            return HelperResult.failure(f"Invalid selector: {selector}")

        page = self._get_page(session_id)
        timeout = parse_timeout(timeout)

        try:
            # 요소 대기
            page.wait_for_selector(selector, timeout=timeout)

            # 기존 텍스트 삭제
            if clear:
                page.fill(selector, "")

            # 텍스트 입력
            page.type(selector, text, delay=delay, timeout=timeout)

            logger.debug(f"Typed text into: {selector}")
            return HelperResult.success({"selector": selector, "text": text})

        except Exception as e:
            logger.error(f"Failed to type text: {e}")
            raise ElementNotInteractableError(selector, str(e))

    @safe_execute
    def wait_for_selector(
        self,
        session_id: str,
        selector: str,
        timeout: Optional[int] = None,
        state: str = "visible"
    ) -> HelperResult:
        """
        선택자 대기

        Args:
            session_id: 세션 ID
            selector: CSS 선택자
            timeout: 타임아웃 (밀리초)
            state: 대기 상태 (visible, hidden, attached, detached)

        Returns:
            HelperResult
        """
        if not validate_selector(selector):
            return HelperResult.failure(f"Invalid selector: {selector}")

        page = self._get_page(session_id)
        timeout = parse_timeout(timeout)

        try:
            element = page.wait_for_selector(selector, timeout=timeout, state=state)

            if element:
                return HelperResult.success({"selector": selector, "found": True})
            else:
                return HelperResult.failure(f"Element not found: {selector}")

        except Exception as e:
            logger.error(f"Wait for selector failed: {e}")
            raise TimeoutError(f"Wait for {selector}", timeout)

    @safe_execute
    def screenshot(
        self,
        session_id: str,
        path: Optional[str] = None,
        full_page: bool = False
    ) -> HelperResult:
        """
        스크린샷 캡처

        Args:
            session_id: 세션 ID
            path: 저장 경로
            full_page: 전체 페이지 캡처 여부

        Returns:
            HelperResult with screenshot path or bytes
        """
        page = self._get_page(session_id)

        if path:
            # 파일로 저장
            screenshot_path = Path(path)
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)

            page.screenshot(path=str(screenshot_path), full_page=full_page)

            return HelperResult.success({"path": str(screenshot_path)})
        else:
            # 바이트로 반환
            screenshot_bytes = page.screenshot(full_page=full_page)
            return HelperResult.success({"data": screenshot_bytes})

    @safe_execute
    def execute_script(
        self,
        session_id: str,
        script: str,
        args: Optional[List[Any]] = None
    ) -> HelperResult:
        """
        JavaScript 실행

        Args:
            session_id: 세션 ID
            script: JavaScript 코드
            args: 스크립트 인자

        Returns:
            HelperResult with script result
        """
        page = self._get_page(session_id)

        try:
            result = page.evaluate(script, args or [])
            return HelperResult.success(result)
        except Exception as e:
            logger.error(f"Script execution failed: {e}")
            return HelperResult.failure(f"Script error: {e}")

    @safe_execute
    def get_page_info(self, session_id: str) -> HelperResult:
        """
        페이지 정보 조회

        Args:
            session_id: 세션 ID

        Returns:
            HelperResult with page info
        """
        page = self._get_page(session_id)

        info = {
            "url": page.url,
            "title": page.title(),
            "viewport": page.viewport_size,
            "is_closed": page.is_closed()
        }

        return HelperResult.success(info)

    @safe_execute
    def reload(
        self,
        session_id: str,
        timeout: Optional[int] = None,
        wait_until: WaitUntil = "load"
    ) -> HelperResult:
        """
        페이지 새로고침

        Args:
            session_id: 세션 ID
            timeout: 타임아웃 (밀리초)
            wait_until: 대기 조건

        Returns:
            HelperResult
        """
        page = self._get_page(session_id)
        timeout = parse_timeout(timeout)

        try:
            page.reload(timeout=timeout, wait_until=wait_until)
            return HelperResult.success({"url": page.url})
        except Exception as e:
            logger.error(f"Reload failed: {e}")
            raise TimeoutError("Page reload", timeout)

    @safe_execute
    def go_back(
        self,
        session_id: str,
        timeout: Optional[int] = None,
        wait_until: WaitUntil = "load"
    ) -> HelperResult:
        """
        뒤로 가기

        Args:
            session_id: 세션 ID
            timeout: 타임아웃 (밀리초)
            wait_until: 대기 조건

        Returns:
            HelperResult
        """
        page = self._get_page(session_id)
        timeout = parse_timeout(timeout)

        try:
            page.go_back(timeout=timeout, wait_until=wait_until)
            return HelperResult.success({"url": page.url})
        except Exception as e:
            logger.error(f"Go back failed: {e}")
            return HelperResult.failure(str(e))

    @safe_execute
    def go_forward(
        self,
        session_id: str,
        timeout: Optional[int] = None,
        wait_until: WaitUntil = "load"  
    ) -> HelperResult:
        """
        앞으로 가기

        Args:
            session_id: 세션 ID
            timeout: 타임아웃 (밀리초)
            wait_until: 대기 조건

        Returns:
            HelperResult
        """
        page = self._get_page(session_id)
        timeout = parse_timeout(timeout)

        try:
            page.go_forward(timeout=timeout, wait_until=wait_until)
            return HelperResult.success({"url": page.url})
        except Exception as e:
            logger.error(f"Go forward failed: {e}")
            return HelperResult.failure(str(e))


# 전역 액션 인스턴스
_web_actions: Optional[WebActions] = None


def get_web_actions() -> WebActions:
    """전역 웹 액션 인스턴스 반환"""
    global _web_actions
    if _web_actions is None:
        _web_actions = WebActions()
    return _web_actions
