# web_session.py
import json, os, signal, subprocess, sys, time
from pathlib import Path
from typing import Tuple
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

BASE_DIR = Path.home() / ".web_sessions"
BASE_DIR.mkdir(exist_ok=True)


def _meta_path(session_id: str) -> Path:
    return BASE_DIR / session_id / "meta.json"


def _launch_server(session_id: str,
                   headless: bool = False,
                   browser: str = "chromium") -> Tuple[str, int]:
    """
    새 브라우저 서버를 띄우고 WS endpoint, pid 반환
    """
    session_dir = BASE_DIR / session_id
    user_data_dir = session_dir / "user_data"
    session_dir.mkdir(exist_ok=True)
    user_data_dir.mkdir(exist_ok=True)

    with sync_playwright() as p:
        btype = getattr(p, browser)
        # 1) 서버 모드로 실행
        server = btype.launch_server(
            headless=headless,
            args=[f"--user-data-dir={user_data_dir}"]
        )
        ws = server.ws_endpoint
        pid = server.process.pid

        # 2) 메타데이터 저장
        with _meta_path(session_id).open("w") as f:
            json.dump({"ws": ws, "pid": pid, "browser": browser}, f)

    return ws, pid


def _read_meta(session_id: str) -> dict | None:
    try:
        with _meta_path(session_id).open() as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def _is_alive(pid: int) -> bool:
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
                 browser: str = "chromium"
                 ) -> Tuple[Browser, BrowserContext, Page]:
    """
    ① 이미 살아있는 세션이면 connect
    ② 없으면 launch → connect
    """
    meta = _read_meta(session_id)

    # 1. 살아있는 세션?
    if meta and _is_alive(meta["pid"]):
        ws = meta["ws"]
    else:
        ws, _ = _launch_server(session_id, headless=headless, browser=browser)

    # 2. 이제 연결
    pw = sync_playwright().start()
    btype = getattr(pw, browser)
    browser_obj = btype.connect(ws)
    # launch_server 로 띄웠으므로 persistent context X → 새 context 필요
    context = browser_obj.new_context()
    page = context.new_page()
    return browser_obj, context, page


def connect_session(session_id: str,
                    browser: str = "chromium") -> Page:
    """메타 정보만 있으면 바로 page 객체 반환"""
    meta = _read_meta(session_id)
    if not meta:
        raise RuntimeError(f"세션 '{session_id}'가 존재하지 않습니다. 먼저 open_session을 호출하세요.")
    if not _is_alive(meta["pid"]):
        raise RuntimeError(f"세션 '{session_id}' 브라우저가 종료되었습니다. open_session으로 재시작하세요.")

    pw = sync_playwright().start()
    btype = getattr(pw, browser)
    browser_obj = btype.connect(meta["ws"])
    context = browser_obj.new_context()
    return context.new_page()


def close_session(session_id: str):
    """
    • page.close 가 아니라 '브라우저 프로세스'를 종료
    • PID 가 종료되지 않으면 SIGTERM → SIGKILL
    """
    meta = _read_meta(session_id)
    if not meta:
        print(f"[close_session] '{session_id}' not found")
        return

    pid = meta["pid"]
    # 1) 정상 종료 시도
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

    # 2) 메타파일 삭제
    try:
        _meta_path(session_id).unlink()
    except FileNotFoundError:
        pass

    print(f"[close_session] '{session_id}' 종료 완료")
