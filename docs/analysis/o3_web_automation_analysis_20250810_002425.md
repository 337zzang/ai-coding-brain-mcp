아래 계획은 현재 Thread 기반 REPL 브라우저 구조를 Playwright의 browser_type.launch_server()와 connect()를 중심으로 한 Client-Server(프로세스 분리) 아키텍처로 전환하고, 세션 ID 기반 재연결/로깅/운영 안정성을 확보하는 것입니다. Windows 호환성과 운용성을 최우선으로 고려했습니다.

1) 단계별 개선 로드맵

- 긴급(오늘~1주)
  - 치명적 버그 핫픽스
    - .h.append, .h.replace 오타 정정
    - true/false → True/False
    - 함수 중복 정의 제거
    - JS 코드 생성 안전화(템플릿 보간 금지, evaluate(fn, args) 방식 통일)
  - 세션 ID 포함 Structured Logging 도입
    - logger = LoggerAdapter 또는 structlog로 session_id 자동 포함
    - 최소 콘솔+파일 이중 로깅, JSON 로그 포맷
  - helpers.py 방어적 패치
    - 공용 util과 위험한 API 분리(Deprecated 경고 추가)
    - 예외 클래스 통일 및 상세 메시지

- 단기(1~3주)
  - Client-Server 전환의 1차 구현
    - 브라우저 서버 프로세스(browser_host) 분리: Playwright browser_type.launch_server() 사용
    - BrowserManager(서버/관리자) 도입: 세션 생성/조회/종료/재연결 관리
    - REPL/클라이언트에서는 p.connect(ws_endpoint=...)로 접속
    - 세션별 단일 Browser(프로세스) 전략으로 단순화(세션=브라우저 1:1)
  - ID 기반 활동 로깅
    - 클라이언트 측 action wrapper로 goto/click/type 등 로깅
    - page/console/network 이벤트 리스너 부착
    - tracing/har 옵션 지원
  - Windows 운영 고려
    - subprocess.Popen + CREATE_NEW_PROCESS_GROUP
    - 종료 시 taskkill 대체 로직
    - 로컬 루프백 바인딩, 방화벽 예외 문서화

- 중기(3~8주)
  - 리팩토링/안정화
    - helpers.py → 모듈화: manager, host, client, logging, js_safe, models, errors 등
    - 세션 레지스트리 영속화(파일/SQLite). 매니저 재시작 시 고아 브라우저 인수/정리
    - 관측성 확장: 메트릭, 헬스체크, 힙덤프/크래시 덤프, 트레이싱 보관 자동화
    - 대량 동시 세션 관리 성능 튜닝(워커 풀, 리소스 제한, LRU 정리)
    - 선택: auth 토큰 기반 ws_endpoint 보호(내부 네트워크/IPC로 제한)

2) Client-Server 아키텍처 구현 방법

- 핵심 아이디어
  - 세션=브라우저 1:1. 각 세션은 독립 브라우저 서버 프로세스에서 launch_server()로 띄움.
  - 클라이언트(REPL, 작업자)는 playwright.connect(ws_endpoint=...)로 어디서든 재접속.
  - BrowserManager는 세션 수명주기와 메타데이터(ws_endpoint, pid, 로그 경로, 생성시간, 상태)를 관리.
  - 로깅은 서버와 클라이언트 모두에서 session_id를 공통 태그로 사용해 상관관계 확보.

- 데이터 흐름
  - 클라이언트 → BrowserManager.create_session(session_id) 호출
  - BrowserManager가 browser_host 프로세스 생성 → ws_endpoint 획득/저장
  - 클라이언트는 p.connect(ws_endpoint)로 접속해 작업 수행
  - 다른 REPL/세션에서도 동일 session_id로 ws_endpoint 조회 후 재접속

- 보안/접근 제어
  - ws_endpoint는 로컬 루프백만 허용, 외부 노출 금지
  - 매니저 API(예: FastAPI) 앞단 인증 토큰 적용(내부라면 단순화 가능)
  - Windows 방화벽 예외 애드혹 문서화

3) BrowserManager 클래스 재설계

- 책임
  - 세션 생성/조회/재연결/종료
  - 브라우저 서버 프로세스의 생명주기 관리 및 헬스 모니터링
  - 레지스트리(디스크) 영속화: 재시작 시 기존 세션 복구 또는 정리
  - 로깅 표준화(session_id, action, meta)

- 설계 원칙
  - 세션=브라우저 서버 프로세스 1:1
  - 매니저 다운타임 동안도 브라우저는 지속
  - 매니저 재시작 시 레지스트리를 읽어 자동 재인수(adopt) 또는 정리

- 주요 메서드
  - create_session(session_id, browser="chromium", headless=False, channel=None, env=None) -> SessionInfo
  - get_session(session_id) -> SessionInfo | None
  - list_sessions() -> list[SessionInfo]
  - is_alive(session_id) -> bool
  - ensure_session(session_id, ...) -> SessionInfo
  - terminate_session(session_id, force=False)
  - cleanup_orphans()
  - adopt_existing()

4) ID 기반 로깅 시스템

- 공통 로거 팩토리
  - logger = get_logger(session_id) → JSON 포맷, console/file 핸들러
- 서버 측(browser_host)
  - 프로세스 시작/종료/예외/endpoint 출력
  - 브라우저 이벤트(옵션) 최소 로깅
- 클라이언트 측
  - 고수준 액션 Wrapper: goto/click/type/fill/check/query 등
  - page.on("console"/"pageerror"), context.on("request"/"response") 핸들러
  - 필요 시 tracing.start/stop 저장
- 로그 필드 예시
  - ts, level, session_id, action, url, selector, args, result_summary, duration_ms, error, stack

5) 버그 수정 체크리스트

- 언어/오타
  - .h.append → .append 또는 의도한 API로 교정
  - .h.replace → .replace 또는 올바른 호출부로 교정
  - true/false → True/False
  - 중복 함수 제거 및 단일 소스 유지
- JS 안전성
  - 문자열 템플릿 기반 evaluate 금지
  - page.evaluate(lambda el, v: ..., arg) 패턴으로 통일
  - add_init_script 시 사용자 입력 이스케이프 또는 함수/args만 허용
- 예외 처리
  - 명시적 타임아웃과 재시도 정책
  - PlaywrightError 별도 처리, 스크린샷/트레이스 수집 후 재던지기
- 리소스/종료
  - 컨텍스트/페이지/브라우저 종료 보장 finally 블록
  - 프로세스 종료 시 자식 프로세스 정리(taskkill /T /F)
- 테스트
  - 단위: JS wrapper, logger adapter, manager process spawn
  - 통합: create→connect→action→reconnect→terminate 시나리오

6) 리팩토링 전략

- 모듈 분해
  - helpers/
    - manager.py (BrowserManager)
    - host.py (브라우저 서버 프로세스 엔트리)
    - client.py (connect/telemetry wrapper)
    - logging.py (공통 로깅 팩토리)
    - js_safe.py (evaluate 헬퍼)
    - models.py (SessionInfo, States)
    - errors.py
    - util.py
  - 기존 helpers.py는 위 모듈로 기능 이관 후 Deprecated Facade 제공
- 점진적 마이그레이션
  - REPL에서 먼저 Manager+connect 사용하는 경로 추가
  - 구 API는 내부적으로 새 경로 위임, 경고 로그
  - 사용 통계 수집 후 완전 전환
- 품질/도구
  - ruff/black/mypy 적용
  - pytest + playwright testcontainers(옵션)

7) 구체적 코드 예시

A. 브라우저 서버 프로세스(host) 예시

```python
# host.py
import asyncio, json, logging, os, signal, sys, time
from dataclasses import dataclass
from playwright.async_api import async_playwright

def setup_logger(session_id: str, log_path: str):
    logger = logging.getLogger(f"host.{session_id}")
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter('%(asctime)s %(levelname)s session=%(session_id)s %(message)s')
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    ch = logging.StreamHandler(sys.stderr)
    ch.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(ch)
    # LoggerAdapter to inject session_id
    return logging.LoggerAdapter(logger, {"session_id": session_id})

async def run_host(session_id: str, browser: str = "chromium", headless: bool = False, channel: str | None = None):
    runtime_dir = os.path.abspath(os.environ.get("BROWSER_RUNTIME_DIR", "./runtime"))
    os.makedirs(runtime_dir, exist_ok=True)
    log_path = os.path.join(runtime_dir, f"{session_id}.log")
    logger = setup_logger(session_id, log_path)
    logger.info("host starting")

    async with async_playwright() as p:
        bt = getattr(p, browser)
        launch_kwargs = {"headless": headless}
        if channel:
            launch_kwargs["channel"] = channel
        server = await bt.launch_server(**launch_kwargs)
        ws = server.ws_endpoint
        info = {"session_id": session_id, "ws_endpoint": ws, "pid": os.getpid(), "browser": browser, "headless": headless, "ts": time.time()}
        # Print JSON to stdout so manager can capture
        print(json.dumps(info), flush=True)
        logger.info(f"host launched ws={ws}")

        # Optional: keep minimal observers; main actions are from clients
        try:
            await server.wait_for_close()
            logger.info("browser server closed")
        except Exception as e:
            logger.exception(f"server exception: {e}")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--browser", default="chromium", choices=["chromium", "firefox", "webkit"])
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--channel", default=None)
    args = parser.parse_args()

    # Windows-friendly
    try:
        asyncio.run(run_host(args.session_id, args.browser, args.headless, args.channel))
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
```

B. BrowserManager 예시(서버/라이브러리)

```python
# manager.py
import json, os, subprocess, sys, time, typing as t, platform, shutil
from dataclasses import dataclass, asdict

RUNTIME_DIR = os.path.abspath(os.environ.get("BROWSER_RUNTIME_DIR", "./runtime"))
os.makedirs(RUNTIME_DIR, exist_ok=True)
REGISTRY_PATH = os.path.join(RUNTIME_DIR, "registry.json")

@dataclass
class SessionInfo:
    session_id: str
    ws_endpoint: str
    pid: int
    browser: str
    headless: bool
    created_at: float
    status: str = "running"

class BrowserManager:
    def __init__(self):
        self.registry: dict[str, SessionInfo] = {}
        self._load_registry()

    def _load_registry(self):
        if os.path.exists(REGISTRY_PATH):
            try:
                data = json.load(open(REGISTRY_PATH, "r", encoding="utf-8"))
                for k, v in data.items():
                    self.registry[k] = SessionInfo(**v)
            except Exception:
                self.registry = {}

    def _save_registry(self):
        tmp = {k: asdict(v) for k, v in self.registry.items()}
        json.dump(tmp, open(REGISTRY_PATH, "w", encoding="utf-8"))

    def _is_pid_alive(self, pid: int) -> bool:
        if platform.system() == "Windows":
            # Use tasklist
            try:
                out = subprocess.check_output(["tasklist", "/FI", f"PID eq {pid}"]).decode("cp949", errors="ignore")
                return str(pid) in out
            except Exception:
                return False
        else:
            try:
                os.kill(pid, 0)
                return True
            except Exception:
                return False

    def create_session(self, session_id: str, browser: str = "chromium", headless: bool = False, channel: str | None = None) -> SessionInfo:
        if session_id in self.registry and self._is_pid_alive(self.registry[session_id].pid):
            return self.registry[session_id]

        python_exec = sys.executable
        host_script = os.path.join(os.path.dirname(__file__), "host.py")
        args = [python_exec, host_script, "--session-id", session_id, "--browser", browser]
        if headless:
            args.append("--headless")
        if channel:
            args += ["--channel", channel]

        creationflags = 0
        if platform.system() == "Windows":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore

        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=creationflags)
        assert proc.stdout is not None
        # Read first line JSON with endpoint
        line = proc.stdout.readline().strip()
        if not line:
            # if host wrote errors to stderr
            err = proc.stderr.read() if proc.stderr else ""
            raise RuntimeError(f"Failed to start browser_host: {err}")

        info = json.loads(line)
        si = SessionInfo(
            session_id=session_id,
            ws_endpoint=info["ws_endpoint"],
            pid=info["pid"],
            browser=info.get("browser", browser),
            headless=bool(info.get("headless", headless)),
            created_at=info.get("ts", time.time()),
            status="running",
        )
        self.registry[session_id] = si
        self._save_registry()
        return si

    def get_session(self, session_id: str) -> SessionInfo | None:
        si = self.registry.get(session_id)
        if not si:
            return None
        if not self._is_pid_alive(si.pid):
            si.status = "dead"
        return si

    def list_sessions(self) -> list[SessionInfo]:
        return [self.get_session(sid) for sid in list(self.registry.keys()) if self.get_session(sid)]

    def terminate_session(self, session_id: str, force: bool = False) -> bool:
        si = self.registry.get(session_id)
        if not si:
            return False
        if platform.system() == "Windows":
            try:
                subprocess.run(["taskkill", "/PID", str(si.pid), "/T", "/F" if force else ""], check=False)
            except Exception:
                pass
        else:
            try:
                os.kill(si.pid, 15)
            except Exception:
                pass
        si.status = "terminated"
        self._save_registry()
        return True

    def cleanup_orphans(self):
        for sid, si in list(self.registry.items()):
            if not self._is_pid_alive(si.pid):
                si.status = "dead"
        self._save_registry()
```

C. 클라이언트에서 재연결(connect) 예시

```python
# client.py
import asyncio, time
from typing import Callable, Awaitable
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from .manager import BrowserManager

async def attach(session_id: str) -> tuple[Browser, BrowserContext, Page]:
    bm = BrowserManager()
    si = bm.get_session(session_id) or bm.create_session(session_id)
    async with async_playwright() as p:
        # 핵심: launch_server()로 생성된 ws_endpoint에 접속
        browser = await p.connect(ws_endpoint=si.ws_endpoint)
        # 세션=브라우저 1:1이므로 컨텍스트를 명시적으로 1개 운용
        contexts = browser.contexts
        if contexts:
            context = contexts[0]
        else:
            context = await browser.new_context()
        pages = context.pages
        page = pages[0] if pages else await context.new_page()
        return browser, context, page
```

D. 활동 로깅과 안전한 JS evaluate

```python
# logging.py
import json, logging, sys
def get_logger(session_id: str):
    logger = logging.getLogger(f"client.{session_id}")
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter('%(asctime)s %(levelname)s session=%(session_id)s action=%(action)s %(message)s')
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    if not logger.handlers:
        logger.addHandler(ch)
    return logging.LoggerAdapter(logger, {"session_id": session_id, "action": "-"})

# js_safe.py
from typing import Any, Callable
async def eval_fn(page, fn: Callable, *args: Any):
    # fn은 직렬화 가능한 함수여야 하며 문자열 템플릿 금지
    return await page.evaluate(fn, *args)

# telemetry wrapper
async def attach_telemetry(context, page, logger):
    page.on("console", lambda msg: logger.info(f"console {msg.type}: {msg.text}", extra={"action": "console"}))
    page.on("pageerror", lambda err: logger.error(f"pageerror {err}", extra={"action": "pageerror"}))
    context.on("request", lambda req: logger.info(f"request {req.method} {req.url}", extra={"action": "request"}))
    context.on("response", lambda res: logger.info(f"response {res.status} {res.url}", extra={"action": "response"}))

async def goto(page, url: str, logger):
    t0 = time.perf_counter()
    logger.info(f"goto {url}", extra={"action": "goto"})
    resp = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    logger.info(f"goto_done status={resp.status if resp else 'n/a'} dur_ms={(time.perf_counter()-t0)*1000:.1f}", extra={"action": "goto"})

async def click(page, selector: str, logger):
    logger.info(f"click {selector}", extra={"action": "click"})
    await page.click(selector, timeout=20000)

async def type_text(page, selector: str, text: str, logger):
    logger.info(f"type {selector} len={len(text)}", extra={"action": "type"})
    await page.fill(selector, text, timeout=20000)
```

E. FastAPI(옵션)로 Manager API 노출

```python
# api.py
from fastapi import FastAPI, HTTPException
from .manager import BrowserManager

app = FastAPI()
bm = BrowserManager()

@app.post("/sessions/{session_id}")
def create(session_id: str):
    si = bm.create_session(session_id)
    return si.__dict__

@app.get("/sessions/{session_id}")
def get(session_id: str):
    si = bm.get_session(session_id)
    if not si:
        raise HTTPException(404)
    return si.__dict__

@app.delete("/sessions/{session_id}")
def delete(session_id: str):
    ok = bm.terminate_session(session_id)
    if not ok:
        raise HTTPException(404)
    return {"ok": True}
```

F. Playwright의 launch_server()와 connect() 포인트

- 서버(호스트)
  - server = await p.chromium.launch_server(headless=False)
  - ws = server.ws_endpoint
  - await server.wait_for_close()
- 클라이언트
  - browser = await p.connect(ws_endpoint=ws)
  - context = await browser.new_context()
  - page = await context.new_page()

주의:
- launch_persistent_context는 BrowserType 레벨에서만 가능하므로, launch_server와 병행해 세션별 영속 프로필이 꼭 필요하면 대안으로 storage_state 저장/복구를 사용하세요.
- 영속 상태가 꼭 필요할 때
  - 최초 컨텍스트에서 await context.storage_state(path="...") 저장
  - 재연결 또는 재생성 시 await browser.new_context(storage_state="...")로 복구
- 여러 클라이언트 동시 연결이 가능하나 충돌 방지를 위해 “세션=브라우저 1:1” + 컨텍스트 1개 정책을 권장합니다.

G. Windows 고려 사항

- 프로세스 생성
  - subprocess.CREATE_NEW_PROCESS_GROUP 사용
  - 종료는 taskkill /PID <pid> /T /F
- 포트/네트워크
  - ws_endpoint는 기본적으로 로컬 바인딩. 원격 필요 시 TLS/터널 고려
- 이벤트 루프
  - asyncio.run 사용, Python 3.8+ 기본 Proactor 정책이면 OK
- 경로/인코딩
  - cp949 로그 출력 주의, UTF-8 고정 권장

요약 핵심 결정

- Thread 기반 REPL → 프로세스 기반 브라우저 서버로 분리
- 세션=브라우저 1:1. BrowserManager가 수명주기/레지스트리 관리
- 클라이언트는 playwright.connect(ws_endpoint)로 언제든 재접속
- 로깅은 session_id를 공통 상관키로 사용한 Structured Logging
- 안전한 JS 실행, 예외/리소스 처리, Windows 호환성 보강
- helpers.py를 기능 단위 모듈로 분해하고 단계적으로 마이그레이션

이 설계로 세션 ID 기반 관리, 크로스 세션 재연결, 상세 활동 로깅, Windows 지원을 모두 충족하면서 유지보수성과 확장성을 확보할 수 있습니다.