"""
REPL에서 테스트하기 위한 예제 코드
"""

# REPL에서 실행:
# 1. 이 파일을 복사해서 REPL에 붙여넣기
# 2. 또는 exec(open('test_async_web.py').read())

from playwright.async_api import async_playwright

async def test_browser():
    """브라우저 테스트 함수"""
    print("🚀 브라우저 시작 중...")

    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=False)
    page = await browser.new_page()

    print("📍 Example.com 이동...")
    await page.goto("https://example.com")

    print("📸 스크린샷 캡처...")
    await page.screenshot(path="test_screenshot.png")

    print(f"✅ 현재 URL: {page.url}")
    print(f"✅ 페이지 제목: {await page.title()}")

    input("엔터를 누르면 브라우저가 종료됩니다...")

    await browser.close()
    await p.stop()
    print("👋 브라우저 종료 완료!")

# REPL에서 실행: await test_browser()
