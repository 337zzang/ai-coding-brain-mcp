#!/usr/bin/env python3
"""
네이버 자동화 스크립트
분석된 셀렉터를 활용한 자동화 예제
"""

from playwright.sync_api import sync_playwright
import time
from datetime import datetime

def naver_automation():
    """네이버 자동화 작업"""

    with sync_playwright() as p:
        # 브라우저 시작
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print("🚀 네이버 자동화 시작")

        # 1. 네이버 접속
        page.goto("https://www.naver.com")
        page.wait_for_load_state("networkidle")
        print("✅ 네이버 메인 페이지 접속")

        # 2. 검색 수행
        search_box = page.locator("#query")  # 검색창 셀렉터
        search_box.fill("파이썬 웹 스크래핑")
        search_box.press("Enter")
        page.wait_for_load_state("networkidle")
        print("✅ 검색 완료: 파이썬 웹 스크래핑")

        # 3. 검색 결과 수집
        time.sleep(2)
        results = page.locator(".total_tit").all()
        print(f"\n📊 검색 결과 {len(results)}개 발견:")

        for i, result in enumerate(results[:5]):  # 상위 5개만
            title = result.text_content()
            print(f"  {i+1}. {title}")

        # 4. 스크린샷
        page.screenshot(path=f"naver_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        print("\n📸 스크린샷 저장 완료")

        # 5. 뉴스 탭으로 이동
        page.locator(".shortcut_item").filter(has_text="뉴스").click()
        page.wait_for_load_state("networkidle")
        print("✅ 뉴스 페이지로 이동")

        # 6. 뉴스 헤드라인 수집
        headlines = page.locator(".cjs_t").all()[:5]
        print(f"\n📰 주요 뉴스 헤드라인:")
        for i, headline in enumerate(headlines):
            text = headline.text_content()
            print(f"  {i+1}. {text}")

        # 브라우저 종료
        input("\n⏸️ Enter를 누르면 브라우저를 종료합니다...")
        browser.close()
        print("✅ 자동화 완료")

# 특정 작업용 함수들
def search_and_collect(query, max_results=10):
    """검색 후 결과 수집"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 네이버 접속 및 검색
        page.goto("https://www.naver.com")
        page.locator("#query").fill(query)
        page.locator("#query").press("Enter")
        page.wait_for_load_state("networkidle")

        # 결과 수집
        results = []
        items = page.locator(".total_tit").all()[:max_results]

        for item in items:
            results.append({
                "title": item.text_content(),
                "link": item.locator("a").get_attribute("href")
            })

        browser.close()
        return results

def monitor_news_keywords(keywords):
    """특정 키워드 뉴스 모니터링"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        results = {}

        for keyword in keywords:
            page.goto("https://search.naver.com/search.naver?where=news&query=" + keyword)
            page.wait_for_load_state("networkidle")

            news_items = page.locator(".news_tit").all()[:3]
            results[keyword] = [item.text_content() for item in news_items]

        browser.close()
        return results

if __name__ == "__main__":
    # 메인 자동화 실행
    naver_automation()

    # 또는 특정 함수 실행
    # results = search_and_collect("AI 개발")
    # print(results)
