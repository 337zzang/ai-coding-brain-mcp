# REPL에서 Playwright 사용하기

## 🚀 빠른 시작 (Async API)

```python
# 1. Playwright async API 직접 사용
from playwright.async_api import async_playwright

# 브라우저 시작 (REPL에서 await 사용)
p = await async_playwright().start()
browser = await p.chromium.launch(headless=False)
page = await browser.new_page()

# 페이지 이동
await page.goto("https://example.com")

# 요소 클릭
await page.click("button")

# 텍스트 입력
await page.type("input[name='search']", "검색어")

# 스크린샷
await page.screenshot(path="example.png")

# 브라우저는 계속 열려있음 - 추가 명령 가능!
await page.goto("https://google.com")
```

## 🎯 AsyncWebAutomation 클래스 사용

```python
# 모듈 import
from python.api.web_automation_async import AsyncWebAutomation

# 인스턴스 생성
web = AsyncWebAutomation()

# 브라우저 시작
await web.start(headless=False)

# 페이지 이동
await web.goto("https://naver.com")

# 검색
await web.type("input[name='query']", "파이썬")
await web.click("button[type='submit']")

# 스크린샷
await web.screenshot("naver_search.png")

# 브라우저는 계속 열려있음!
```

## 💡 Sync처럼 사용하기 (선택사항)

만약 await를 매번 쓰기 귀찮다면:

```python
import asyncio
from functools import wraps

class SyncWrapper:
    """Async 함수를 Sync처럼 사용하는 래퍼"""

    def __init__(self, async_obj):
        self._async_obj = async_obj
        self._loop = asyncio.get_event_loop()

    def __getattr__(self, name):
        attr = getattr(self._async_obj, name)
        if asyncio.iscoroutinefunction(attr):
            @wraps(attr)
            def wrapper(*args, **kwargs):
                return self._loop.run_until_complete(attr(*args, **kwargs))
            return wrapper
        return attr

# 사용 예
from python.api.web_automation_async import AsyncWebAutomation
async_web = AsyncWebAutomation()
web = SyncWrapper(async_web)

# 이제 await 없이 사용 가능
web.start(headless=False)
web.goto("https://example.com")
web.click("button")
```

## ⚠️ 주의사항

1. **Sync API는 REPL에서 사용 불가**
   - `playwright.sync_api` 사용 시 에러 발생
   - 반드시 `playwright.async_api` 사용

2. **브라우저 종료**
   - 작업 완료 후 `await web.close()` 호출
   - 또는 REPL 종료 시 자동으로 정리됨

3. **에러 처리**
   - 모든 메서드는 `{"success": bool, "message": str}` 형식 반환
   - 에러 발생 시 `success: False`와 에러 메시지 포함
