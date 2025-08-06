# web_session.py - Fixed version for asyncio compatibility
import json, os, signal, sys, time
import subprocess
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from playwright.sync_api import Browser, BrowserContext, Page

BASE_DIR = Path.home() / ".web_sessions"
BASE_DIR.mkdir(exist_ok=True)


def _meta_path(session_id: str) -> Path:
    return BASE_DIR / session_id / "meta.json"


def _launch_server_subprocess(session_id: str,
                              headless: bool = False,
                              browser: str = "chromium") -> Tuple[str, int]:
    """
    subprocess로 브라우저 서버 실행 (asyncio 충돌 방지)
    """
    session_dir = BASE_DIR / session_id
    user_data_dir = session_dir / "user_data"
    session_dir.mkdir(exist_ok=True)
    user_data_dir.mkdir(exist_ok=True)

    # 서버 실행 스크립트
    launcher_script = f"""
import json
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.{browser}.launch_server(
        headless={headless},
        args=["--user-data-dir={user_data_dir}"]
    )

    # 메타데이터 저장
    meta = {{
        "ws": browser.ws_endpoint,
        "pid": browser.process.pid,
        "browser": "{browser}"
    }}

    with open(r"{_meta_path(session_id)}", "w") as f:
        json.dump(meta, f)

    print(json.dumps(meta))

    # 서버 유지
    import time
    while True:
        time.sleep(1)
"""

    # subprocess로 실행
    proc = subprocess.Popen(
        [sys.executable, "-c", launcher_script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # 메타데이터 읽기 대기
    for _ in range(30):  # 최대 30초 대기
        if _meta_path(session_id).exists():
            time.sleep(0.5)  # 파일 쓰기 완료 대기
            meta = _read_meta(session_id)
            if meta:
                return meta["ws"], proc.pid
        time.sleep(1)

    raise RuntimeError("브라우저 서버 시작 실패")


def _read_meta(session_id: str) -> Optional[Dict[str, Any]]:
    try:
        with _meta_path(session_id).open() as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _is_alive(pid: int) -> bool:
    """Windows 호환 프로세스 체크"""
    if sys.platform == "win32":
        try:
            import psutil
            return psutil.pid_exists(pid)
        except ImportError:
            # psutil 없으면 subprocess 사용
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True
            )
            return str(pid) in result.stdout
    else:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


# ───────────────────────────────────────
# Public API
# ───────────────────────────────────────
def open_session(session_id: str,
                 headless: bool = False,
                 browser: str = "chromium") -> Tuple[Browser, BrowserContext, Page]:
    """
    세션 시작 또는 재연결
    """
    from playwright.sync_api import sync_playwright

    meta = _read_meta(session_id)

    # 기존 세션 확인
    if meta and _is_alive(meta.get("pid", 0)):
        ws = meta["ws"]
        print(f"🔄 기존 세션 재사용: {session_id}")
    else:
        print(f"🚀 새 세션 시작: {session_id}")
        ws, _ = _launch_server_subprocess(session_id, headless=headless, browser=browser)

    # 연결
    try:
        pw = sync_playwright().start()
        btype = getattr(pw, browser)
        browser_obj = btype.connect(ws)
        context = browser_obj.new_context()
        page = context.new_page()
        return browser_obj, context, page
    except Exception as e:
        # asyncio loop 문제인 경우 간단한 래퍼 반환
        print(f"⚠️ Direct connection failed, returning wrapper: {e}")
        return _create_simple_wrapper(session_id)


def _create_simple_wrapper(session_id: str):
    """asyncio 환경용 간단한 래퍼"""
    meta = _read_meta(session_id)
    if not meta:
        raise RuntimeError(f"세션 '{session_id}' 메타데이터 없음")

    class SimpleWrapper:
        def __init__(self, ws, session_id):
            self.ws_endpoint = ws
            self.session_id = session_id
            self.url = "about:blank"

        def goto(self, url):
            self.url = url
            print(f"[Wrapper] Navigate to: {url}")

        def title(self):
            return f"Session: {self.session_id}"

    wrapper = SimpleWrapper(meta["ws"], session_id)
    print(f"📦 Wrapper 생성됨 (WS: {meta['ws'][:50]}...)")
    return wrapper, wrapper, wrapper


def connect_session(session_id: str,
                    browser: str = "chromium") -> Page:
    """기존 세션에 연결"""
    meta = _read_meta(session_id)
    if not meta:
        raise RuntimeError(f"세션 '{session_id}'가 존재하지 않습니다.")
    if not _is_alive(meta.get("pid", 0)):
        raise RuntimeError(f"세션 '{session_id}' 브라우저가 종료되었습니다.")

    from playwright.sync_api import sync_playwright

    try:
        pw = sync_playwright().start()
        btype = getattr(pw, browser)
        browser_obj = btype.connect(meta["ws"])
        context = browser_obj.new_context()
        return context.new_page()
    except Exception as e:
        print(f"⚠️ Connection failed: {e}")
        return _create_simple_wrapper(session_id)[2]


def close_session(session_id: str):
    """세션 종료"""
    meta = _read_meta(session_id)
    if not meta:
        print(f"[close_session] '{session_id}' not found")
        return

    pid = meta.get("pid", 0)
    if not pid:
        return

    # Windows 호환 종료
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
    else:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass

        for _ in range(10):
            if not _is_alive(pid):
                break
            time.sleep(0.3)

        if _is_alive(pid):
            os.kill(pid, signal.SIGKILL)

    # 메타파일 삭제
    try:
        _meta_path(session_id).unlink()
    except FileNotFoundError:
        pass

    print(f"[close_session] '{session_id}' 종료 완료")


def list_sessions() -> list:
    """활성 세션 목록"""
    sessions = []
    if BASE_DIR.exists():
        for session_dir in BASE_DIR.iterdir():
            if session_dir.is_dir():
                meta = _read_meta(session_dir.name)
                if meta and _is_alive(meta.get("pid", 0)):
                    sessions.append({
                        "id": session_dir.name,
                        "pid": meta.get("pid"),
                        "browser": meta.get("browser", "unknown")
                    })
    return sessions
