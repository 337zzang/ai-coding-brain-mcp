#!/usr/bin/env python3
"""
자동 생성된 웹 스크래핑 스크립트
생성일: 2025-07-27 17:39:42
URL: https://www.naver.com
"""

# === 설정 ===
URL = "https://www.naver.com"
SELECTORS = {
    "today_schedule": "div.game_schedule",
    "today_schedule_alt": "div.today_schedule",
    "top_news": "div.news_list li:first-child",
    "team_ranking": "div.team_rank",
}

# === 메인 함수 ===
def main():
    from python.api.web_automation_repl import REPLBrowser
    
    browser = REPLBrowser()
    extracted_data = {}
    
    try:
        # 브라우저 시작
        print("🌐 브라우저 시작...")
        browser.start()
        
        # 페이지 이동
        print("📍 이동: https://www.naver.com")
        browser.goto("https://www.naver.com")
        
        # 페이지 이동
        print("📍 이동: https://sports.news.naver.com/kbaseball/index")
        browser.goto("https://sports.news.naver.com/kbaseball/index")
        
        # 데이터 추출: today_schedule
        result = browser.eval("document.querySelector('div.game_schedule')?.innerText?.trim() || ''")
        if result.get("ok"):
            extracted_data["today_schedule"] = result.get("data")
            print(f"✅ today_schedule: {result.get('data')[:50]}...")
        
        # 데이터 추출: today_schedule_alt
        result = browser.eval("document.querySelector('div.today_schedule')?.innerText?.trim() || ''")
        if result.get("ok"):
            extracted_data["today_schedule_alt"] = result.get("data")
            print(f"✅ today_schedule_alt: {result.get('data')[:50]}...")
        
        # 데이터 추출: top_news
        result = browser.eval("document.querySelector('div.news_list li:first-child')?.innerText?.trim() || ''")
        if result.get("ok"):
            extracted_data["top_news"] = result.get("data")
            print(f"✅ top_news: {result.get('data')[:50]}...")
        
        # 데이터 추출: team_ranking
        result = browser.eval("document.querySelector('div.team_rank')?.innerText?.trim() || ''")
        if result.get("ok"):
            extracted_data["team_ranking"] = result.get("data")
            print(f"✅ team_ranking: {result.get('data')[:50]}...")
        
        # 페이지 이동
        print("📍 이동: https://m.sports.naver.com/kbaseball/schedule/index")
        browser.goto("https://m.sports.naver.com/kbaseball/schedule/index")
        
        return extracted_data
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return None
    finally:
        browser.stop()
        print("✅ 브라우저 종료")

if __name__ == "__main__":
    data = main()
    if data:
        print(f"
📊 추출 완료: {len(data)}개 데이터")
        for key, value in data.items():
            print(f"  - {key}: {str(value)[:50]}...")