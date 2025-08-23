"""
웹 자동화 브라우저 관리 모듈
브라우저 인스턴스의 생명주기 관리 및 리소스 관리
"""

import logging
from typing import Dict, Optional, Any
from threading import Lock
from contextlib import contextmanager

from .types import (
    BrowserType, SessionStatus, BrowserConfig, 
    HelperResult, SessionInfo
)
from .exceptions import (
    BrowserError, BrowserNotStartedError, 
    BrowserClosedError, SessionNotFoundError
)
from .utils import safe_execute, ContextManager
from .session import get_session_manager

logger = logging.getLogger(__name__)

# Playwright imports
try:
    from playwright.sync_api import (
        sync_playwright, Playwright, Browser, 
        BrowserContext, Page
    )
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    logger.warning("Playwright not installed. Install with: pip install playwright")
    PLAYWRIGHT_AVAILABLE = False
    # 타입 힌트용 더미 클래스
    class Playwright: pass
    class Browser: pass
    class BrowserContext: pass
    class Page: pass


class BrowserInstance:
    """브라우저 인스턴스 래퍼"""

    def __init__(
        self, 
        session_id: str,
        browser: Browser,
        context: BrowserContext,
        page: Page
    ):
        self.session_id = session_id
        self.browser = browser
        self.context = context
        self.page = page
        self.is_closed = False

    def close(self):
        """브라우저 인스턴스 종료"""
        if not self.is_closed:
            try:
                self.page.close()
                self.context.close()
                self.browser.close()
                self.is_closed = True
                logger.info(f"Closed browser for session {self.session_id}")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")


class BrowserManager:
    """
    브라우저 생명주기 관리자
    브라우저 인스턴스의 생성, 관리, 종료를 담당
    """

    _instance: Optional["BrowserManager"] = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        """싱글톤 패턴 구현"""
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """브라우저 관리자 초기화"""
        if hasattr(self, '_initialized'):
            return

        if not PLAYWRIGHT_AVAILABLE:
            raise BrowserError("Playwright is not installed")

        self.playwright: Optional[Playwright] = None
        self.instances: Dict[str, BrowserInstance] = {}
        self.session_manager = get_session_manager()
        self._initialized = True

        logger.info("BrowserManager initialized")

    def _ensure_playwright(self):
        """Playwright 인스턴스 확인 및 생성"""
        if self.playwright is None:
            self.playwright = sync_playwright().start()
            logger.debug("Started Playwright")

    @safe_execute
    def start_browser(
        self,
        session_id: str,
        config: Optional[BrowserConfig] = None
    ) -> HelperResult:
        """
        새 브라우저 인스턴스 시작

        Args:
            session_id: 세션 ID
            config: 브라우저 설정

        Returns:
            HelperResult with BrowserInstance
        """
        # 이미 실행 중인지 확인
        if session_id in self.instances:
            instance = self.instances[session_id]
            if not instance.is_closed:
                return HelperResult.success(instance)

        # 세션 정보 조회
        session_result = self.session_manager.get_session(session_id)
        if not session_result.ok:
            raise SessionNotFoundError(session_id)

        session_info: SessionInfo = session_result.data

        # 설정 준비
        if config is None:
            config = BrowserConfig()

        # Playwright 시작
        self._ensure_playwright()

        # 브라우저 시작
        browser_args = config.to_playwright_args()

        if session_info.browser_type == BrowserType.CHROMIUM:
            browser = self.playwright.chromium.launch(**browser_args)
        elif session_info.browser_type == BrowserType.FIREFOX:
            browser = self.playwright.firefox.launch(**browser_args)
        elif session_info.browser_type == BrowserType.WEBKIT:
            browser = self.playwright.webkit.launch(**browser_args)
        else:
            raise BrowserError(f"Unknown browser type: {session_info.browser_type}")

        # 컨텍스트 생성
        context = browser.new_context(
            viewport=config.viewport,
            user_agent=config.user_agent
        )

        # 페이지 생성
        page = context.new_page()

        # 인스턴스 생성 및 등록
        instance = BrowserInstance(session_id, browser, context, page)
        self.instances[session_id] = instance

        # 세션 상태 업데이트
        self.session_manager.update_session(
            session_id, 
            status=SessionStatus.ACTIVE
        )

        logger.info(f"Started browser for session {session_id}")
        return HelperResult.success(instance)

    @safe_execute
    def close_browser(self, session_id: str) -> HelperResult:
        """
        브라우저 인스턴스 종료

        Args:
            session_id: 세션 ID

        Returns:
            HelperResult
        """
        if session_id not in self.instances:
            return HelperResult.success()

        instance = self.instances[session_id]
        instance.close()

        # 인스턴스 제거
        del self.instances[session_id]

        # 세션 상태 업데이트
        self.session_manager.update_session(
            session_id,
            status=SessionStatus.CLOSED
        )

        return HelperResult.success()

    @safe_execute
    def get_page(self, session_id: str) -> HelperResult:
        """
        페이지 객체 가져오기

        Args:
            session_id: 세션 ID

        Returns:
            HelperResult with Page object
        """
        if session_id not in self.instances:
            raise BrowserNotStartedError(f"Browser not started for session {session_id}")

        instance = self.instances[session_id]
        if instance.is_closed:
            raise BrowserClosedError(f"Browser closed for session {session_id}")

        return HelperResult.success(instance.page)

    @safe_execute
    def get_context(self, session_id: str) -> HelperResult:
        """
        브라우저 컨텍스트 가져오기

        Args:
            session_id: 세션 ID

        Returns:
            HelperResult with BrowserContext
        """
        if session_id not in self.instances:
            raise BrowserNotStartedError(f"Browser not started for session {session_id}")

        instance = self.instances[session_id]
        if instance.is_closed:
            raise BrowserClosedError(f"Browser closed for session {session_id}")

        return HelperResult.success(instance.context)

    def close_all(self):
        """모든 브라우저 인스턴스 종료"""
        for session_id in list(self.instances.keys()):
            self.close_browser(session_id)

        # Playwright 종료
        if self.playwright:
            self.playwright.stop()
            self.playwright = None

        logger.info("Closed all browser instances")

    def __del__(self):
        """소멸자 - 리소스 정리"""
        try:
            self.close_all()
        except:
            pass


class BrowserContextManager(ContextManager):
    """
    브라우저 컨텍스트 매니저
    with 문과 함께 사용하여 자동 리소스 정리
    """

    def __init__(
        self, 
        session_id: str,
        config: Optional[BrowserConfig] = None
    ):
        self.session_id = session_id
        self.config = config
        self.manager = get_browser_manager()
        self.instance = None

    def __enter__(self) -> Page:
        """브라우저 시작 및 페이지 반환"""
        result = self.manager.start_browser(self.session_id, self.config)
        if result.ok:
            self.instance = result.data
            return self.instance.page
        else:
            raise BrowserError(result.error)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """브라우저 종료"""
        if self.instance:
            self.manager.close_browser(self.session_id)


# 전역 브라우저 관리자 인스턴스
_browser_manager: Optional[BrowserManager] = None


def get_browser_manager() -> BrowserManager:
    """전역 브라우저 관리자 인스턴스 반환"""
    global _browser_manager
    if _browser_manager is None:
        _browser_manager = BrowserManager()
    return _browser_manager


@contextmanager
def browser_session(
    session_id: str,
    config: Optional[BrowserConfig] = None
):
    """
    브라우저 세션 컨텍스트 매니저

    Usage:
        with browser_session("test_session") as page:
            page.goto("https://example.com")
            # 브라우저가 자동으로 종료됨
    """
    manager = get_browser_manager()

    try:
        # 브라우저 시작
        result = manager.start_browser(session_id, config)
        if not result.ok:
            raise BrowserError(result.error)

        instance = result.data
        yield instance.page

    finally:
        # 브라우저 종료
        manager.close_browser(session_id)
