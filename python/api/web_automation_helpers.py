"""
웹 자동화 레코딩 헬퍼 함수들
REPLBrowserWithRecording을 사용하여 REPL 환경에서 쉽게 웹 자동화를 수행합니다.

작성일: 2025-01-27
"""
from typing import Dict, Any, Optional
from python.api.web_automation_integrated import REPLBrowserWithRecording
from .web_automation_errors import safe_execute


# 전역 인스턴스 저장
_web_instance: Optional[REPLBrowserWithRecording] = None

def _get_web_instance():
    """전역 _web_instance를 안전하게 가져오기"""
    # globals()에서 직접 가져오기 (JSON REPL 환경 대응)
    return globals().get('_web_instance', None)

def _set_web_instance(instance):
    """전역 _web_instance를 안전하게 설정"""
    globals()['_web_instance'] = instance



def web_start(headless: bool = False, project_name: str = "web_scraping") -> Dict[str, Any]:
    """
    웹 자동화 레코딩 시작

    Args:
        headless: 헤드리스 모드 여부 (기본값: False - 브라우저 표시)
        project_name: 프로젝트 이름

    Returns:
        시작 결과

    Example:
        >>> web_start()
        >>> web_goto("https://example.com")
        >>> web_click("button")
        >>> web_generate_script("my_scraper.py")
    """
    global _web_instance

    # 기존 인스턴스가 있으면 먼저 종료
    if _get_web_instance() and _get_web_instance().browser_started:
        _web_instance.stop()

    # 새 인스턴스 생성
    _web_instance = REPLBrowserWithRecording(headless=headless, project_name=project_name)

    # 브라우저 시작
    result = _web_instance.start()

    if result.get('ok'):
        print(f"✅ 웹 자동화 시작됨 (프로젝트: {project_name})")
        # 전역 변수에 강제로 설정 (JSON REPL 환경 대응)
        _set_web_instance(_web_instance)
    else:
        print(f"❌ 시작 실패: {result.get('error')}")

    return result


def _web_goto_impl(url: str, wait_until: str = 'load') -> Dict[str, Any]:
    """페이지 이동"""
    if not _get_web_instance():
        return {'ok': False, 'error': 'web_start()를 먼저 실행하세요'}

    result = _web_instance.goto(url, wait_until)
    if result.get('ok'):
        print(f"📍 이동: {url}")
    return result

def web_goto(url: str, wait_until: str = 'load') -> Dict[str, Any]:
    """페이지 이동 (에러 처리 강화)"""
    return safe_execute('web_goto', _web_goto_impl, url, wait_until)

def _web_click_impl(selector: str) -> Dict[str, Any]:
    """요소 클릭"""
    if not _get_web_instance():
        return {'ok': False, 'error': 'web_start()를 먼저 실행하세요'}

    result = _web_instance.click(selector)
    if result.get('ok'):
        print(f"🖱️ 클릭: {selector}")
    return result

def web_click(selector: str) -> Dict[str, Any]:
    """요소 클릭 (에러 처리 강화)"""
    return safe_execute('web_click', _web_click_impl, selector)

def _web_type_impl(selector: str, text: str) -> Dict[str, Any]:
    """텍스트 입력"""
    if not _get_web_instance():
        return {'ok': False, 'error': 'web_start()를 먼저 실행하세요'}

    result = _web_instance.type(selector, text)
    if result.get('ok'):
        print(f"⌨️ 입력: {selector} <- {text[:20]}...")
    return result


def web_extract(selector: str, name: Optional[str] = None, 
                extract_type: str = 'text') -> Dict[str, Any]:
    """
    데이터 추출

    Args:
        selector: CSS 선택자
        name: 데이터 이름 (자동 생성 가능)
        extract_type: 추출 타입 ('text', 'value', 'href', 'src', 'html')

    Returns:
        추출 결과 {'ok': bool, 'data': 추출값, 'name': 이름}
    """
    if not _get_web_instance():
        return {'ok': False, 'error': 'web_start()를 먼저 실행하세요'}

    result = _web_instance.extract(selector, name, extract_type)
    if result.get('ok'):
        data_preview = str(result.get('data', ''))[:50]
        print(f"📊 추출: {result.get('name')} = {data_preview}...")
    return result


def web_extract_table(table_selector: str, name: Optional[str] = None) -> Dict[str, Any]:
    """테이블 데이터 추출"""
    if not _get_web_instance():
        return {'ok': False, 'error': 'web_start()를 먼저 실행하세요'}

    result = _web_instance.extract_table(table_selector, name)
    if result.get('ok'):
        data = result.get('data', {})
        rows_count = len(data.get('rows', [])) if data else 0
        print(f"📊 테이블 추출: {result.get('name')} ({rows_count}개 행)")
    return result


def _web_wait_impl(seconds: float) -> Dict[str, Any]:
    """대기"""
    if not _get_web_instance():
        return {'ok': False, 'error': 'web_start()를 먼저 실행하세요'}

    print(f"⏳ {seconds}초 대기...")
    return _get_web_instance().wait(seconds)


def web_screenshot(path: Optional[str] = None) -> Dict[str, Any]:
    """스크린샷 캡처"""
    if not _get_web_instance():
        return {'ok': False, 'error': 'web_start()를 먼저 실행하세요'}

    result = _web_instance.screenshot(path)
    if result.get('ok'):
        print(f"📸 스크린샷 저장: {path or 'screenshot_*.png'}")
    return result


def web_generate_script(output_file: Optional[str] = None) -> Dict[str, Any]:
    """
    레코딩된 액션으로 스크래핑 스크립트 생성

    Args:
        output_file: 출력 파일 경로 (기본값: generated_scraper_*.py)

    Returns:
        생성 결과
    """
    if not _get_web_instance():
        return {'ok': False, 'error': 'web_start()를 먼저 실행하세요'}

    result = _web_instance.generate_script(output_file)
    if result.get('ok'):
        print(f"✅ 스크립트 생성: {result.get('file')}")
        print(f"   액션 수: {result.get('actions_count')}")
    return result


def _web_stop_impl() -> Dict[str, Any]:
    """웹 자동화 종료"""
    global _web_instance

    if not _get_web_instance():
        return {'ok': False, 'error': '실행 중인 인스턴스가 없습니다'}

    result = _web_instance.stop()
    if result.get('ok'):
        print("🛑 웹 자동화 종료")

    _web_instance = None
    return result


def _web_status_impl() -> Dict[str, Any]:
    """현재 상태 조회"""
    if not _get_web_instance():
        return {
            'ok': True,
            'running': False,
            'message': '웹 자동화가 시작되지 않았습니다'
        }

    return {
        'ok': True,
        'running': _web_instance.browser_started,
        'actions_count': len(_web_instance.recorder.actions),
        'extracted_data_count': len(_web_instance.extracted_data),
        'project_name': _web_instance.recorder.project_name
    }


def _web_get_data_impl() -> Dict[str, Any]:
    """추출된 모든 데이터 조회"""
    if not _web_instance:
        return {'ok': False, 'error': 'web_start()를 먼저 실행하세요'}

    data = _web_instance.get_extracted_data()
    return {'ok': True, 'data': data, 'count': len(data)}


# 간단한 데모
def web_demo():
    """웹 자동화 데모"""
    print("🎭 웹 자동화 데모 시작")
    print("-" * 40)

    # 1. 시작
    web_start()

    # 2. 구글 방문
    web_goto("https://www.google.com")
    web_wait(1)

    # 3. 검색
    web_type('textarea[name="q"]', "Python web scraping")
    web_wait(0.5)

    # 4. 스크린샷
    web_screenshot("google_search.png")

    # 5. 스크립트 생성
    web_generate_script("google_search_demo.py")

    # 6. 종료
    web_stop()

    print("-" * 40)
    print("✅ 데모 완료!")


# 기존 함수명과의 호환성을 위한 별칭
web_record_start = web_start
web_record_stop = web_generate_script
# web_record_status = web_status  # web_status는 아래에 정의되어 있으므로 나중에 설정

# Wrapper 함수들 (에러 처리 강화)

def web_type(selector: str, text: str) -> Dict[str, Any]:
    """텍스트 입력 (에러 처리 강화)"""
    return safe_execute('web_type', _web_type_impl, selector, text)


def web_extract(selector: str, name: str = None, extract_type: str = "text") -> Dict[str, Any]:
    """데이터 추출 (에러 처리 강화)"""
    return safe_execute('web_extract', _web_extract_impl, selector, name, extract_type)


def web_extract_table(table_selector: str, name: str = None) -> Dict[str, Any]:
    """테이블 데이터 추출 (에러 처리 강화)"""
    return safe_execute('web_extract_table', _web_extract_table_impl, table_selector, name)


def web_wait(seconds: float) -> Dict[str, Any]:
    """대기 (에러 처리 강화)"""
    return safe_execute('web_wait', _web_wait_impl, seconds)


def web_screenshot(path: str = None) -> Dict[str, Any]:
    """스크린샷 캡처 (에러 처리 강화)"""
    return safe_execute('web_screenshot', _web_screenshot_impl, path)

def web_generate_script(output_file: str = None) -> Dict[str, Any]:
    """기록된 액션으로 스크립트 생성 (에러 처리 강화)"""
    return safe_execute('web_generate_script', _web_generate_script_impl, output_file)

def web_stop() -> Dict[str, Any]:
    """브라우저 종료 (에러 처리 강화)"""
    return safe_execute('web_stop', _web_stop_impl, check_instance=False)

def web_status() -> Dict[str, Any]:
    """현재 상태 확인 (에러 처리 강화)"""
    return safe_execute('web_status', _web_status_impl, check_instance=False)

def web_get_data() -> Dict[str, Any]:
    """추출된 데이터 가져오기 (에러 처리 강화)"""
    return safe_execute('web_get_data', _web_get_data_impl)


# web_status 함수가 정의된 후에 별칭 설정
web_record_status = web_status
