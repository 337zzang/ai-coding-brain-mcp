# REPL에서 Playwright 사용하기 - 완전 가이드

## 🚀 빠른 시작

```python
from python.api.web_automation_repl import REPLBrowser

# 브라우저 시작
browser = REPLBrowser()
browser.start()

# 웹페이지 제어
browser.goto("https://naver.com")
browser.type("input[name='query']", "파이썬")
browser.click("button[type='submit']")
browser.screenshot("result.png")

# 브라우저는 계속 열려있음!
# 원하는 만큼 명령을 계속 실행 가능

# 종료
browser.stop()
```

## 📋 주요 기능

### 1. 페이지 탐색
```python
browser.goto("https://example.com")
browser.goto("https://google.com", wait_until="domcontentloaded")
```

### 2. 요소 상호작용
```python
browser.click("button#submit")
browser.type("input[name='search']", "검색어")
```

### 3. 스크린샷
```python
browser.screenshot()  # 자동 파일명
browser.screenshot("my_capture.png")  # 지정 파일명
```

### 4. JavaScript 실행
```python
result = browser.eval("document.title")
print(result["result"])
```

### 5. 페이지 내용 가져오기
```python
content = browser.get_content()
print(content["content"][:100])  # 처음 100자
```

### 6. 대기
```python
browser.wait(2)  # 2초 대기
```

## 🎯 실제 사용 예제

### 네이버 검색
```python
browser = REPLBrowser()
browser.start()

# 네이버 이동
browser.goto("https://naver.com")

# 검색
browser.type("input[name='query']", "AI 코딩")
browser.click("button[type='submit']")

# 결과 캡처
browser.wait(2)
browser.screenshot("naver_search_result.png")
```

### 구글 검색
```python
# 구글 이동
browser.goto("https://google.com")

# 검색
browser.type("input[name='q']", "Playwright Python")
browser.type("input[name='q']", "\n")  # 엔터키

# 결과 대기 및 캡처
browser.wait(2)
browser.screenshot("google_result.png")
```

## ⚠️ 주의사항

1. **브라우저 종료**: 작업 완료 후 반드시 `browser.stop()` 호출
2. **선택자**: CSS 선택자를 정확히 사용
3. **대기**: 페이지 로딩 후 충분한 대기 시간 확보

## 🔧 문제 해결

### "브라우저가 실행 중이 아닙니다" 오류
```python
# 브라우저 재시작
browser = REPLBrowser()
browser.start()
```

### 선택자를 찾을 수 없음
```python
# 페이지 내용 확인
content = browser.get_content()
# HTML에서 올바른 선택자 찾기
```

## 💡 고급 팁

### 여러 브라우저 동시 사용
```python
browser1 = REPLBrowser()
browser2 = REPLBrowser()

browser1.start()
browser2.start()

browser1.goto("https://naver.com")
browser2.goto("https://google.com")
```

### 자동화 스크립트
```python
def auto_search(browser, site, query):
    if site == "naver":
        browser.goto("https://naver.com")
        browser.type("input[name='query']", query)
        browser.click("button[type='submit']")
    elif site == "google":
        browser.goto("https://google.com")
        browser.type("input[name='q']", query)
        browser.type("input[name='q']", "\n")

    browser.wait(2)
    browser.screenshot(f"{site}_{query}.png")

# 사용
auto_search(browser, "naver", "Python")
auto_search(browser, "google", "JavaScript")
```
