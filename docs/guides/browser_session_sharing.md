# 브라우저 세션 공유 가이드

## 📋 개요
다른 대화 세션이나 터미널에서 기존에 실행 중인 브라우저에 연결하는 방법을 제공합니다.

## 🔗 방법 1: Chrome 디버깅 모드 사용

### 1단계: Chrome을 디버깅 모드로 실행
```bash
# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222

# Mac
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222

# Linux
google-chrome --remote-debugging-port=9222
```

### 2단계: 다른 세션에서 연결
```python
import ai_helpers_new as h

# CDP URL로 연결
result = h.connect_to_existing_browser(cdp_url="http://127.0.0.1:9222")
if result['ok']:
    print(f"✅ 연결 성공: {result['data']}")

    # 이제 일반적인 웹 자동화 함수 사용 가능
    h.web_goto("https://example.com")
    h.handle_popup("확인")
```

## 🔗 방법 2: 세션 파일 공유

### 세션 1에서 저장
```python
import ai_helpers_new as h

# 브라우저 시작 및 작업
h.web_start()
h.web_goto("https://example.com")

# 세션 정보 저장
h.save_browser_session("my_work_session")
# 파일이 .ai-brain/browser_sessions/my_work_session.json에 저장됨
```

### 세션 2에서 로드
```python
import ai_helpers_new as h

# 저장된 세션 목록 확인
result = h.list_browser_sessions()
if result['ok']:
    for session in result['data']['sessions']:
        print(f"- {session['name']}: {session['url']}")

# 세션 정보 로드
h.load_browser_session("my_work_session")
# 세션 정보를 확인하고 가능한 경우 연결 시도
```

## 🔗 방법 3: Playwright 디버깅 브라우저

### 세션 1에서 디버깅 브라우저 실행
```python
import ai_helpers_new as h

# 디버깅 포트를 열고 브라우저 실행
h.launch_browser_with_debugging(port=9222)
# 브라우저가 실행되고 다른 세션에서 연결 가능
```

### 세션 2에서 연결
```python
import ai_helpers_new as h

# CDP URL로 연결
h.connect_to_existing_browser(cdp_url="http://127.0.0.1:9222")
```

## 📊 세션 정보 확인

### 현재 세션의 WebSocket Endpoint 가져오기
```python
result = h.get_browser_ws_endpoint()
if result['ok']:
    print(f"WebSocket: {result['data']['ws_endpoint']}")
```

### 활성 세션 목록 확인
```python
# BrowserManager를 통한 세션 확인
result = h.web_list_sessions()
if result['ok']:
    print(f"활성 세션: {result['data']}")
```

## ⚠️ 주의사항

1. **포트 충돌**: 9222 포트가 이미 사용 중이면 다른 포트 사용
2. **보안**: 디버깅 포트는 보안상 위험할 수 있으므로 신뢰할 수 있는 환경에서만 사용
3. **브라우저 종료**: 디버깅 모드로 실행한 브라우저는 수동으로 종료 필요
4. **세션 파일**: `.ai-brain/browser_sessions/` 폴더의 세션 파일은 민감한 정보를 포함할 수 있음

## 🎯 사용 시나리오

### 시나리오 1: 장시간 작업 세션 유지
1. 브라우저를 디버깅 모드로 실행
2. 작업 진행
3. 필요시 다른 터미널에서 연결하여 추가 작업

### 시나리오 2: 팀 협업
1. 한 명이 브라우저 세션 시작 및 설정
2. 세션 정보 저장 및 공유
3. 다른 팀원이 세션에 연결하여 작업 계속

### 시나리오 3: 디버깅 및 테스트
1. 수동으로 브라우저 조작
2. 특정 상태에서 자동화 스크립트 연결
3. 문제 상황 재현 및 테스트

## 🔧 문제 해결

### "연결 실패" 오류
- Chrome이 디버깅 모드로 실행되었는지 확인
- 포트가 올바른지 확인 (기본값: 9222)
- 방화벽이 포트를 차단하지 않는지 확인

### "asyncio loop" 오류
- 동기 API 사용 확인
- 필요시 별도 스레드에서 실행

### 세션 파일을 찾을 수 없음
- `.ai-brain/browser_sessions/` 폴더 확인
- 세션 이름이 정확한지 확인
