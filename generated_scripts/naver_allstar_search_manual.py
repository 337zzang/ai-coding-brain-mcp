#!/usr/bin/env python3
"""
네이버 올스타전 검색 자동화 스크립트
생성 시간: 2025-07-13
"""

import time
import sys
import os

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python.api.web_automation import WebAutomation


def search_naver_allstar():
    """네이버에서 올스타전 검색"""
    print("🎯 네이버 올스타전 검색 시작")

    # WebAutomation 인스턴스 생성
    with WebAutomation(headless=False) as web:
        try:
            # 1. 네이버 접속
            print("\n1️⃣ 네이버 홈페이지 접속...")
            result = web.go_to_page("https://www.naver.com")
            if not result["success"]:
                raise Exception(f"페이지 접속 실패: {result['message']}")
            print(f"✅ 접속 성공: {result['title']}")
            time.sleep(2)

            # 2. 검색어 입력
            print("\n2️⃣ 검색어 '올스타전' 입력...")
            result = web.input_text("input[name='query']", "올스타전", by="css")
            if not result["success"]:
                raise Exception(f"검색어 입력 실패: {result['message']}")
            print("✅ 검색어 입력 완료")
            time.sleep(0.5)

            # 3. 검색 실행 (Enter)
            print("\n3️⃣ 검색 실행...")
            result = web.input_text("input[name='query']", "", by="css", press_enter=True)
            print("✅ 검색 실행 완료")
            time.sleep(3)  # 검색 결과 로드 대기

            # 4. 검색 결과 분석
            print("\n4️⃣ 검색 결과 분석...")

            # 뉴스 제목 추출
            news_result = web.extract_text("a.news_tit", by="css", all_matches=True)
            if news_result["success"] and news_result.get("texts"):
                print(f"\n📰 관련 뉴스 ({len(news_result['texts'])}개):")
                for i, title in enumerate(news_result['texts'][:5], 1):
                    print(f"   {i}. {title[:60]}...")

            # 스포츠 정보 확인
            sports_result = web.extract_text("div.sports_area", by="css")
            if sports_result["success"] and sports_result.get("text"):
                print("\n⚾ 스포츠 섹션 정보 발견")
                text_preview = sports_result["text"][:200]
                print(f"   내용 미리보기: {text_preview}...")

            # 추가 정보 추출 시도
            # 날짜/일정 정보
            date_result = web.extract_text("span.date", by="css", all_matches=True)
            if date_result["success"] and date_result.get("texts"):
                print("\n📅 날짜 정보:")
                for date in date_result['texts'][:3]:
                    print(f"   - {date}")

            # 5. 스크린샷 (선택사항)
            print("\n5️⃣ 검색 결과 페이지 상태")
            page_info = web.get_page_content()
            if page_info["success"]:
                print(f"   - 현재 URL: {page_info['url']}")
                print(f"   - 페이지 제목: {page_info['title']}")
                print(f"   - 텍스트 길이: {page_info['text_length']:,}자")

            print("\n✅ 검색 완료!")
            return True

        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            return False


def main():
    """메인 실행 함수"""
    success = search_naver_allstar()

    if success:
        print("\n🎉 네이버 올스타전 검색 자동화 성공!")
    else:
        print("\n😢 검색 중 문제가 발생했습니다.")

    return success


if __name__ == "__main__":
    # 스크립트 실행
    result = main()
    exit(0 if result else 1)
