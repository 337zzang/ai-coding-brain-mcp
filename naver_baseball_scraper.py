#!/usr/bin/env python3
"""
자동 생성된 웹 스크래핑 스크립트
생성일: 2025-07-27 17:19:48
URL: https://www.naver.com
"""

# === 설정 ===
URL = "https://www.naver.com"
SELECTORS = {
    "today_date": "div.sch_tb div.td_date strong",
    "game_time": "span.td_hour",
    "home_team": "span.team_lft",
    "away_team": "span.team_rgt",
    "stadium": "span.td_stadium",
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
        print("📍 이동: https://sports.news.naver.com/kbaseball/schedule/index")
        browser.goto("https://sports.news.naver.com/kbaseball/schedule/index")
        
        # 데이터 추출: today_date
        result = browser.eval("document.querySelector('div.sch_tb div.td_date strong')?.innerText?.trim() || ''")
        if result.get("ok"):
            extracted_data["today_date"] = result.get("data")
            print(f"✅ today_date: {result.get('data')[:50]}...")
        
        # 데이터 추출: game_time
        result = browser.eval("document.querySelector('span.td_hour')?.innerText?.trim() || ''")
        if result.get("ok"):
            extracted_data["game_time"] = result.get("data")
            print(f"✅ game_time: {result.get('data')[:50]}...")
        
        # 데이터 추출: home_team
        result = browser.eval("document.querySelector('span.team_lft')?.innerText?.trim() || ''")
        if result.get("ok"):
            extracted_data["home_team"] = result.get("data")
            print(f"✅ home_team: {result.get('data')[:50]}...")
        
        # 데이터 추출: away_team
        result = browser.eval("document.querySelector('span.team_rgt')?.innerText?.trim() || ''")
        if result.get("ok"):
            extracted_data["away_team"] = result.get("data")
            print(f"✅ away_team: {result.get('data')[:50]}...")
        
        # 데이터 추출: stadium
        result = browser.eval("document.querySelector('span.td_stadium')?.innerText?.trim() || ''")
        if result.get("ok"):
            extracted_data["stadium"] = result.get("data")
            print(f"✅ stadium: {result.get('data')[:50]}...")
        
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