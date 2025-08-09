import os
import json
import subprocess
import logging
from datetime import datetime
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
from playwright.sync_api import sync_playwright, Browser
import psutil  # 프로세스 관리용

@dataclass
class SessionInfo:
    session_id: str
    pid: int
    ws_endpoint: str
    created_at: str
    last_activity: str
    status: str  # "active", "terminated", "orphan"
    browser_type: str = "chromium"
    headless: bool = False
    profile_dir: Optional[str] = None
    log_file: Optional[str] = None

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
            f"--browser={browser_type}",
            "--port=0"  # 자동 포트 할당
        ]

        if not headless:
            cmd.append("--no-headless")

        # Windows 특별 처리
        if os.name == 'nt':
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            creation_flags = 0

        # 프로세스 시작
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=creation_flags,
            cwd=self.base_dir
        )

        # WebSocket 엔드포인트 읽기
        ws_endpoint = None
        for line in process.stdout:
            if "ws://" in line:
                # 엔드포인트 추출
                import re
                match = re.search(r'ws://[^\s]+', line)
                if match:
                    ws_endpoint = match.group()
                    break

        if not ws_endpoint:
            process.terminate()
            raise RuntimeError("Failed to get WebSocket endpoint")

        return ws_endpoint, process.pid

    def connect(self, session_id: str) -> Optional[Browser]:
        """기존 브라우저에 연결"""

        session_info = self.registry.get_session(session_id)
        if not session_info:
            self.logger.error(f"Session {session_id} not found")
            return None

        if not self._is_alive(session_info.pid):
            self.logger.error(f"Session {session_id} process is dead")
            self.registry.update_status(session_id, "terminated")
            return None

        try:
            # Playwright 연결
            playwright = sync_playwright().start()
            browser = playwright.chromium.connect(session_info.ws_endpoint)

            # 활동 시간 업데이트
            self.registry.update_activity(session_id)

            # 활동 로깅
            activity_logger = ActivityLogger(session_id, self.base_dir)
            activity_logger.log_action("connected", {})

            self.logger.info(f"Connected to session {session_id}")
            return browser

        except Exception as e:
            self.logger.error(f"Failed to connect to {session_id}: {e}")
            return None

    def terminate_session(self, session_id: str, force: bool = False):
        """브라우저 종료"""

        session_info = self.registry.get_session(session_id)
        if not session_info:
            return

        # 프로세스 종료
        if self._is_alive(session_info.pid):
            try:
                process = psutil.Process(session_info.pid)
                if force:
                    process.kill()
                else:
                    process.terminate()
                process.wait(timeout=5)
            except Exception as e:
                self.logger.error(f"Failed to terminate {session_id}: {e}")

        # 레지스트리 업데이트
        self.registry.update_status(session_id, "terminated")

        # 활동 로깅
        activity_logger = ActivityLogger(session_id, self.base_dir)
        activity_logger.log_action("session_terminated", {"force": force})

        self.logger.info(f"Terminated session {session_id}")

    def list_sessions(self, active_only: bool = True) -> List[SessionInfo]:
        """세션 목록 조회"""

        sessions = self.registry.list_sessions()

        if active_only:
            # 활성 세션만 필터링
            active_sessions = []
            for session in sessions:
                if self._is_alive(session.pid):
                    active_sessions.append(session)
                else:
                    # 죽은 세션 상태 업데이트
                    self.registry.update_status(session.session_id, "terminated")

            return active_sessions

        return sessions

    def _is_alive(self, pid: int) -> bool:
        """프로세스 생존 확인"""
        try:
            process = psutil.Process(pid)
            return process.is_running()
        except psutil.NoSuchProcess:
            return False

    def _recover_orphans(self):
        """고아 프로세스 복구"""

        orphans = self.registry.find_orphans()
        for session_info in orphans:
            if self._is_alive(session_info.pid):
                # 프로세스가 살아있으면 복구
                self.registry.update_status(session_info.session_id, "active")
                self.logger.info(f"Recovered orphan session {session_info.session_id}")
            else:
                # 죽은 프로세스는 정리
                self.registry.update_status(session_info.session_id, "terminated")
                self.logger.info(f"Cleaned dead session {session_info.session_id}")
