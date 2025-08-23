# Web 모듈 사용 가이드

## 🚀 빠른 시작

### 설치
```bash
# 필요한 패키지 설치
pip install playwright
python -m playwright install chromium
```

### 기본 사용법
```python
import ai_helpers_new as h

# 웹 자동화 시작
result = h.execute_code('''
from ai_helpers_new.web import WebAutomation
import asyncio

async def main():
    web = WebAutomation()
    await web.start()
    await web.goto("https://example.com")
    title = await web.page.title()
    print(f"Page title: {title}")
    await web.close()

asyncio.run(main())
''')
```

## 📚 주요 기능

### 1. 브라우저 관리
```python
# 헤드리스 모드
web = WebAutomation(headless=True)

# 커스텀 설정
web = WebAutomation(
    headless=False,
    viewport={"width": 1920, "height": 1080},
    user_agent="Custom User Agent"
)
```

### 2. 페이지 상호작용
```python
# 클릭
await web.click("button.submit")

# 텍스트 입력
await web.type("input#email", "user@example.com")

# 선택
await web.select("select#country", "USA")

# 스크롤
await web.scroll_to("div#footer")
```

### 3. 데이터 추출
```python
# 텍스트 추출
text = await web.get_text("h1.title")

# 속성 추출
href = await web.get_attribute("a.link", "href")

# 다중 요소
items = await web.get_all("li.item")
```

### 4. 오버레이 기능
```python
# 오버레이 활성화
web.enable_overlay()

# 미니 모드
web.set_mini_mode(True)

# 투명도 조절
web.set_transparency(0.8)
```

### 5. 세션 관리
```python
# 세션 저장
web.save_session("shopping_cart")

# 세션 복구
web.load_session("shopping_cart")

# 세션 목록
sessions = web.list_sessions()
```

## 🧪 테스트 예제

### 로그인 자동화
```python
async def test_login():
    web = WebAutomation()
    await web.start()

    # 로그인 페이지로 이동
    await web.goto("https://example.com/login")

    # 자격 증명 입력
    await web.type("#username", "myuser")
    await web.type("#password", "mypass")

    # 로그인 버튼 클릭
    await web.click("button[type='submit']")

    # 로그인 성공 확인
    await web.wait_for("div.dashboard")

    await web.close()
```

### 데이터 스크래핑
```python
async def scrape_products():
    web = WebAutomation()
    await web.start()

    await web.goto("https://shop.example.com")

    # 모든 상품 가져오기
    products = await web.evaluate('''
        Array.from(document.querySelectorAll('.product')).map(p => ({
            name: p.querySelector('.name').textContent,
            price: p.querySelector('.price').textContent,
            image: p.querySelector('img').src
        }))
    ''')

    print(f"Found {len(products)} products")
    return products
```

## 🛠️ 고급 설정

### 프록시 설정
```python
web = WebAutomation(proxy={
    "server": "http://proxy.example.com:8080",
    "username": "user",
    "password": "pass"
})
```

### 쿠키 관리
```python
# 쿠키 설정
await web.set_cookie({
    "name": "session",
    "value": "abc123",
    "domain": ".example.com"
})

# 쿠키 가져오기
cookies = await web.get_cookies()
```

### 스크린샷
```python
# 전체 페이지
await web.screenshot("full_page.png", full_page=True)

# 특정 요소
await web.screenshot_element("div.content", "content.png")
```

## 📝 베스트 프랙티스

1. **에러 처리**: 항상 try-except 블록 사용
2. **리소스 정리**: 작업 완료 후 반드시 close() 호출
3. **대기 전략**: 명시적 대기 > 암묵적 대기
4. **세션 재사용**: 가능한 경우 세션 저장/복구 활용
5. **병렬 처리**: 독립적인 작업은 병렬로 실행

## 🆘 문제 해결

### 타임아웃 에러
```python
# 타임아웃 증가
web = WebAutomation(timeout=60000)  # 60초
```

### 요소를 찾을 수 없음
```python
# 대기 추가
await web.wait_for_selector("div.content", timeout=10000)
```

### 메모리 누수
```python
# 주기적으로 브라우저 재시작
if web.memory_usage > 500_000_000:  # 500MB
    await web.restart()
```
