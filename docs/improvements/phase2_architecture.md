
## 🏗️ Phase 2: Client-Server 아키텍처 구현

### 2.1 핵심 BrowserManager 클래스 구현

```python
import json
import os
import subprocess
import logging
from datetime import datetime
from typing import Dict, Optional
from playwright.sync_api import sync_playwright, Browser, Page

class ImprovedBrowserManager:
    """세션 ID 기반 브라우저 관리자"""

    def __init__(self, base_dir: str = "browser_sessions"):
        self.base_dir = base_dir
        self.sessions_file = os.path.join(base_dir, "sessions.json")
        self.sessions = self._load_sessions()
        self._ensure_directories()

    def _ensure_directories(self):
        """필요한 디렉토리 생성"""
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "logs"), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "profiles"), exist_ok=True)

    def _load_sessions(self) -> Dict:
        """저장된 세션 정보 로드"""
        if os.path.exists(self.sessions_file):
            with open(self.sessions_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_sessions(self):
        """세션 정보 저장"""
        with open(self.sessions_file, 'w') as f:
            json.dump(self.sessions, f, indent=2)

    def start_browser_server(self, session_id: str, headless: bool = False) -> Dict:
        """독립 브라우저 서버 시작"""
        # 프로필 디렉토리
        profile_dir = os.path.join(self.base_dir, "profiles", session_id)
        os.makedirs(profile_dir, exist_ok=True)

        # 브라우저 서버 시작 명령
        cmd = [
            "npx", "playwright", "launch-server",
            "--browser", "chromium",
            "--port", "0",  # 자동 포트 할당
        ]

        if not headless:
            cmd.append("--headless=false")

        # 프로세스 시작
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # WebSocket 엔드포인트 읽기
        for line in process.stdout:
            if "ws://" in line:
                ws_endpoint = line.strip()
                break

        # 세션 정보 저장
        session_info = {
            "session_id": session_id,
            "pid": process.pid,
            "ws_endpoint": ws_endpoint,
            "profile_dir": profile_dir,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "status": "active"
        }

        self.sessions[session_id] = session_info
        self._save_sessions()

        # 로거 설정
        self._setup_logger(session_id)

        return session_info

    def connect_to_browser(self, session_id: str) -> Optional[Browser]:
        """기존 브라우저에 연결"""
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]
        ws_endpoint = session["ws_endpoint"]

        try:
            playwright = sync_playwright().start()
            browser = playwright.chromium.connect(ws_endpoint)

            # 활동 시간 업데이트
            session["last_activity"] = datetime.now().isoformat()
            self._save_sessions()

            return browser
        except Exception as e:
            logging.error(f"Failed to connect to browser {session_id}: {e}")
            return None

    def _setup_logger(self, session_id: str):
        """세션별 로거 설정"""
        log_file = os.path.join(self.base_dir, "logs", f"{session_id}.log")

        # 세션별 로거
        logger = logging.getLogger(f"web_auto.{session_id}")
        logger.setLevel(logging.INFO)

        # 파일 핸들러
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)

        # 포맷터
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [Session: %(session_id)s] %(message)s'
        )
        fh.setFormatter(formatter)

        # LoggerAdapter로 session_id 자동 주입
        adapter = logging.LoggerAdapter(logger, {'session_id': session_id})

        logger.addHandler(fh)
        return adapter
```

### 2.2 헬퍼 함수 개선

```python
def web_connect(session_id: str, create_new: bool = True) -> Browser:
    """세션 ID로 브라우저 연결 또는 생성"""
    manager = ImprovedBrowserManager()

    # 기존 세션 연결 시도
    browser = manager.connect_to_browser(session_id)

    if browser is None and create_new:
        # 새 브라우저 서버 시작
        session_info = manager.start_browser_server(session_id)
        browser = manager.connect_to_browser(session_id)

    return browser

def web_goto(session_id: str, url: str):
    """세션 ID 기반 페이지 이동"""
    browser = web_connect(session_id, create_new=False)
    if browser:
        page = browser.pages[0] if browser.pages else browser.new_page()
        page.goto(url)

        # 로깅
        logger = logging.getLogger(f"web_auto.{session_id}")
        logger.info(f"Navigated to {url}")

def web_click(session_id: str, selector: str):
    """세션 ID 기반 클릭"""
    browser = web_connect(session_id, create_new=False)
    if browser:
        page = browser.pages[0]
        page.click(selector)

        # 로깅
        logger = logging.getLogger(f"web_auto.{session_id}")
        logger.info(f"Clicked on {selector}")
```

### 2.3 세션 재연결 테스트

```python
# 세션 1: 브라우저 시작
browser1 = web_connect("user123", create_new=True)
web_goto("user123", "https://example.com")

# 세션 2: 다른 REPL에서 재연결
browser2 = web_connect("user123", create_new=False)  # 기존 브라우저 재사용
web_click("user123", "button.submit")

# 로그 확인
# logs/web_automation/user123.log
```
