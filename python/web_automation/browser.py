"""
웹 자동화 브라우저 관리
BrowserManager와 SessionRegistry 통합
WebAutomation 래퍼 클래스 제공
"""

import os
import json
import subprocess
import logging
from datetime import datetime
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, asdict
import psutil
import re

try:
    from playwright.sync_api import sync_playwright, Browser, Page
except ImportError:
    print("⚠️ playwright가 설치되지 않았습니다. pip install playwright")
    Browser = None
    Page = None

# ============ SessionInfo 데이터 클래스 ============
@dataclass
class SessionInfo:
    """브라우저 세션 정보"""
    session_id: str
    pid: int
    ws_endpoint: str
    browser_type: str
    status: str  # active, terminated, orphaned
    created_at: str
    last_activity: str
    metadata: Dict[str, Any] = None

# ============ SessionRegistry 클래스 ============
class SessionRegistry:
    """세션 정보 영속화 관리"""

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.registry_file = os.path.join(base_dir, "registry.json")
        self.sessions: Dict[str, SessionInfo] = {}
        self._load_sessions()

    def _load_sessions(self):
        """저장된 세션 정보 로드"""
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, 'r') as f:
                    data = json.load(f)
                    self.sessions = {
                        sid: SessionInfo(**info) 
                        for sid, info in data.items()
                    }
            except Exception as e:
                print(f"레지스트리 로드 오류: {e}")
                self.sessions = {}

    def _save_sessions(self):
        """세션 정보 저장"""
        try:
            data = {
                sid: asdict(info) 
                for sid, info in self.sessions.items()
            }
            with open(self.registry_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"레지스트리 저장 오류: {e}")

    def save_session(self, session_info: SessionInfo):
        """세션 정보 저장"""
        self.sessions[session_info.session_id] = session_info
        self._save_sessions()

    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """세션 정보 조회"""
        return self.sessions.get(session_id)

    def update_status(self, session_id: str, status: str):
        """세션 상태 업데이트"""
        if session_id in self.sessions:
            self.sessions[session_id].status = status
            self._save_sessions()

    def list_sessions(self) -> List[SessionInfo]:
        """모든 세션 목록"""
        return list(self.sessions.values())

# ============ BrowserManager 클래스 ============
class BrowserManager:
    """중앙 집중식 브라우저 관리자"""

    def __init__(self, base_dir: str = "browser_sessions"):
        self.base_dir = os.path.abspath(base_dir)
        self.registry = SessionRegistry(self.base_dir)
        self.logger = self._setup_logger()
        self._ensure_directories()
        self._recover_orphans()

    def _ensure_directories(self):
        """필수 디렉토리 생성"""
        dirs = ["profiles", "logs", "activities", "traces"]
        for dir_name in dirs:
            os.makedirs(os.path.join(self.base_dir, dir_name), exist_ok=True)

    def _setup_logger(self) -> logging.Logger:
        """로거 설정"""
        logger = logging.getLogger("BrowserManager")
        logger.setLevel(logging.INFO)

        # 파일 핸들러
        fh = logging.FileHandler(
            os.path.join(self.base_dir, "manager.log")
        )
        fh.setFormatter(logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s'
        ))
        logger.addHandler(fh)

        return logger

    def create_session(self, 
                      session_id: str,
                      browser_type: str = "chromium",
                      headless: bool = False,
                      **kwargs) -> SessionInfo:
        """새 브라우저 서버 시작"""

        # 기존 세션 확인
        existing = self.registry.get_session(session_id)
        if existing and self._is_alive(existing.pid):
            self.logger.warning(f"Session {session_id} already exists")
            return existing

        # 프로필 디렉토리
        profile_dir = os.path.join(self.base_dir, "profiles", session_id)
        os.makedirs(profile_dir, exist_ok=True)

        # 브라우저 서버 시작
        ws_endpoint, pid = self._launch_browser_server(
            browser_type, headless, profile_dir, **kwargs
        )

        # 세션 정보 생성
        session_info = SessionInfo(
            session_id=session_id,
            pid=pid,
            ws_endpoint=ws_endpoint,
            created_at=datetime.now().isoformat(),
            last_activity=datetime.now().isoformat(),
            status="active",
            browser_type=browser_type,
            headless=headless,
            profile_dir=profile_dir,
            log_file=os.path.join(self.base_dir, "logs", f"{session_id}.log")
        )

        # 레지스트리에 저장
        self.registry.save_session(session_info)

        # 활동 로거 초기화
        activity_logger = ActivityLogger(session_id, self.base_dir)
        activity_logger.log_action("session_created", {
            "browser_type": browser_type,
            "headless": headless
        })

        self.logger.info(f"Created session {session_id} with PID {pid}")
        return session_info

    def _launch_browser_server(self, 
                              browser_type: str,
                              headless: bool,
                              profile_dir: str,
                              **kwargs) -> tuple[str, int]:
        """브라우저 서버 프로세스 시작"""

        # 명령어 구성
        cmd = [
            "npx", "playwright", "launch-server",
       


# ============ WebAutomation 통합 인터페이스 ============
class WebAutomation:
    """
    통합 웹 자동화 인터페이스
    BrowserManager와 헬퍼 함수를 결합한 단순 API
    """

    def __init__(self, session_id: str = None, headless: bool = False):
        """
        Args:
            session_id: 세션 ID (재사용 가능)
            headless: 헤드리스 모드 여부
        """
        self.session_id = session_id or f"web_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.headless = headless
        self.manager = BrowserManager()
        self.browser = None
        self.page = None
        self.playwright = None

    def start(self, browser_type: str = "chromium"):
        """브라우저 시작"""
        try:
            # 기존 세션 확인
            existing = self.manager.registry.get_session(self.session_id)
            if existing and self.manager._is_alive(existing.pid):
                # 기존 세션 재사용
                self.browser = self.manager.connect(self.session_id)
                if self.browser:
                    self.page = self.browser.pages[0] if self.browser.pages else self.browser.new_page()
                    return True

            # 새 세션 생성
            session_info = self.manager.create_session(
                self.session_id,
                browser_type,
                self.headless
            )

            # 브라우저 연결
            self.browser = self.manager.connect(self.session_id)
            if self.browser:
                self.page = self.browser.new_page()
                return True

        except Exception as e:
            print(f"브라우저 시작 실패: {e}")
            return False

    def goto(self, url: str, timeout: int = 30000):
        """페이지 이동"""
        if not self.page:
            print("브라우저가 시작되지 않았습니다")
            return False

        try:
            self.page.goto(url, timeout=timeout)
            return True
        except Exception as e:
            print(f"페이지 이동 실패: {e}")
            return False

    def click(self, selector: str):
        """요소 클릭"""
        if not self.page:
            return False

        try:
            self.page.click(selector)
            return True
        except Exception as e:
            print(f"클릭 실패: {e}")
            return False

    def type(self, selector: str, text: str):
        """텍스트 입력"""
        if not self.page:
            return False

        try:
            self.page.type(selector, text)
            return True
        except Exception as e:
            print(f"입력 실패: {e}")
            return False

    def extract(self, selector: str) -> Optional[str]:
        """데이터 추출"""
        if not self.page:
            return None

        try:
            element = self.page.query_selector(selector)
            if element:
                return element.text_content()
        except Exception as e:
            print(f"추출 실패: {e}")
        return None

    def screenshot(self, path: str = None):
        """스크린샷"""
        if not self.page:
            return None

        try:
            if not path:
                path = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            self.page.screenshot(path=path)
            return path
        except Exception as e:
            print(f"스크린샷 실패: {e}")
            return None

    def close(self):
        """브라우저 종료"""
        try:
            if self.browser:
                self.browser.close()
            self.manager.terminate_session(self.session_id)
        except Exception as e:
            print(f"종료 중 오류: {e}")

    def __enter__(self):
        """컨텍스트 매니저 진입"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.close()

# ============ 하위 호환성 별칭 ============
WebBrowser = WebAutomation  # 별칭
