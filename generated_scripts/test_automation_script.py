#!/usr/bin/env python3
"""
자동 생성된 웹 스크래핑 스크립트
생성일: 2025-07-27 20:38:17
URL: https://example.com
"""

# === 설정 ===
URL = "https://example.com"
SELECTORS = {
    "selector_0": "h1",
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
        print("📍 이동: https://example.com")
        browser.goto("https://example.com")
        
        # 데이터 추출: unknown
        result = browser.eval("document.querySelector('h1')?.innerText?.trim() || ''")
        if result.get("ok"):
            extracted_data["unknown"] = result.get("data")
            print(f"✅ unknown: {result.get('data')[:50]}...")
        
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