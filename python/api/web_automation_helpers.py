"""
웹 자동화 레코딩 헬퍼 함수들
"""

from typing import Dict, Any, Optional
from python.api.web_automation_extended import WebAutomationWithRecording

# 전역 인스턴스 저장
_recorder_instance: Optional[WebAutomationWithRecording] = None


def web_record_start(headless: bool = False, project_name: str = "web_automation") -> WebAutomationWithRecording:
    """웹 자동화 레코딩 시작

    Args:
        headless: 헤드리스 모드 여부 (기본값: False - 브라우저 표시)
        project_name: 프로젝트 이름

    Returns:
        WebAutomationWithRecording: 레코딩 가능한 웹 자동화 인스턴스

    Example:
        >>> web = web_record_start()
        >>> web.go_to_page("https://example.com")
        >>> web.click_element("button", by="css")
        >>> web_record_stop("my_script.py")
    """
    global _recorder_instance

    # 기존 인스턴스가 있으면 종료
    if _recorder_instance:
        _recorder_instance.close()

    # 새 인스턴스 생성
    _recorder_instance = WebAutomationWithRecording(
        headless=headless,
        record_actions=True,
        project_name=project_name
    )

    return _recorder_instance


def web_record_stop(output_file: str = None) -> Dict[str, Any]:
    """레코딩 중지 및 스크립트 생성

    Args:
        output_file: 출력 파일 경로 (기본값: 자동 생성)

    Returns:
        Dict: 스크립트 생성 결과
    """
    global _recorder_instance

    if not _recorder_instance:
        return {
            "success": False,
            "message": "레코딩 중인 인스턴스가 없습니다. web_record_start()를 먼저 호출하세요."
        }

    # 스크립트 생성
    result = _recorder_instance.generate_script(output_file)

    # 브라우저 종료
    _recorder_instance.close()
    _recorder_instance = None

    return result


def web_record_status() -> Dict[str, Any]:
    """현재 레코딩 상태 조회

    Returns:
        Dict: 레코딩 상태 정보
    """
    global _recorder_instance

    if not _recorder_instance:
        return {
            "success": True,
            "recording": False,
            "message": "레코딩 중인 인스턴스가 없습니다."
        }

    return _recorder_instance.get_recording_status()


def web_record_demo():
    """레코딩 기능 데모

    간단한 예제를 통해 레코딩 기능을 시연합니다.
    """
    print("🎬 웹 자동화 레코딩 데모 시작")

    # 레코딩 시작
    web = web_record_start(headless=False, project_name="demo")

    try:
        # 구글 검색 시연
        print("1️⃣ 구글 홈페이지 접속")
        result = web.go_to_page("https://www.google.com")
        if not result['success']:
            print(f"❌ 페이지 접속 실패: {result['message']}")
            return

        # 검색어 입력
        print("2️⃣ 검색어 입력")
        result = web.input_text("textarea[name='q']", "Playwright Python", by="css")
        if not result['success']:
            print(f"❌ 검색어 입력 실패: {result['message']}")
            return

        # 검색 버튼 클릭
        print("3️⃣ 검색 실행")
        result = web.input_text("textarea[name='q']", "", by="css", press_enter=True)

        # 잠시 대기
        import time
        time.sleep(3)

        # 스크립트 생성
        print("4️⃣ 스크립트 생성 중...")
        result = web_record_stop("generated_scripts/google_search_demo.py")

        if result['success']:
            print(f"✅ 데모 완료!")
            print(f"📄 생성된 스크립트: {result['script_path']}")
            print(f"📊 총 액션 수: {result['total_actions']}")
            print(f"⏱️ 소요 시간: {result['duration']:.2f}초")
        else:
            print(f"❌ 스크립트 생성 실패: {result['message']}")

    except Exception as e:
        print(f"❌ 데모 중 오류 발생: {e}")
        if _recorder_instance:
            _recorder_instance.close()


# ai_helpers에 추가할 함수들
def web_automation_record_start(**kwargs):
    """헬퍼 함수: 웹 자동화 레코딩 시작"""
    return web_record_start(**kwargs)

def web_automation_record_stop(**kwargs):
    """헬퍼 함수: 웹 자동화 레코딩 중지 및 스크립트 생성"""
    return web_record_stop(**kwargs)

def web_automation_record_status():
    """헬퍼 함수: 웹 자동화 레코딩 상태 조회"""
    return web_record_status()
