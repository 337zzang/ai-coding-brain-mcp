"""
웹 브라우저 세션 관리 - Persistent Context 버전
REPL 재시작 후에도 재연결 가능한 브라우저 세션 관리

테스트 완료: 2025-08-06
- REPL 프로세스 재시작 후에도 세션 복원 가능
- 쿠키, 로그인 상태 등 모두 유지됨
"""

import os
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

# 세션 저장 디렉토리
BASE_DIR = Path(".browser_sessions")
BASE_DIR.mkdir(exist_ok=True)

def _session_dir(session_id: str) -> Path:
    """세션별 프로필 디렉토리"""
    return BASE_DIR / session_id

def _meta_path(session_id: str) -> Path:
    """세션 메타데이터 파일 경로"""
    return BASE_DIR / f"{session_id}.json"

def open_session(session_id: str = "default",
                 headless: bool = False,
                 url: Optional[str] = None) -> Tuple[BrowserContext, Page]:
    """
    Persistent Context 세션 열기

    Args:
        session_id: 세션 식별자
        headless: 헤드리스 모드 여부
        url: 초기 URL

    Returns:
        (context, page) 튜플
    """
    print(f"🚀 세션 열기: {session_id}")

    # 프로필 디렉토리 생성
    profile_dir = _session_dir(session_id)
    profile_dir.mkdir(exist_ok=True)

    # Playwright 시작
    playwright = sync_playwright().start()

    # Persistent Context 실행
    context = playwright.chromium.launch_persistent_context(
        user_data_dir=str(profile_dir),
        headless=headless,
        args=['--start-maximized'],
        viewport=None  # 전체 화면 사용
    )

    # 페이지 가져오기 또는 생성
    if context.pages:
        page = context.pages[0]
        print(f"   기존 페이지 사용: {page.url}")
    else:
        page = context.new_page()
        print(f"   새 페이지 생성")

    # URL로 이동
    if url:
        page.goto(url)
        print(f"   이동: {url}")

    # 메타데이터 저장
    meta = {
        "session_id": session_id,
        "profile_dir": str(profile_dir),
        "created_at": time.time(),
        "pid": os.getpid(),
        "url": page.url
    }

    with open(_meta_path(session_id), "w") as f:
        json.dump(meta, f, indent=2)

    # playwright 인스턴스도 함께 저장 (close_session에서 사용)
    context._playwright = playwright

    return context, page

def close_session(session_id: str = "default", keep_profile: bool = True):
    """
    세션 종료

    Args:
        session_id: 세션 식별자
        keep_profile: 프로필 유지 여부
    """
    print(f"🔚 세션 종료: {session_id}")

    # 프로필 삭제 옵션
    if not keep_profile:
        import shutil
        profile_dir = _session_dir(session_id)
        if profile_dir.exists():
            shutil.rmtree(profile_dir)
            print(f"   프로필 삭제됨: {profile_dir}")

    # 메타데이터 삭제
    meta_path = _meta_path(session_id)
    if meta_path.exists():
        meta_path.unlink()
        print(f"   메타데이터 삭제됨")

def reconnect_session(session_id: str = "default") -> Tuple[BrowserContext, Page]:
    """
    기존 세션에 재연결 (REPL 재시작 후 사용)

    Args:
        session_id: 세션 식별자

    Returns:
        (context, page) 튜플
    """
    print(f"🔄 세션 재연결: {session_id}")

    # 메타데이터 읽기
    meta_path = _meta_path(session_id)
    if meta_path.exists():
        with open(meta_path, "r") as f:
            meta = json.load(f)
        print(f"   이전 세션 정보:")
        print(f"   - PID: {meta.get('pid')}")
        print(f"   - URL: {meta.get('url')}")

    # open_session 호출 (동일한 프로필 사용)
    return open_session(session_id)

def list_sessions() -> list:
    """활성 세션 목록"""
    sessions = []

    for meta_file in BASE_DIR.glob("*.json"):
        try:
            with open(meta_file, "r") as f:
                meta = json.load(f)
                sessions.append({
                    "session_id": meta.get("session_id"),
                    "profile_dir": meta.get("profile_dir"),
                    "created_at": meta.get("created_at"),
                    "pid": meta.get("pid"),
                    "url": meta.get("url")
                })
        except:
            pass

    return sessions

# 간단한 래퍼 클래스
class PersistentSession:
    """간편한 세션 관리 클래스"""

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.context = None
        self.page = None
        self.playwright = None

    def start(self, url: Optional[str] = None):
        """세션 시작"""
        self.context, self.page = open_session(self.session_id, url=url)
        self.playwright = self.context._playwright
        return self.page

    def stop(self, keep_profile: bool = True):
        """세션 종료"""
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()
        close_session(self.session_id, keep_profile)

    def reconnect(self):
        """세션 재연결"""
        self.context, self.page = reconnect_session(self.session_id)
        self.playwright = self.context._playwright
        return self.page

    def goto(self, url: str):
        """페이지 이동"""
        if self.page:
            self.page.goto(url)

    def screenshot(self, path: str = None):
        """스크린샷"""
        if self.page:
            path = path or f"{self.session_id}.png"
            self.page.screenshot(path=path)
            return path

if __name__ == "__main__":
    # 테스트 코드
    print("웹 세션 테스트")

    # 세션 시작
    session = PersistentSession("test")
    page = session.start("https://www.google.com")
    print(f"페이지 열림: {page.url}")

    # 작업 수행
    page.fill('textarea[name="q"], input[name="q"]', "Persistent Session Test")

    # 세션 종료
    session.stop()
    print("세션 종료됨 - REPL 재시작 후 reconnect() 가능")
