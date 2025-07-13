"""
웹 자동화 레코딩 사용 예제
"""

from python.ai_helpers import (
    web_automation_record_start,
    web_automation_record_stop,
    web_automation_record_status
)

def example_1_basic_recording():
    """기본 레코딩 예제"""
    print("=== 기본 레코딩 예제 ===")

    # 1. 레코딩 시작
    web = web_automation_record_start(headless=False, project_name="basic_example")

    # 2. 웹 자동화 작업 수행
    web.go_to_page("https://example.com")
    web.click_element("h1", by="css")
    web.input_text("input[type='text']", "Hello World", by="css")

    # 3. 레코딩 상태 확인
    status = web_automation_record_status()
    print(f"레코딩 상태: {status}")

    # 4. 스크립트 생성
    result = web_automation_record_stop("my_automation_script.py")
    print(f"스크립트 생성 결과: {result}")


def example_2_login_automation():
    """로그인 자동화 레코딩 예제"""
    print("\n=== 로그인 자동화 레코딩 예제 ===")

    # 레코딩 시작
    web = web_automation_record_start(headless=False, project_name="login_automation")

    try:
        # 로그인 페이지로 이동
        web.go_to_page("https://example.com/login")

        # 아이디/비밀번호 입력
        web.input_text("input[name='username']", "myusername", by="css")
        web.input_text("input[name='password']", "mypassword", by="css")

        # 로그인 버튼 클릭
        web.click_element("button[type='submit']", by="css")

        # 페이지 로드 대기
        import time
        time.sleep(2)

        # 로그인 후 작업
        web.extract_text("h1.welcome", by="css")

    finally:
        # 스크립트 생성
        result = web_automation_record_stop("login_automation.py")
        print(f"생성된 스크립트: {result.get('script_path')}")


def example_3_search_and_extract():
    """검색 및 데이터 추출 레코딩 예제"""
    print("\n=== 검색 및 데이터 추출 레코딩 예제 ===")

    web = web_automation_record_start(headless=False, project_name="search_extract")

    try:
        # 구글 검색
        web.go_to_page("https://www.google.com")
        web.input_text("textarea[name='q']", "Python Playwright tutorial", by="css", press_enter=True)

        # 검색 결과 대기
        import time
        time.sleep(2)

        # 검색 결과 추출
        web.extract_text("h3", by="css", all_matches=True)

        # 페이지 스크롤
        web.scroll_page(action="down")

        # 스크린샷 (기록되지 않음 - 추가 구현 필요)
        # web.take_screenshot("search_results.png")

    finally:
        # 스크립트 생성
        result = web_automation_record_stop("search_and_extract.py")
        if result['success']:
            print(f"✅ 스크립트 생성 성공!")
            print(f"   - 스크립트: {result['script_path']}")
            print(f"   - 로그: {result['log_path']}")
            print(f"   - 총 액션: {result['total_actions']}")


def example_4_advanced_recording():
    """고급 레코딩 예제 - 조건부 작업"""
    print("\n=== 고급 레코딩 예제 ===")

    web = web_automation_record_start(headless=False, project_name="advanced_example")

    try:
        # 웹사이트 접속
        web.go_to_page("https://httpbin.org/forms/post")

        # 폼 필드 채우기
        web.input_text("input[name='custname']", "John Doe", by="css")
        web.input_text("input[name='custtel']", "123-456-7890", by="css")
        web.input_text("input[name='custemail']", "john@example.com", by="css")

        # 셀렉트 박스 선택 (추가 구현 필요)
        # web.select_option("select[name='size']", "large", by="css")

        # 체크박스 선택
        web.click_element("input[value='bacon']", by="css")
        web.click_element("input[value='cheese']", by="css")

        # 텍스트 영역
        web.input_text("textarea[name='comments']", "Please deliver after 6 PM", by="css")

        # 제출
        web.click_element("button[type='submit']", by="css")

        # 결과 확인
        import time
        time.sleep(2)
        web.extract_text("pre", by="css")

    finally:
        # 스크립트 생성
        result = web_automation_record_stop("form_submission.py")
        print(f"스크립트 생성 완료: {result}")


if __name__ == "__main__":
    # 예제 실행
    # example_1_basic_recording()
    # example_2_login_automation()
    # example_3_search_and_extract()
    # example_4_advanced_recording()

    # 또는 내장 데모 실행
    from python.ai_helpers import web_record_demo
    web_record_demo()
