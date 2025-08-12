"""
웹 자동화 통합 모듈
ID 기반 세션 관리, 로그 기록, 핵심 헬퍼 함수 제공
"""

import os
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, asdict

try:
    from playwright.sync_api import sync_playwright, Browser, Page, Playwright
except ImportError:
    print("⚠️ playwright가 설치되지 않았습니다. pip install playwright")
    Browser = Page = Playwright = None

# ============================================
# 로깅 설정
# ============================================
logger = logging.getLogger("web_automation")
logger.setLevel(logging.INFO)

# 로그 디렉토리
# 프로젝트 절대 경로 기준 로그 디렉토리
project_root = Path(r"C:\Users\82106\Desktop\ai-coding-brain-mcp")
LOG_DIR = project_root / "logs" / "web_automation"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 파일 핸들러
log_file = LOG_DIR / f"web_{datetime.now():%Y%m%d}.log"
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logger.addHandler(file_handler)

# ============================================
# 데이터 클래스
# ============================================
@dataclass
class SessionInfo:
    """브라우저 세션 정보"""
    session_id: str
    pid: Optional[int] = None
    ws_endpoint: Optional[str] = None
    browser_type: str = "chromium"
    status: str = "active"  # active, closed, error
    created_at: str = ""
    last_activity: str = ""
    metadata: Dict[str, Any] = None

    def to_dict(self):
        return asdict(self)

# ============================================
# 세션 매니저
# ============================================
class SessionManager:
    """ID 기반 세션 관리"""

    def __init__(self, base_dir: str = ".web_sessions"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.sessions: Dict[str, SessionInfo] = {}
        self._load_sessions()

    def _load_sessions(self):
        """저장된 세션 정보 로드"""
        registry_file = self.base_dir / "registry.json"
        if registry_file.exists():
            try:
                with open(registry_file, 'r') as f:
                    data = json.load(f)
                    self.sessions = {
                        sid: SessionInfo(**info) 
                        for sid, info in data.items()
                    }
                logger.info(f"Loaded {len(self.sessions)} sessions")
            except Exception as e:
                logger.error(f"Failed to load sessions: {e}")
                self.sessions = {}

    def _save_sessions(self):
        """세션 정보 저장"""
        registry_file = self.base_dir / "registry.json"
        try:
            data = {
                sid: info.to_dict() 
                for sid, info in self.sessions.items()
            }
            with open(registry_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved {len(self.sessions)} sessions")
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")

    def save(self, session_info: SessionInfo):
        """세션 저장"""
        self.sessions[session_info.session_id] = session_info
        self._save_sessions()
        logger.info(f"Session saved: {session_info.session_id}")

    def get(self, session_id: str) -> Optional[SessionInfo]:
        """세션 조회"""
        return self.sessions.get(session_id)

    def list_sessions(self) -> List[SessionInfo]:
        """모든 세션 목록"""
        return list(self.sessions.values())

    def update_status(self, session_id: str, status: str):
        """세션 상태 업데이트"""
        if session_id in self.sessions:
            self.sessions[session_id].status = status
            self.sessions[session_id].last_activity = datetime.now().isoformat()
            self._save_sessions()

# ============================================
# 브라우저 매니저
# ============================================
class BrowserManager:
    """브라우저 생명주기 관리"""

    def __init__(self):
        self.session_manager = SessionManager()
        self.playwright: Optional[Playwright] = None
        self.browsers: Dict[str, Browser] = {}
        self.pages: Dict[str, Page] = {}

    def start_browser(self, 
                     session_id: str = None,
                     browser_type: str = "chromium",
                     headless: bool = False,
                     **kwargs) -> str:
        """새 브라우저 시작"""
        if not session_id:
            session_id = f"session_{datetime.now():%Y%m%d_%H%M%S}"

        # 기존 세션 확인
        existing = self.session_manager.get(session_id)
        if existing and existing.session_id in self.browsers:
            logger.info(f"Reusing existing session: {session_id}")
            return session_id

        try:
            # Playwright 초기화
            if not self.playwright:
                self.playwright = sync_playwright().start()

            # 브라우저 시작
            if browser_type == "chromium":
                browser = self.playwright.chromium.launch(headless=headless, **kwargs)
            elif browser_type == "firefox":
                browser = self.playwright.firefox.launch(headless=headless, **kwargs)
            else:
                browser = self.playwright.webkit.launch(headless=headless, **kwargs)

            # 페이지 생성
            page = browser.new_page()

            # 저장
            self.browsers[session_id] = browser
            self.pages[session_id] = page

            # 세션 정보 저장
            session_info = SessionInfo(
                session_id=session_id,
                browser_type=browser_type,
                status="active",
                created_at=datetime.now().isoformat(),
                last_activity=datetime.now().isoformat()
            )
            self.session_manager.save(session_info)

            logger.info(f"Browser started: {session_id}")
            return session_id

        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            raise

    def get_page(self, session_id: str) -> Optional[Page]:
        """페이지 객체 가져오기"""
        return self.pages.get(session_id)

    def close_browser(self, session_id: str):
        """브라우저 종료"""
        if session_id in self.browsers:
            try:
                self.browsers[session_id].close()
                del self.browsers[session_id]
                del self.pages[session_id]
                self.session_manager.update_status(session_id, "closed")
                logger.info(f"Browser closed: {session_id}")
            except Exception as e:
                logger.error(f"Failed to close browser: {e}")

# ============================================
# 전역 인스턴스
# ============================================
_browser_manager = BrowserManager()
_current_session_id = None

# ============================================
# 헬퍼 함수들
# ============================================
def web_start(session_id: str = None, 
              headless: bool = False,
              browser_type: str = "chromium") -> str:
    """브라우저 시작"""
    global _current_session_id
    _current_session_id = _browser_manager.start_browser(
        session_id=session_id,
        browser_type=browser_type,
        headless=headless
    )
    logger.info(f"web_start: {_current_session_id}")
    return _current_session_id

def web_goto(url: str, session_id: str = None) -> bool:
    """페이지 이동"""
    sid = session_id or _current_session_id
    if not sid:
        logger.error("No active session")
        return False

    page = _browser_manager.get_page(sid)
    if page:
        try:
            page.goto(url)
            logger.info(f"web_goto: {url} (session: {sid})")
            return True
        except Exception as e:
            logger.error(f"web_goto failed: {e}")
    return False

def web_click(selector: str, session_id: str = None) -> bool:
    """요소 클릭"""
    sid = session_id or _current_session_id
    page = _browser_manager.get_page(sid)
    if page:
        try:
            page.click(selector)
            logger.info(f"web_click: {selector} (session: {sid})")
            # 코드 생성용 구조화된 로그
            logger.info(f"CODE_GEN: click|{selector}|{sid}")
            return True
        except Exception as e:
            logger.error(f"web_click failed: {e}")
    return False

def web_type(selector: str, text: str, session_id: str = None) -> bool:
    """텍스트 입력"""
    sid = session_id or _current_session_id
    page = _browser_manager.get_page(sid)
    if page:
        try:
            page.type(selector, text)
            logger.info(f"web_type: {selector} (session: {sid})")
            # 코드 생성용 구조화된 로그  
            logger.info(f"CODE_GEN: type|{selector}|{text}|{sid}")
            return True
        except Exception as e:
            logger.error(f"web_type failed: {e}")
    return False

def web_extract(selector: str, session_id: str = None) -> Optional[str]:
    """데이터 추출"""
    sid = session_id or _current_session_id
    page = _browser_manager.get_page(sid)
    if page:
        try:
            element = page.query_selector(selector)
            if element:
                text = element.text_content()
                logger.info(f"web_extract: {selector} -> {len(text)} chars")
                return text
        except Exception as e:
            logger.error(f"web_extract failed: {e}")
    return None

def web_screenshot(path: str = None, session_id: str = None) -> Optional[str]:
    """스크린샷"""
    sid = session_id or _current_session_id
    page = _browser_manager.get_page(sid)
    if page:
        try:
            if not path:
                path = f"screenshot_{datetime.now():%Y%m%d_%H%M%S}.png"
            page.screenshot(path=path)
            logger.info(f"web_screenshot: {path} (session: {sid})")
            return path
        except Exception as e:
            logger.error(f"web_screenshot failed: {e}")
    return None

def web_close(session_id: str = None):
    """브라우저 종료"""
    global _current_session_id
    sid = session_id or _current_session_id
    if sid:
        _browser_manager.close_browser(sid)
        if sid == _current_session_id:
            _current_session_id = None

def web_wait(seconds: float = 1.0, session_id: str = None):
    """대기"""
    sid = session_id or _current_session_id
    page = _browser_manager.get_page(sid)
    if page:
        page.wait_for_timeout(seconds * 1000)
        logger.debug(f"web_wait: {seconds}s")

def web_execute_js(script: str, session_id: str = None) -> Any:
    """JavaScript 실행"""
    sid = session_id or _current_session_id
    page = _browser_manager.get_page(sid)
    if page:
        try:
            result = page.evaluate(script)
            logger.info(f"web_execute_js: executed (session: {sid})")
            return result
        except Exception as e:
            logger.error(f"web_execute_js failed: {e}")
    return None

def web_list_sessions() -> List[Dict]:
    """세션 목록"""
    sessions = _browser_manager.session_manager.list_sessions()
    return [s.to_dict() for s in sessions]

# 추가 함수들은 필요에 따라 구현...

# ============================================
# Facade 네임스페이스
# ============================================
class WebNamespace:
    """Facade 패턴을 위한 네임스페이스"""

    # 함수 매핑
    start = staticmethod(web_start)
    goto = staticmethod(web_goto)
    click = staticmethod(web_click)
    type = staticmethod(web_type)
    extract = staticmethod(web_extract)
    screenshot = staticmethod(web_screenshot)
    close = staticmethod(web_close)
    wait = staticmethod(web_wait)
    execute_js = staticmethod(web_execute_js)
    list_sessions = staticmethod(web_list_sessions)

    # 클래스 접근
    SessionManager = SessionManager
    BrowserManager = BrowserManager

# 전역 네임스페이스 인스턴스
web = WebNamespace()
