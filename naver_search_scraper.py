#!/usr/bin/env python3
"""
자동 생성된 웹 자동화 스크립트
생성 시간: 2025-07-27 16:56:31
프로젝트: naver_test
총 액션 수: 4
"""

import time
from python.api.web_automation import WebAutomation


def main():
    """메인 실행 함수"""
    # WebAutomation 인스턴스 생성
    with WebAutomation(headless=False) as web:
        try:
            # 액션 1: navigate
            print("🌐 페이지 이동: https://www.naver.com")
            result = web.go_to_page("https://www.naver.com")
            if not result["success"]:
                raise Exception(f"페이지 이동 실패: {result['message']}")
            time.sleep(2)  # 페이지 로드 대기

            # 액션 2: input
            print("⌨️ 입력: 파이썬...")
            result = web.input_text("input[name="query"]", "파이썬", by="css")
            if not result["success"]:
                raise Exception(f"입력 실패: {result['message']}")
            time.sleep(0.5)

            # 액션 3: click
            print("🖱️ 클릭: button[type="submit"]")
            result = web.click_element("button[type="submit"]", by="css")
            if not result["success"]:
                raise Exception(f"클릭 실패: {result['message']}")
            time.sleep(1)

            # 액션 4: extract
            print("📋 텍스트 추출: title")
            result = web.extract_text("title", by="css")
            if result["success"]:
                print(f"추출된 텍스트: {result['text'][:100]}...")


        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            return False
        
        print("✅ 모든 작업 완료!")
        return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)