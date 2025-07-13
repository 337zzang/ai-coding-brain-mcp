#!/usr/bin/env python3
"""
네이버 올스타전 검색 - 간단 버전
"""

from python.api.web_automation import WebAutomation
import time

# 브라우저 실행
web = WebAutomation(headless=False)

try:
    # 네이버 접속
    web.go_to_page("https://www.naver.com")
    time.sleep(2)

    # 검색
    web.input_text("input[name='query']", "올스타전", press_enter=True)
    time.sleep(3)

    # 결과 확인
    news = web.extract_text("a.news_tit", by="css", all_matches=True)
    if news["success"]:
        print(f"뉴스 {len(news.get('texts', []))}개 발견")
        for i, title in enumerate(news.get('texts', [])[:3], 1):
            print(f"{i}. {title[:50]}...")

finally:
    # 브라우저 종료
    web.close()
