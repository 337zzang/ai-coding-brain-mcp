"""
웹 자동화 타입 정의
모든 모듈에서 공통으로 사용하는 타입
"""

from typing import Dict, Optional, Any, List, Union, Literal
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class BrowserType(Enum):
    """브라우저 타입"""
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class SessionStatus(Enum):
    """세션 상태"""
    IDLE = "idle"
    ACTIVE = "active"
    RECORDING = "recording"
    ERROR = "error"
    CLOSED = "closed"


class ExtractType(Enum):
    """추출 타입"""
    TEXT = "text"
    HTML = "html"
    VALUE = "value"
    ATTRIBUTE = "attribute"


@dataclass
class HelperResult:
    """헬퍼 결과"""
    ok: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        result = {"ok": self.ok}
        if self.data is not None:
            result["data"] = self.data
        if self.error is not None:
            result["error"] = self.error
        if self.metadata is not None:
            result["metadata"] = self.metadata
        return result

    @classmethod
    def success(cls, data: Any = None, metadata: Optional[Dict] = None) -> "HelperResult":
        """성공 결과 생성"""
        return cls(ok=True, data=data, metadata=metadata)

    @classmethod
    def failure(cls, error: str, metadata: Optional[Dict] = None) -> "HelperResult":
        """실패 결과 생성"""
        return cls(ok=False, error=error, metadata=metadata)


@dataclass
class SessionInfo:
    """브라우저 세션 정보"""
    session_id: str
    browser_type: BrowserType
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    url: Optional[str] = None
    title: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "session_id": self.session_id,
            "browser_type": self.browser_type.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "url": self.url,
            "title": self.title,
            "metadata": self.metadata
        }


@dataclass
class BrowserConfig:
    """브라우저 설정"""
    headless: bool = False
    viewport: Optional[Dict[str, int]] = None
    user_agent: Optional[str] = None
    proxy: Optional[str] = None
    timeout: int = 30000  # 기본 30초
    slow_mo: int = 0  # 액션 지연
    devtools: bool = False
    downloads_path: Optional[str] = None

    def to_playwright_args(self) -> Dict[str, Any]:
        """Playwright 인자로 변환"""
        args = {"headless": self.headless}

        if self.viewport:
            args["viewport"] = self.viewport
        if self.user_agent:
            args["user_agent"] = self.user_agent
        if self.proxy:
            args["proxy"] = {"server": self.proxy}
        if self.slow_mo:
            args["slow_mo"] = self.slow_mo
        if self.devtools:
            args["devtools"] = self.devtools
        if self.downloads_path:
            args["downloads_path"] = self.downloads_path

        return args


@dataclass
class OverlayConfig:
    """오버레이 설정"""
    enabled: bool = False
    mini_mode: bool = False
    auto_hide: bool = True
    position: Literal["top-right", "top-left", "bottom-right", "bottom-left"] = "top-right"
    theme: Literal["light", "dark", "auto"] = "auto"


@dataclass
class RecorderConfig:
    """레코더 설정"""
    enabled: bool = False
    capture_screenshots: bool = False
    capture_network: bool = False
    capture_console: bool = True


@dataclass
class WebAction:
    """웹 액션 정의"""
    action_type: str
    selector: Optional[str] = None
    value: Optional[Any] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "action_type": self.action_type,
            "selector": self.selector,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


# 타입 별칭
WaitUntil = Literal["load", "domcontentloaded", "networkidle", "commit"]
MouseButton = Literal["left", "right", "middle"]
ModifierKey = Literal["Alt", "Control", "Meta", "Shift"]
