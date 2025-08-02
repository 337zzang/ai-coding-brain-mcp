#!/usr/bin/env python3
"""
자동 생성된 웹 스크래핑 스크립트
생성일: 2025-08-02 09:52:47
URL: https://www.naver.com
"""

# === 설정 ===
URL = "https://www.naver.com"
SELECTORS = {
    "page_title": "title",
    "selector_1": "input#query",
    "selector_2": "button.btn_search",
    "first_result": "a.link_tit",
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
        
        # 데이터 추출: page_title
        result = browser.eval("document.querySelector('title')?.innerText?.trim() || ''")
        if result.get("ok"):
            extracted_data["page_title"] = result.get("data")
            print(f"✅ page_title: {result.get('data')[:50]}...")
        
        # 텍스트 입력
        browser.type("input#query", "AI 코딩 도구")
        
        # 클릭
        browser.click("button.btn_search")
        
        # 데이터 추출: first_result
        result = browser.eval("document.querySelector('a.link_tit')?.innerText?.trim() || ''")
        if result.get("ok"):
            extracted_data["first_result"] = result.get("data")
            print(f"✅ first_result: {result.get('data')[:50]}...")
        
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