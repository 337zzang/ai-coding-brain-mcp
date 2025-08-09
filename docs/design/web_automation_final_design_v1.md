
# 웹 자동화 시스템 최종 설계 v1.0

## 🎯 목표 및 요구사항
- ✅ 고유 ID 기반 브라우저 관리
- ✅ ID 기반 활동 로그 추적
- ✅ 다른 세션에서 브라우저 재연결
- ✅ Windows 환경 안정성

## 🏗️ 아키텍처 설계

### 1. 전체 구조 (Client-Server Model)

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   REPL Client 1 │     │   REPL Client 2 │     │   REPL Client N │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │ connect()              │ connect()              │
         └────────────┬───────────┴────────────┬───────────┘
                      ▼                        ▼
            ┌──────────────────────────────────────┐
            │         BrowserManager               │
            │  (세션 레지스트리 + 라이프사이클)    │
            └──────────┬───────────────────────────┘
                       │ launch_server()
         ┌─────────────┼─────────────┬─────────────┐
         ▼             ▼             ▼             ▼
   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
   │ Browser  │  │ Browser  │  │ Browser  │  │ Browser  │
   │ Process 1│  │ Process 2│  │ Process 3│  │ Process N│
   │(session1)│  │(session2)│  │(session3)│  │(sessionN)│
   └──────────┘  └──────────┘  └──────────┘  └──────────┘
```

### 2. 핵심 컴포넌트

#### 2.1 BrowserManager (중앙 관리자)
```python
class BrowserManager:
    """세션 생명주기 관리"""

    def __init__(self, base_dir="browser_sessions"):
        self.base_dir = base_dir
        self.registry = SessionRegistry(base_dir)
        self.logger = logging.getLogger("BrowserManager")

    def create_session(self, session_id: str, **options) -> SessionInfo:
        """새 브라우저 서버 시작"""

    def connect(self, session_id: str) -> Browser:
        """기존 브라우저 연결"""

    def terminate_session(self, session_id: str):
        """브라우저 종료"""

    def list_sessions(self) -> List[SessionInfo]:
        """활성 세션 목록"""

    def health_check(self, session_id: str) -> bool:
        """세션 상태 확인"""
```

#### 2.2 SessionRegistry (영속화)
```python
class SessionRegistry:
    """세션 정보 영속화"""

    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.sessions_file = f"{storage_path}/sessions.json"
        self._load_sessions()

    def save_session(self, session_info: SessionInfo):
        """세션 정보 저장"""

    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """세션 정보 조회"""

    def remove_session(self, session_id: str):
        """세션 정보 삭제"""

    def adopt_orphans(self) -> List[SessionInfo]:
        """고아 프로세스 복구"""
```

#### 2.3 SessionInfo (데이터 모델)
```python
@dataclass
class SessionInfo:
    session_id: str
    pid: int
    ws_endpoint: str
    created_at: datetime
    last_activity: datetime
    status: str  # "active", "terminated", "orphan"
    browser_type: str = "chromium"
    headless: bool = False
    profile_dir: Optional[str] = None
    log_file: Optional[str] = None
```

#### 2.4 ActivityLogger (활동 추적)
```python
class ActivityLogger:
    """세션별 활동 로깅"""

    def __init__(self, session_id: str, log_dir: str):
        self.session_id = session_id
        self.logger = self._setup_logger(session_id, log_dir)
        self.activity_file = f"{log_dir}/{session_id}_activities.jsonl"

    def log_action(self, action: str, details: dict):
        """활동 기록"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "action": action,
            "details": details
        }
        # JSONL 형식으로 저장
        with open(self.activity_file, 'a') as f:
            f.write(json.dumps(record) + '\n')
```

### 3. 구현 우선순위

#### Phase 1: MVP (최소 기능 제품)
1. BrowserManager 기본 구현
2. launch_server() + connect() 검증
3. 세션 레지스트리 (JSON)
4. 기본 로깅

#### Phase 2: 안정화
1. Windows 특화 처리
2. 에러 처리 및 복구
3. 헬스 체크
4. 고아 프로세스 처리

#### Phase 3: 고도화
1. 성능 최적화
2. 대량 세션 관리
3. 메트릭 및 모니터링
4. UI 대시보드

## 🔧 구현 세부사항 (대기 중)

O3가 제공할 구체적 코드:
- [ ] launch_server() 정확한 구현
- [ ] WebSocket 엔드포인트 파싱
- [ ] Windows 프로세스 관리
- [ ] 세션 재연결 로직

## 📦 패키지 구조

```
web_automation/
├── __init__.py
├── manager.py          # BrowserManager
├── registry.py         # SessionRegistry
├── models.py           # SessionInfo, 데이터 모델
├── logger.py           # ActivityLogger
├── client.py           # 클라이언트 헬퍼 함수
├── errors.py           # 커스텀 예외
└── utils.py            # 유틸리티 함수
```
