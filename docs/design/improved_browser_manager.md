
## 개선된 BrowserManager 설계안

### 1. 핵심 구조
```python
class ImprovedBrowserManager:
    """독립 프로세스 기반 브라우저 관리자"""

    def __init__(self):
        self.sessions = {}  # {session_id: session_info}
        self.logs_dir = "logs/web_automation"

    def start_browser_server(self, session_id: str) -> dict:
        """독립 브라우저 서버 시작"""
        # playwright launch_server 사용
        # WebSocket endpoint 반환

    def connect_to_browser(self, session_id: str) -> Browser:
        """기존 브라우저에 연결"""
        # playwright.connect() 사용

    def get_session_logger(self, session_id: str):
        """세션별 로거 반환"""
        # LoggerAdapter 사용하여 session_id 자동 주입
```

### 2. 세션 정보 저장 구조
```python
session_info = {
    "session_id": "user123",
    "pid": 12345,
    "ws_endpoint": "ws://localhost:9222/...",
    "created_at": "2025-08-09T10:00:00",
    "last_activity": "2025-08-09T10:15:00",
    "status": "active",
    "log_file": "logs/web_automation/user123.log"
}
```

### 3. 로깅 시스템
```python
class SessionLogger:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.logger = logging.LoggerAdapter(
            logging.getLogger("web_automation"),
            {"session_id": session_id}
        )
```
