아래 코드는 “하나의 브라우저 서버를 여러 프로세스에서 재연결해서 쓰는” 것을 목표로, 운영체제(특히 Windows) 특화 처리, 세션 레지스트리(SQLite), 로깅, 헬스체크/재연결/정리까지 포함한 실제 운영 가능한 예제입니다.

중요한 전제
- cross‑process 안정성: Python의 browser_type.launch_server()는 현재 Python 프로세스/Playwright 드라이버 생명주기에 묶입니다. 즉, 매니저 프로세스가 죽으면 서버도 같이 종료될 위험이 큽니다. 반면 playwright launch-server CLI를 별도 OS 프로세스로 띄우면 부모가 죽어도 브라우저 서버는 살아남을 수 있어 “고아 세션 adopt”가 가능합니다. 따라서 실제 운영에서는 subprocess로 playwright launch-server를 띄우는 방식을 권장합니다.
- 페이지 공유 한계: Playwright BrowserServer에 다중 클라이언트가 연결해도 각 클라이언트가 만든 Context/Page는 다른 클라이언트에서 보이지 않습니다. 즉 REPL2에서 REPL1이 만든 page를 browser2.pages[0]로 바로 “가져오기”는 기본 프로토콜로 불가합니다. 같은 “브라우저”를 공유하되 각 클라이언트는 자신의 컨텍스트/페이지를 만듭니다. 다른 프로세스에서 기존 탭을 붙잡아야 한다면 Chromium + CDP(connect_over_cdp) 또는 단일 매니저 프로세스가 모든 동작을 중개하도록 설계해야 합니다.

1) launch_server 구현: Python API vs subprocess 방식
A. Python API (주의: 매니저가 죽으면 서버도 같이 죽을 수 있음)

```python
from playwright.sync_api import sync_playwright

def start_browser_server_python_api(browser_type: str = "chromium"):
    p = sync_playwright().start()
    bt = getattr(p, browser_type)  # p.chromium / p.firefox / p.webkit
    server = bt.launch_server()    # returns BrowserServer
    ws_endpoint = server.ws_endpoint
    # 주의: p(Playwright)와 server 객체 수명에 종속적.
    return p, server, ws_endpoint  # p.stop() 또는 server.close() 호출 시 서버 종료
```

B. subprocess로 playwright launch-server 실행(권장: 프로세스 독립성 보장)

아래는 stdout에서 ws:// 엔드포인트를 정확히 파싱하고, 출력 대기 로직과 Windows/Linux 차이를 반영한 함수입니다.

```python
import os, sys, re, time, signal, platform, subprocess, threading, queue

_WS_RE = re.compile(r'(?P<ws>(?:ws|wss)://[^\s"\'<>]+)')

class _StreamReader(threading.Thread):
    def __init__(self, stream, out_queue, logger=None, name="stdout"):
        super().__init__(daemon=True)
        self.stream = stream
        self.out_queue = out_queue
        self.logger = logger
        self.name = name

    def run(self):
        try:
            for line in iter(self.stream.readline, ''):
                if not line:
                    break
                if self.logger:
                    self.logger.debug(f"{self.name}: {line.rstrip()}")
                self.out_queue.put(line)
        except Exception as e:
            if self.logger:
                self.logger.exception(f"Reader thread error ({self.name}): {e}")

def _windows_creation():
    # Windows: 새로운 프로세스 그룹으로 실행하면 CTRL_BREAK_EVENT로 그룹 전체에 신호 전송 가능
    flags = 0
    try:
        flags |= subprocess.CREATE_NEW_PROCESS_GROUP
        flags |= subprocess.CREATE_NO_WINDOW  # 콘솔 창 숨김(서비스/백그라운드에 적합)
    except Exception:
        pass
    si = None
    # 선택: 콘솔 창 숨김을 더 확실히 하고 싶으면 STARTUPINFO 사용
    # import subprocess
    # si = subprocess.STARTUPINFO()
    # si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    # si.wShowWindow = 0
    return flags, si

def _posix_popen_kwargs():
    # POSIX: 새로운 세션으로 시작하여 프로세스 그룹 신호 제어
    kwargs = {}
    if hasattr(os, "setsid"):
        kwargs["preexec_fn"] = os.setsid
    else:
        # Python 3.9+: start_new_session=True 대체
        kwargs["start_new_session"] = True
    return kwargs

def start_browser_server(session_id: str,
                         browser_type: str = "chromium",
                         port: int = 0,
                         env: dict | None = None,
                         logger=None,
                         timeout_sec: float = 30.0) -> dict:
    """
    subprocess로 `playwright launch-server <browser>` 실행,
    stdout에서 ws_endpoint 파싱 후 반환.
    반환 예: {"pid": pid, "ws_endpoint": "...", "port": 12345, "browser_type": "chromium"}
    """
    cmd = [sys.executable, "-m", "playwright", "launch-server", browser_type]
    if port and port > 0:
        cmd += ["--port", str(port)]
    else:
        # 0은 OS 임의 포트 할당. (CLI가 0 허용. 미지원 환경이면 생략)
        cmd += ["--port", "0"]

    popen_kwargs = dict(
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
        text=True,
        encoding="utf-8",
        env={**os.environ, **(env or {})},
        shell=False,
    )

    if os.name == "nt":
        flags, si = _windows_creation()
        popen_kwargs["creationflags"] = flags
        if si:
            popen_kwargs["startupinfo"] = si
    else:
        popen_kwargs.update(_posix_popen_kwargs())

    proc = subprocess.Popen(cmd, **popen_kwargs)

    q = queue.Queue()
    stdout_reader = _StreamReader(proc.stdout, q, logger=logger, name="stdout")
    stderr_reader = _StreamReader(proc.stderr, q, logger=logger, name="stderr")
    stdout_reader.start()
    stderr_reader.start()

    ws_endpoint = None
    deadline = time.time() + timeout_sec
    last_err = ""
    while time.time() < deadline:
        try:
            line = q.get(timeout=0.2)
        except queue.Empty:
            if proc.poll() is not None:
                last_err = f"process exited with code {proc.returncode}"
                break
            continue
        if not line:
            continue
        m = _WS_RE.search(line)
        if m:
            ws_endpoint = m.group("ws")
            break

    if not ws_endpoint:
        # 남은 로그를 조금 더 긁어서 에러 힌트 확보
        try:
            # non-blocking으로 잠깐만
            start = time.time()
            while time.time() - start < 0.5:
                try:
                    line = q.get_nowait()
                    last_err += line
                except queue.Empty:
                    break
        except Exception:
            pass
        try:
            proc.terminate()
        except Exception:
            pass
        raise RuntimeError(f"Failed to parse ws endpoint from playwright output: {last_err.strip()}")

    # 포트 파싱
    port_num = None
    try:
        # ws://127.0.0.1:12345/xxxx
        host_port = ws_endpoint.split("://", 1)[1].split("/", 1)[0]
        if ":" in host_port:
            port_num = int(host_port.rsplit(":", 1)[-1])
    except Exception:
        pass

    return {
        "session_id": session_id,
        "pid": proc.pid,
        "ws_endpoint": ws_endpoint,
        "port": port_num,
        "browser_type": browser_type,
        # 참고: proc 핸들은 이 함수 밖에서 보관/관리하거나 pid만 기록하고 필요 시 psutil로 제어
        "_proc": proc,
    }
```

2) Windows 특화 처리
- CREATE_NEW_PROCESS_GROUP 사용: 위 start_browser_server에서 creationflags로 설정.
- 종료 시 taskkill 대신:
  - CTRL_BREAK_EVENT 보내기(가장 부드러움, 같은 콘솔/새 프로세스 그룹 필요).
  - 실패 시 TerminateProcess(proc.terminate()) 또는 psutil로 자식 포함 종료.
- 방화벽: 기본적으로 127.0.0.1(루프백) 바인딩이면 Windows Defender가 막지 않습니다. 외부에서 접속하려고 0.0.0.0 바인딩을 쓰면 관리자 권한으로 netsh 규칙 추가가 필요합니다.

아래는 종료/방화벽 유틸입니다.

```python
import signal, subprocess, time, contextlib

def graceful_stop_windows(pid: int, logger=None, timeout=5.0):
    try:
        # CTRL_BREAK_EVENT: 같은 콘솔 + CREATE_NEW_PROCESS_GROUP 필요
        os.kill(pid, signal.CTRL_BREAK_EVENT)
        t0 = time.time()
        while time.time() - t0 < timeout:
            if not _is_pid_running(pid):
                return True
            time.sleep(0.2)
    except Exception as e:
        if logger:
            logger.warning(f"CTRL_BREAK_EVENT failed: {e}")

    # fallback: TerminateProcess
    try:
        import psutil  # 권장
        with contextlib.suppress(psutil.NoSuchProcess):
            p = psutil.Process(pid)
            for child in p.children(recursive=True):
                with contextlib.suppress(psutil.NoSuchProcess):
                    child.terminate()
            p.terminate()
            gone, alive = psutil.wait_procs([p], timeout=timeout)
            for a in alive:
                a.kill()
        return True
    except Exception as e:
        if logger:
            logger.warning(f"Terminate fallback failed: {e}")
        # 최후 수단
        try:
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                           check=False, capture_output=True)
            return True
        except Exception:
            return False

def graceful_stop_posix(pid: int, logger=None, timeout=5.0):
    try:
        # start_new_session or setsid로 시작했다면 프로세스 그룹 신호 사용
        pgid = os.getpgid(pid)
        os.killpg(pgid, signal.SIGTERM)
    except Exception:
        try:
            os.kill(pid, signal.SIGTERM)
        except Exception:
            pass
    t0 = time.time()
    while time.time() - t0 < timeout:
        if not _is_pid_running(pid):
            return True
        time.sleep(0.2)
    # force kill
    try:
        pgid = os.getpgid(pid)
        os.killpg(pgid, signal.SIGKILL)
    except Exception:
        try:
            os.kill(pid, signal.SIGKILL)
        except Exception:
            pass
    return not _is_pid_running(pid)

def ensure_firewall_rule_for_port(port: int, rule_name: str = "PlaywrightBrowserServer", logger=None):
    """
    루프백이 아니라 외부 접근(0.0.0.0) 가능하게 열었을 때만 필요.
    관리자 권한 필요. 실패해도 동작에는 영향 없음.
    """
    if os.name != "nt":
        return
    try:
        subprocess.run(
            ["netsh", "advfirewall", "firewall", "add", "rule",
             f"name={rule_name}_{port}", "dir=in", "action=allow",
             "protocol=TCP", f"localport={port}"],
            check=False, capture_output=True, text=True
        )
    except Exception as e:
        if logger:
            logger.warning(f"Firewall rule add failed: {e}")

def _is_pid_running(pid: int) -> bool:
    try:
        import psutil
        return psutil.pid_exists(pid) and psutil.Process(pid).is_running()
    except Exception:
        # Fallback
        if os.name == "nt":
            # No easy non-psutil method; try OpenProcess? keep it simple:
            # assume running if not obviously dead
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False
        else:
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False
```

3) 세션 레지스트리 구현(SQLite 권장)
JSON은 동시성/원자성 문제로 취약합니다. 다프로세스 안정성을 위해 SQLite + WAL 모드 사용을 권장합니다.

```python
import sqlite3, time, json, os, contextlib

class SessionRegistry:
    def __init__(self, storage_path: str):
        """
        storage_path: SQLite 파일 경로
        """
        self.path = storage_path
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        self._init_db()

    def _connect(self):
        con = sqlite3.connect(self.path, timeout=10.0, isolation_level=None)
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute("PRAGMA synchronous=NORMAL;")
        con.row_factory = sqlite3.Row
        return con

    def _init_db(self):
        con = self._connect()
        with con:
            con.execute("""
            CREATE TABLE IF NOT EXISTS sessions(
              session_id TEXT PRIMARY KEY,
              ws_endpoint TEXT NOT NULL,
              pid INTEGER NOT NULL,
              browser_type TEXT NOT NULL,
              port INTEGER,
              status TEXT NOT NULL,            -- running|stale|stopped
              started_at REAL NOT NULL,
              updated_at REAL NOT NULL,
              last_heartbeat REAL,
              os TEXT,
              extra JSON
            );
            """)
            con.execute("CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);")
        con.close()

    def save_session(self, session_info: dict):
        now = time.time()
        fields = {
            "session_id": session_info["session_id"],
            "ws_endpoint": session_info["ws_endpoint"],
            "pid": int(session_info["pid"]),
            "browser_type": session_info.get("browser_type", "chromium"),
            "port": session_info.get("port"),
            "status": session_info.get("status", "running"),
            "started_at": session_info.get("started_at", now),
            "updated_at": now,
            "last_heartbeat": now,
            "os": platform.system(),
            "extra": json.dumps(session_info.get("extra", {}), ensure_ascii=False),
        }
        con = self._connect()
        with con:
            con.execute("""
            INSERT INTO sessions(session_id, ws_endpoint, pid, browser_type, port,
                                 status, started_at, updated_at, last_heartbeat, os, extra)
            VALUES(:session_id, :ws_endpoint, :pid, :browser_type, :port,
                   :status, :started_at, :updated_at, :last_heartbeat, :os, :extra)
            ON CONFLICT(session_id) DO UPDATE SET
              ws_endpoint=excluded.ws_endpoint,
              pid=excluded.pid,
              browser_type=excluded.browser_type,
              port=excluded.port,
              status=excluded.status,
              updated_at=excluded.updated_at,
              last_heartbeat=excluded.last_heartbeat,
              os=excluded.os,
              extra=excluded.extra
            """, fields)
        con.close()

    def get_session(self, session_id: str) -> dict | None:
        con = self._connect()
        with con:
            row = con.execute("SELECT * FROM sessions WHERE session_id=?", (session_id,)).fetchone()
        con.close()
        return dict(row) if row else None

    def list_sessions(self, status: str | None = None) -> list[dict]:
        con = self._connect()
        with con:
            if status:
                rows = con.execute("SELECT * FROM sessions WHERE status=?", (status,)).fetchall()
            else:
                rows = con.execute("SELECT * FROM sessions").fetchall()
        con.close()
        return [dict(r) for r in rows]

    def update_status(self, session_id: str, status: str):
        con = self._connect()
        with con:
            con.execute("UPDATE sessions SET status=?, updated_at=? WHERE session_id=?",
                        (status, time.time(), session_id))
        con.close()

    def delete_session(self, session_id: str):
        con = self._connect()
        with con:
            con.execute("DELETE FROM sessions WHERE session_id=?", (session_id,))
        con.close()

    def heartbeat(self, session_id: str):
        con = self._connect()
        with con:
            con.execute("UPDATE sessions SET last_heartbeat=?, updated_at=? WHERE session_id=?",
                        (time.time(), time.time(), session_id))
        con.close()

    def adopt_orphan_sessions(self) -> list[dict]:
        """
        DB 관점의 고아 세션 처리:
        - pid가 더 이상 살아있지 않으면 status=stale로 표시하고 반환.
        - 프로세스가 살아있으면 그대로 두고 반환하지 않음.
        실제 재연결(adopt)은 Manager에서 수행.
        """
        victims = []
        con = self._connect()
        with con:
            rows = con.execute("SELECT * FROM sessions WHERE status='running'").fetchall()
            for r in rows:
                pid = int(r["pid"])
                if not _is_pid_running(pid):
                    con.execute("UPDATE sessions SET status='stale', updated_at=? WHERE session_id=?",
                                (time.time(), r["session_id"]))
                    victims.append(dict(r))
        con.close()
        return victims
```

4) BrowserManager 전체 구현
- 세션 생성(서버 띄우기) / 연결 / 헬스 체크 / 정리 / adopt
- 로깅 통합

```python
import logging, json
from datetime import datetime
from playwright.sync_api import sync_playwright, Error as PWError

class SessionLogger:
    def __init__(self, session_id: str, base_logdir: str = "./logs"):
        os.makedirs(base_logdir, exist_ok=True)
        self.session_id = session_id
        self.logger = logging.getLogger(f"session.{session_id}")
        self.logger.setLevel(logging.DEBUG)

        # 파일 핸들러 (회전로깅 사용해도 됨)
        fh = logging.FileHandler(os.path.join(base_logdir, f"{session_id}.log"), encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        fh.setFormatter(fmt)
        if not self.logger.handlers:
            self.logger.addHandler(fh)

    def log_action(self, action: str, details: dict | None = None, level="info"):
        record = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "session_id": self.session_id,
            "action": action,
            "details": details or {}
        }
        line = json.dumps(record, ensure_ascii=False)
        getattr(self.logger, level, self.logger.info)(line)

class BrowserManager:
    def __init__(self, storage_path: str = "./data/sessions.db", logdir: str = "./logs"):
        self.registry = SessionRegistry(storage_path)
        self.logdir = logdir
        self._p = None  # Playwright instance
        self._ensure_playwright()

    def _ensure_playwright(self):
        if self._p is None:
            self._p = sync_playwright().start()

    def _get_logger(self, session_id: str) -> SessionLogger:
        return SessionLogger(session_id, base_logdir=self.logdir)

    def create_session(self, session_id: str, browser_type: str = "chromium", port: int = 0) -> dict:
        """
        이미 존재하고 살아있으면 그대로 반환. 아니면 새로 띄움.
        """
        self._ensure_playwright()
        logger = self._get_logger(session_id)
        logger.log_action("create_session.begin", {"browser_type": browser_type, "port": port})

        # 기존 세션 검사
        existing = self.registry.get_session(session_id)
        if existing and existing.get("status") == "running":
            if self._healthcheck_ws(existing["ws_endpoint"]):
                logger.log_action("create_session.reuse", {"ws_endpoint": existing["ws_endpoint"]})
                return existing
            else:
                logger.log_action("create_session.existing_unhealthy", existing)
                # 종료 시도
                self._stop_by_pid(existing["pid"], logger)
                self.registry.update_status(session_id, "stale")

        # 새 서버 시작
        try:
            info = start_browser_server(session_id, browser_type=browser_type, port=port, logger=logger.logger)
        except Exception as e:
            logger.log_action("create_session.failed", {"error": str(e)}, level="error")
            raise

        # 방화벽: 루프백이 아니라면 필요. 여기서는 예시로만.
        # if info.get("port"):
        #     ensure_firewall_rule_for_port(info["port"], logger=logger.logger)

        info["status"] = "running"
        info["started_at"] = time.time()
        self.registry.save_session(info)
        logger.log_action("create_session.success", {"ws_endpoint": info["ws_endpoint"], "pid": info["pid"]})
        return info

    def connect(self, session_id: str, timeout_ms: int = 15000):
        """
        기존 세션의 ws_endpoint로 연결해 Browser 객체 반환.
        """
        self._ensure_playwright()
        s = self.registry.get_session(session_id)
        if not s:
            # DB에 없으면 고아 세션 탐색/정리 시도
            self.registry.adopt_orphan_sessions()
            s = self.registry.get_session(session_id)
            if not s:
                raise RuntimeError(f"Session not found: {session_id}")
        if s["status"] != "running":
            raise RuntimeError(f"Session not running: {session_id} ({s['status']})")
        ws = s["ws_endpoint"]
        logger = self._get_logger(session_id)
        logger.log_action("connect.begin", {"ws_endpoint": ws})
        try:
            browser = self._p.connect(ws_endpoint=ws, timeout=timeout_ms)
            logger.log_action("connect.success", {"version": browser.version, "connected": browser.is_connected()})
            self.registry.heartbeat(session_id)
            return browser
        except PWError as e:
            logger.log_action("connect.failed", {"error": str(e)}, level="error")
            # 고아 세션 시나리오 처리
            if not _is_pid_running(int(s["pid"])):
                self.registry.update_status(session_id, "stale")
            raise

    def _healthcheck_ws(self, ws_endpoint: str, timeout_ms: int = 5000) -> bool:
        try:
            b = self._p.connect(ws_endpoint=ws_endpoint, timeout=timeout_ms)
            # 간단히 연결했다 끊기
            b.close()
            return True
        except Exception:
            return False

    def healthcheck(self, session_id: str) -> bool:
        s = self.registry.get_session(session_id)
        return bool(s and s["status"] == "running" and self._healthcheck_ws(s["ws_endpoint"]))

    def stop(self, session_id: str):
        s = self.registry.get_session(session_id)
        if not s:
            return
        logger = self._get_logger(session_id)
        ok = self._stop_by_pid(int(s["pid"]), logger)
        self.registry.update_status(session_id, "stopped" if ok else "stale")
        logger.log_action("stop", {"ok": ok})

    def _stop_by_pid(self, pid: int, logger: SessionLogger | None):
        if os.name == "nt":
            return graceful_stop_windows(pid, logger=logger.logger if logger else None)
        else:
            return graceful_stop_posix(pid, logger=logger.logger if logger else None)

    def adopt_orphan_sessions(self):
        """
        DB 기준으로 pid 죽은 세션을 stale 처리하고,
        pid 살아있으면 ws 연결 확인 후 running 유지.
        """
        victims = self.registry.adopt_orphan_sessions()
        # 살아있지만 연결 안되는 케이스도 정리
        running = self.registry.list_sessions(status="running")
        for s in running:
            if not self._healthcheck_ws(s["ws_endpoint"]):
                # 프로세스가 살아있어도 WS가 죽었으면 stale 처리 후 종료 시도
                self.registry.update_status(s["session_id"], "stale")
                self._stop_by_pid(int(s["pid"]), self._get_logger(s["session_id"]))

    def cleanup(self):
        """
        정리 작업 (죽은 pid 정리)
        """
        for s in self.registry.list_sessions():
            pid = int(s["pid"])
            if not _is_pid_running(pid):
                self.registry.update_status(s["session_id"], "stale")

    def close(self):
        # 매니저 자체 종료(Playwright 드라이버 종료)
        if self._p is not None:
            try:
                self._p.stop()
            except Exception:
                pass
            self._p = None
```

5) 실제 사용 시나리오
중요: 다른 프로세스에서 기존 페이지를 바로 제어하는 것은 Playwright 프로토콜 특성상 불가합니다. 각 프로세스는 같은 브라우저에 연결하되 자신만의 컨텍스트/페이지를 만듭니다.

REPL 1

```python
# REPL 1
manager = BrowserManager()
session = manager.create_session("user123")  # 브라우저 서버 프로세스 생성 및 ws_endpoint 등록
browser = manager.connect("user123")         # 동일 프로세스 내 연결
page = browser.new_page()
page.goto("https://example.com")
print(page.title())

# 브라우저/프로세스는 독립. manager.close()로 Playwright 드라이버만 종료(서버는 계속 살아있음).
```

REPL 2 (다른 프로세스)

```python
# REPL 2
manager2 = BrowserManager()
browser2 = manager2.connect("user123")  # 레지스트리에서 ws_endpoint를 읽어, 이미 떠 있는 브라우저 서버에 연결
# 주의: REPL1에서 만든 page를 그대로 가져올 수는 없음.
page2 = browser2.new_page()
page2.goto("https://example.com/login")
print(browser2.version)
```

만약 “기존 페이지를 다른 클라이언트에서 제어”가 꼭 필요하다면
- 단일 매니저 프로세스가 모든 Playwright 핸들을 가지고 있고, 나머지 프로세스는 RPC/REST를 통해 명령을 중개하는 구조로 바꾸거나,
- Chromium + CDP(원격 디버깅 포트) 기반(connect_over_cdp)을 고려해야 합니다(이 경우 기존 탭 나열/접속 가능). 하지만 이건 보안/안정성 고려가 더 필요합니다.

6) 로깅 통합
위 SessionLogger는 JSON 라인을 파일로 남깁니다. 공통 로거도 추가하려면 다음처럼 루트 로깅 설정을 넣을 수 있습니다.

```python
def setup_root_logging(level=logging.INFO, logfile="./logs/app.log"):
    os.makedirs(os.path.dirname(logfile) or ".", exist_ok=True)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[
            logging.FileHandler(logfile, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ],
    )

# 앱 시작 시 1회
setup_root_logging()
```

운영 팁
- Playwright/브라우저 버전 고정: CI/배포 시 playwright install chromium 등으로 런타임 일관성.
- 서버 바인딩은 127.0.0.1 권장. 외부 바인딩 시 방화벽/보안 필수.
- 좀비 정리: 주기적으로 manager.cleanup() 또는 adopt_orphan_sessions() 호출(예: 크론/스케줄러).
- Windows 서비스로 실행 시 CTRL_BREAK_EVENT는 콘솔이 없으면 동작하지 않을 수 있습니다. 그 경우 psutil 기반 종료를 기본으로 사용하세요.
- 세션 TTL/자동만료: registry에 TTL/last_heartbeat 등을 두고 기간 경과 시 종료/삭제하도록 확장 가능.

요약
- 실제 프로덕션 용도로는 subprocess로 playwright launch-server를 띄우고, stdout에서 ws_endpoint를 파싱해 SQLite에 등록한 뒤, 다른 프로세스가 registry를 통해 ws_endpoint로 connect하는 패턴이 가장 안전합니다.
- Windows에서는 CREATE_NEW_PROCESS_GROUP으로 시작하고 CTRL_BREAK_EVENT→psutil terminate 순으로 종료를 시도하세요.
- Playwright 프로토콜 특성상 다른 연결에서 기존 페이지를 바로 가져오는 것은 지원되지 않습니다. 이를 원한다면 구조적(단일 매니저 중개) 혹은 CDP로의 전환을 검토해야 합니다.