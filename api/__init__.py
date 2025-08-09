"""
웹 자동화 시스템 API
Client-Server 아키텍처 기반 브라우저 관리
"""

from .browser_manager import BrowserManager, SessionInfo
from .session_registry import SessionRegistry
from .activity_logger import ActivityLogger

__all__ = [
    'BrowserManager',
    'SessionInfo',
    'SessionRegistry',
    'ActivityLogger'
]

__version__ = '2.0.0'
