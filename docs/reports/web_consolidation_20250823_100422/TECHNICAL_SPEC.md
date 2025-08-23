# Web 모듈 기술 사양

## 1. 아키텍처 개요

### 현재 구조
```
Web 자동화 시스템
├── Core Web Module (web_new.py)
├── Modular Web (web/)
├── Browser Overlay Automation
└── Session Management
```

### 통합 후 구조
```
통합 Web 시스템
├── Unified API (web/__init__.py)
├── Browser Management
├── Session Persistence
└── Overlay Engine
```

## 2. 핵심 컴포넌트

### WebAutomation 클래스
- Playwright 기반 브라우저 자동화
- 세션 관리 및 복구
- 스마트 대기 및 재시도 로직

### OverlayEngine
- 투명 오버레이 렌더링
- JavaScript 브릿지 통신
- AI 패턴 분석 통합

### SessionManager
- 영속적 세션 관리
- 상태 저장 및 복구
- 멀티 세션 지원

## 3. API 인터페이스

### 기본 사용법
```python
from ai_helpers_new.web import WebAutomation

# 브라우저 시작
web = WebAutomation()
await web.start()

# 페이지 탐색
await web.goto("https://example.com")

# 요소 상호작용
await web.click("button#submit")
await web.type("input#search", "query")

# 데이터 추출
data = await web.extract("div.content")
```

### 고급 기능
```python
# 오버레이 모드
web.enable_overlay(transparency=0.8)

# AI 지원 패턴 매칭
patterns = web.ai.analyze_patterns()

# 세션 저장/복구
web.save_session("my_session")
web.load_session("my_session")
```

## 4. 보안 고려사항

### 입력 검증
- 모든 사용자 입력 sanitize
- XSS 방지 필터링
- SQL 인젝션 방지

### 세션 보안
- 세션 토큰 암호화
- 타임아웃 설정
- IP 검증

## 5. 성능 최적화

### 리소스 관리
- 브라우저 인스턴스 풀링
- 메모리 누수 방지
- 자동 가비지 컬렉션

### 병렬 처리
- 멀티 탭/윈도우 지원
- 비동기 작업 큐
- 워커 스레드 활용
