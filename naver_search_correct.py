#!/usr/bin/env python3
"""
네이버 검색 자동화 스크립트
생성일: 2025-01-27
"""

from python.api.web_automation_repl import REPLBrowser
import time

def main():
    """네이버에서 '파이썬' 검색하기"""
    browser = REPLBrowser()

    try:
        # 브라우저 시작
        print("🌐 브라우저 시작...")
        result = browser.start()
        if result.get('status') != 'started':
            print(f"❌ 브라우저 시작 실패: {result}")
            return False

        # 네이버로 이동
        print("📍 네이버로 이동...")
        result = browser.goto("https://www.naver.com")
        if result.get('status') != 'success':
            print(f"❌ 페이지 이동 실패: {result}")
            return False
        print(f"   제목: {result.get('title')}")

        # 잠시 대기
        time.sleep(2)

        # 검색창에 입력
        print("⌨️ 검색창에 '파이썬' 입력...")
        result = browser.type('input[name="query"]', "파이썬")
        if result.get('status') != 'success':
            print(f"❌ 입력 실패: {result}")
            return False

        # 검색 버튼 클릭
        print("🖱️ 검색 버튼 클릭...")
        result = browser.click('button[type="submit"]')
        if result.get('status') != 'success':
            print(f"❌ 클릭 실패: {result}")
            return False

        # 결과 페이지 로드 대기
        time.sleep(2)

        # 페이지 제목 확인
        print("📊 페이지 제목 추출...")
        result = browser.eval('document.title')
        if result.get('status') == 'success':
            print(f"   제목: {result.get('result')}")

        # 검색 결과 추출 (선택사항)
        print("\n📋 검색 결과 추출...")
        result = browser.eval("""
            Array.from(document.querySelectorAll('.title_link')).slice(0, 5).map(el => el.innerText)
        """)
        if result.get('status') == 'success':
            results = result.get('result', [])
            print("   상위 5개 결과:")
            for i, title in enumerate(results, 1):
                print(f"   {i}. {title}")

        print("\n✅ 작업 완료!")
        return True

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False
    finally:
        # 브라우저 종료
        print("\n🛑 브라우저 종료...")
        browser.stop()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
