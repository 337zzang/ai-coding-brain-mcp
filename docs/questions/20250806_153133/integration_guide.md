# 웹 자동화 세션 유지 - O3 솔루션 통합 가이드

## 🎯 O3 AI 솔루션 요약

O3가 제시한 완벽한 해결책: **Playwright의 launch_server()와 connect() 활용**

### 핵심 원리
1. 브라우저를 서버 모드로 실행 (`launch_server()`)
2. WebSocket endpoint를 파일에 저장
3. 다른 프로세스에서 파일을 읽어 `connect()`로 연결

### 파일 구조
```
~/.web_sessions/
 └─ work/              # 세션 ID
     ├─ user_data/     # 크롬 프로필 (쿠키, localStorage)
     └─ meta.json      # {"ws": "ws://...", "pid": 1234}
```

## 🔧 통합 방법

### 1. 기존 헬퍼 함수와 통합

```python
# python/api/web_automation_helpers.py에 추가

from .web_session import open_session, connect_session, close_session

def web_start_shared(session_id: str = "default", headless: bool = False):
    '''공유 가능한 브라우저 세션 시작'''
    browser, context, page = open_session(session_id, headless=headless)

    # BrowserManager에 등록
    from .web_automation_manager import browser_manager
    wrapper = REPLBrowserWithRecording()
    wrapper.browser = browser
    wrapper.context = context
    wrapper.page = page
    wrapper.browser_started = True

    browser_manager.set_instance(wrapper, session_id)
    _set_web_instance(wrapper)

    return {
        'ok': True,
        'data': {
            'session_id': session_id,
            'status': 'started',
            'message': f'세션 {session_id} 시작됨'
        }
    }

def web_connect_shared(session_id: str = "default"):
    '''기존 브라우저 세션에 연결'''
    try:
        page = connect_session(session_id)

        # 간단한 래퍼 생성
        wrapper = type('WebWrapper', (), {
            'page': page,
            'browser_started': True
        })()

        _set_web_instance(wrapper)

        return {
            'ok': True,
            'data': {
                'session_id': session_id,
                'url': page.url,
                'title': page.title()
            }
        }
    except RuntimeError as e:
        return {'ok': False, 'error': str(e)}

def web_close_shared(session_id: str = "default"):
    '''공유 세션 종료'''
    close_session(session_id)

    from .web_automation_manager import browser_manager
    browser_manager.remove_instance(session_id)

    return {
        'ok': True,
        'data': f'세션 {session_id} 종료됨'
    }
```

### 2. 사용자 경험 개선

```python
# ai_helpers_new/__init__.py에 추가
from api.web_automation_helpers import (
    web_start_shared,
    web_connect_shared, 
    web_close_shared
)

# 간편 별칭
web_shared = web_start_shared
web_join = web_connect_shared
web_leave = web_close_shared
```

## 📝 사용 예시

### 시나리오 1: 개발자 협업
```python
# 개발자 A (터미널 1)
import ai_helpers_new as h
h.web_shared("team_work")
h.web_goto("https://complex-app.com")
# 복잡한 로그인과 설정...

# 개발자 B (터미널 2)
import ai_helpers_new as h
h.web_join("team_work")  # 즉시 연결!
h.web_click("button")     # 같은 브라우저 제어
```

### 시나리오 2: 작업 중단 후 재개
```python
# 월요일
h.web_shared("my_project")
h.web_goto("https://dashboard.com")
# 작업...

# 화요일 (브라우저 종료 후)
h.web_shared("my_project")  # 자동으로 같은 프로필로 재시작
# 로그인 상태 유지됨!
```

### 시나리오 3: 자동화 스크립트 분할
```python
# script1.py
h.web_shared("scraper")
h.web_goto("https://data-site.com")

# script2.py  
h.web_join("scraper")
data = h.web_extract("table")

# script3.py
h.web_leave("scraper")  # 정리
```

## ✅ 장점

1. **단순함**: 3개 함수로 모든 기능
2. **안정성**: Playwright 네이티브 기능
3. **영속성**: 쿠키/로그인 자동 유지
4. **투명성**: 복잡한 설정 불필요
5. **확장성**: 여러 클라이언트 동시 접속

## 📊 비교표

| 기능 | 기존 방식 | O3 솔루션 |
|------|----------|-----------|
| 프로세스 간 공유 | ❌ 불가 | ✅ 가능 |
| 세션 ID 관리 | ❌ 없음 | ✅ 자동 |
| 상태 영속화 | ❌ 수동 | ✅ 자동 |
| 사용 복잡도 | 높음 | 낮음 |
| Chrome 재시작 | 필요 | 불필요 |

## 🚀 다음 단계

1. ✅ web_session.py 구현 완료
2. [ ] 헬퍼 함수 통합
3. [ ] 테스트 케이스 작성
4. [ ] 문서화
5. [ ] 배포

## 📌 참고

- O3 분석 전문: `docs/questions/20250806_153133/o3_analysis.md`
- 구현 코드: `python/api/web_session.py`
- 시니어 질문: `docs/questions/20250806_153133/senior_question.md`
