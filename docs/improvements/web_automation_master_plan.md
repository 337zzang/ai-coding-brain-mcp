
# 웹 자동화 시스템 종합 개선 계획

## 🎯 목표
1. **고유 ID 기반 브라우저 관리** - 세션별 독립적 브라우저 인스턴스
2. **ID 기반 활동 추적** - 모든 액션을 세션 ID로 로깅
3. **크로스 세션 재연결** - 다른 REPL/프로세스에서 기존 브라우저 재사용

## 📅 개선 로드맵

### Phase 1: 긴급 안정화 (1-2일)
- ✅ 치명적 버그 수정 (.h.append, true/false)
- ✅ 중복 함수 정의 제거
- ✅ 안전한 JS 코드 생성

### Phase 2: 아키텍처 전환 (3-5일)
- ✅ Thread 기반 → Client-Server 모델
- ✅ ImprovedBrowserManager 구현
- ✅ WebSocket(CDP) 연결 구조
- ✅ 세션 정보 영속화 (JSON 파일)

### Phase 3: 추적 시스템 (2-3일)
- ✅ ActivityRecorder 구현
- ✅ SessionMonitor 대시보드
- ✅ 세션별 로그 파일 분리
- ✅ 실시간 통계 및 분석

## 🚀 핵심 구현 사항

### 1. BrowserManager (Client-Server)
```python
# 서버 시작 (독립 프로세스)
manager.start_browser_server(session_id="user123")

# 클라이언트 연결 (다른 세션에서)
browser = manager.connect_to_browser(session_id="user123")
```

### 2. 세션 ID 기반 헬퍼
```python
web_goto("user123", "https://example.com")
web_click("user123", "button#submit")
web_extract("user123", "div.content")
```

### 3. 활동 추적
```python
# 자동 로깅
[2025-08-09 10:00:00] [INFO] [Session: user123] Navigated to https://example.com
[2025-08-09 10:00:05] [INFO] [Session: user123] Clicked on button#submit

# 활동 분석
stats = monitor.get_session_stats("user123")
```

## 📁 디렉토리 구조
```
browser_sessions/
├── sessions.json          # 세션 메타데이터
├── profiles/              # 브라우저 프로필
│   └── user123/
├── logs/                  # 세션별 로그
│   └── user123.log
└── activities/            # 활동 기록
    └── user123_activities.jsonl
```

## ✅ 테스트 시나리오

### 시나리오 1: 세션 생성 및 재연결
```python
# REPL 1: 브라우저 시작
browser1 = web_connect("test_session", create_new=True)
web_goto("test_session", "https://google.com")

# REPL 2: 동일 브라우저 재사용
browser2 = web_connect("test_session", create_new=False)
web_click("test_session", "input[name='q']")
```

### 시나리오 2: 활동 추적
```python
# 여러 액션 수행
web_goto_tracked("user123", "https://example.com")
web_click_tracked("user123", "button.login")
web_extract_tracked("user123", "div.user-info")

# 활동 분석
analyze_session_logs("user123")
```

## 🔍 모니터링 및 디버깅

### 실시간 모니터링
```python
monitor = SessionMonitor()
active = monitor.get_active_sessions()
for session in active:
    print(f"Session: {session['session_id']}, PID: {session['pid']}")
```

### 로그 분석
```python
# 세션별 로그 파일
tail -f browser_sessions/logs/user123.log

# 활동 기록 조회
cat browser_sessions/activities/user123_activities.jsonl | jq '.'
```

## 🎉 기대 효과

1. **안정성 향상**
   - Thread 대신 독립 프로세스로 안정성 확보
   - 에러 격리 및 복구 용이

2. **추적성 강화**
   - 모든 액션이 세션 ID로 기록
   - 문제 발생 시 빠른 디버깅

3. **확장성 개선**
   - 여러 REPL/프로세스에서 동시 작업
   - 세션 공유로 협업 가능

4. **유지보수성**
   - 구조화된 코드로 관리 용이
   - 명확한 책임 분리

## 📚 참고 자료
- [Playwright Browser Server](https://playwright.dev/docs/api/class-browsertype#browser-type-launch-server)
- [Python Logging](https://docs.python.org/3/library/logging.html)
- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)
