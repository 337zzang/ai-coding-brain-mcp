#!/usr/bin/env python3
"""
자동 생성된 웹 자동화 스크립트
생성 시간: 2025-07-13 16:43:54
프로젝트: final_demo
총 액션 수: 7
"""

import time
from python.api.web_automation import WebAutomation


def main():
    """메인 실행 함수"""
    # WebAutomation 인스턴스 생성
    with WebAutomation(headless=False) as web:
        try:
            # 액션 1: navigate
            print("🌐 페이지 이동: https://www.google.com")
            result = web.go_to_page("https://www.google.com")
            if not result["success"]:
                raise Exception(f"페이지 이동 실패: {result['message']}")
            time.sleep(2)  # 페이지 로드 대기

            # 액션 2: navigate
            print("🌐 페이지 이동: https://www.github.com")
            result = web.go_to_page("https://www.github.com")
            if not result["success"]:
                raise Exception(f"페이지 이동 실패: {result['message']}")
            time.sleep(2)  # 페이지 로드 대기

            # 액션 3: navigate
            print("🌐 페이지 이동: https://www.python.org")
            result = web.go_to_page("https://www.python.org")
            if not result["success"]:
                raise Exception(f"페이지 이동 실패: {result['message']}")
            time.sleep(2)  # 페이지 로드 대기

            # 액션 4: navigate
            print("🌐 페이지 이동: https://www.python.org")
            result = web.go_to_page("https://www.python.org")
            if not result["success"]:
                raise Exception(f"페이지 이동 실패: {result['message']}")
            time.sleep(2)  # 페이지 로드 대기

            # 액션 5: input
            print("⌨️ 입력: tutorial...")
            result = web.input_text("input#id-search-field", "tutorial", by="css")
            if not result["success"]:
                raise Exception(f"입력 실패: {result['message']}")
            time.sleep(0.5)

            # 액션 6: input
            print("⌨️ 입력: tutorial...")
            result = web.input_text("input[name='q']", "tutorial", by="css")
            if not result["success"]:
                raise Exception(f"입력 실패: {result['message']}")
            time.sleep(0.5)

            # 액션 7: input
            print("⌨️ 입력: tutorial...")
            result = web.input_text("input[type='search']", "tutorial", by="css")
            if not result["success"]:
                raise Exception(f"입력 실패: {result['message']}")
            time.sleep(0.5)


        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            return False
        
        print("✅ 모든 작업 완료!")
        return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)