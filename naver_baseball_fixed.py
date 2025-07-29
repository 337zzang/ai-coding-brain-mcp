#!/usr/bin/env python3
"""
자동 생성된 웹 스크래핑 스크립트 (수정됨)
생성일: 2025-07-27
URL: https://www.naver.com
"""

def main():
    try:
        # playwright 사용 (더 범용적)
        from playwright.sync_api import sync_playwright

        print("🌐 브라우저 시작...")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            extracted_data = {}

            # 네이버 메인 페이지
            print("📍 이동: https://www.naver.com")
            page.goto("https://www.naver.com")
            page.wait_for_timeout(2000)

            # 네이버 스포츠 야구
            print("📍 이동: 네이버 스포츠 야구")
            page.goto("https://sports.news.naver.com/kbaseball/index")
            page.wait_for_timeout(2000)

            # 경기 일정 페이지
            print("📍 이동: 경기 일정")
            page.goto("https://sports.news.naver.com/kbaseball/schedule/index")
            page.wait_for_timeout(2000)

            # 데이터 추출 시도
            try:
                # 날짜 정보
                date_el = page.query_selector('.date_info, .selected_date')
                if date_el:
                    date_text = date_el.inner_text()
                    extracted_data['date'] = date_text
                    print(f"📅 날짜: {date_text}")

                # 경기 정보
                games = page.query_selector_all('.game_schedule li, .sch_tb')
                print(f"⚾ {len(games)}개 경기 발견")

                for i, game in enumerate(games[:5]):
                    game_text = game.inner_text()
                    extracted_data[f'game_{i+1}'] = game_text
                    print(f"  경기 {i+1}: {game_text[:50]}...")

            except Exception as e:
                print(f"⚠️ 데이터 추출 중 오류: {e}")

            # 스크린샷
            print("📸 스크린샷 저장...")
            page.screenshot(path="baseball_schedule.png")

            browser.close()

            print("\n✅ 스크래핑 완료!")
            print(f"📊 추출된 데이터: {len(extracted_data)}개")

            return extracted_data

    except ImportError:
        print("❌ playwright가 설치되지 않았습니다.")
        print("설치: pip install playwright")
        print("브라우저 설치: playwright install chromium")

        # 대안: REPLBrowser 사용
        print("\n🔄 REPLBrowser로 재시도...")
        from python.api.web_automation_repl import REPLBrowser

        browser = REPLBrowser()
        print("🌐 브라우저 시작...")
        browser.start()

        # 네이버 이동
        print("📍 이동: https://www.naver.com")
        browser.goto("https://www.naver.com")

        # 스포츠 페이지
        print("📍 이동: 네이버 스포츠")
        browser.goto("https://sports.news.naver.com/kbaseball/index")

        browser.stop()
        print("✅ 완료!")

        return {}

if __name__ == "__main__":
    data = main()
    if data:
        print("\n📊 추출 결과:")
        for key, value in data.items():
            print(f"  - {key}: {str(value)[:50]}...")
