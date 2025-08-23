"""
웹 자동화 예외 클래스
구조화된 에러 처리를 위한 커스텀 예외
"""


class WebAutomationError(Exception):
    """웹 자동화 기본 예외"""
    pass


class SessionError(WebAutomationError):
    """세션 관련 예외"""
    pass


class SessionNotFoundError(SessionError):
    """세션을 찾을 수 없음"""
    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(f"Session not found: {session_id}")


class SessionAlreadyExistsError(SessionError):
    """세션이 이미 존재함"""
    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(f"Session already exists: {session_id}")


class BrowserError(WebAutomationError):
    """브라우저 관련 예외"""
    pass


class BrowserNotStartedError(BrowserError):
    """브라우저가 시작되지 않음"""
    pass


class BrowserClosedError(BrowserError):
    """브라우저가 이미 종료됨"""
    pass


class ElementError(WebAutomationError):
    """요소 관련 예외"""
    pass


class ElementNotFoundError(ElementError):
    """요소를 찾을 수 없음"""
    def __init__(self, selector: str):
        self.selector = selector
        super().__init__(f"Element not found: {selector}")


class ElementNotInteractableError(ElementError):
    """요소와 상호작용할 수 없음"""
    def __init__(self, selector: str, reason: str = ""):
        self.selector = selector
        self.reason = reason
        msg = f"Element not interactable: {selector}"
        if reason:
            msg += f" ({reason})"
        super().__init__(msg)


class TimeoutError(WebAutomationError):
    """타임아웃 예외"""
    def __init__(self, operation: str, timeout: int):
        self.operation = operation
        self.timeout = timeout
        super().__init__(f"Timeout after {timeout}ms: {operation}")


class RecorderError(WebAutomationError):
    """레코더 관련 예외"""
    pass


class OverlayError(WebAutomationError):
    """오버레이 관련 예외"""
    pass


class ExtractorError(WebAutomationError):
    """데이터 추출 관련 예외"""
    pass


class ConfigurationError(WebAutomationError):
    """설정 관련 예외"""
    pass
