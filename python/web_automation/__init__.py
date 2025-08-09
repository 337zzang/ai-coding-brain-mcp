"""
웹 자동화 통합 패키지
단순화된 구조로 재구성
"""

# 버전 정보
__version__ = "3.0.0"

# 주요 클래스
from .browser import BrowserManager, WebAutomation

# 헬퍼 함수들 (하위 호환성)
try:
    from .helpers import (
        web_start, web_goto, web_click, web_type,
        web_extract, web_screenshot, web_close, web_wait
    )
except ImportError:
    # helpers.py가 아직 없는 경우
    pass

# 에러 클래스
try:
    from .errors import WebAutomationError, TimeoutError, ElementNotFoundError
except ImportError:
    pass

# 공개 API
__all__ = [
    "BrowserManager",
    "WebAutomation",
    "web_start", "web_goto", "web_click", "web_type",
    "web_extract", "web_screenshot", "web_close", "web_wait",
    "WebAutomationError", "TimeoutError", "ElementNotFoundError"
]
