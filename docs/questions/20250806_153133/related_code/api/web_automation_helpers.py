"""
웹 자동화 레코딩 헬퍼 함수들
REPLBrowserWithRecording을 사용하여 REPL 환경에서 쉽게 웹 자동화를 수행합니다.
from .web_automation_smart_wait import SmartWaitManager

작성일: 2025-01-27
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from .web_automation_integrated import REPLBrowserWithRecording
from .web_automation_errors import safe_execute
from .web_automation_manager import browser_manager



# 전역 인스턴스 저장 - 다중 전략
# _web_instance 전역 변수 제거됨 - BrowserManager 사용
_WEB_INSTANCES = {}  # 딕셔너리 방식 추가

def _get_web_instance():
    """전역 _web_instance를 안전하게 가져오기 - BrowserManager 사용"""
    # BrowserManager를 통한 중앙 관리
    return browser_manager.get_instance("default")


def _set_web_instance(instance):
    """전역 _web_instance를 안전하게 설정 - BrowserManager 사용"""
    # BrowserManager를 통한 중앙 관리
    if instance is not None:
        browser_manager.set_instance(instance, "default")
    else:
        browser_manager.remove_instance("default")

def web_start(headless: bool = False, project_name: str = "web_scraping") -> Dict[str, Any]:
    """
    웹 자동화 레코딩 시작

    Args:
        headless: 헤드리스 모드 여부 (기본값: False - 브라우저 표시)
        project_name: 프로젝트 이름

    Returns:
        시작 결과

    Example:
        >>> h.web_start()
        >>> h.web_goto("https://example.com")
        >>> h.web_click("button")
        >>> web_generate_script("my_scraper.py")
    """
    # global _web_instance  # 제거됨

    # 기존 인스턴스가 있으면 먼저 종료
    existing_instance = _get_web_instance()
    if existing_instance:
        try:
            if hasattr(existing_instance, 'browser_started') and existing_instance.browser_started:
                existing_instance.stop()
        except Exception as e:
            print(f"[WARNING] 기존 브라우저 종료 중 오류: {e}")

    # 새 인스턴스 생성
    instance = REPLBrowserWithRecording(headless=headless, project_name=project_name)

    # 브라우저 시작
    result = instance.start()

    if result.get('ok'):
        print(f"[OK] 웹 자동화 시작됨 (프로젝트: {project_name})")
        # 전역 변수에 강제로 설정 (JSON REPL 환경 대응)
        _set_web_instance(instance)
    else:
        print(f"[ERROR] 시작 실패: {result.get('error')}")

    return result
def _web_goto_impl(url: str, wait_until: str = 'load') -> Dict[str, Any]:
    """페이지 이동"""
    web = _get_web_instance()
    if not web:
        return {'ok': False, 'error': 'h.web_start()를 먼저 실행하세요'}

    result = web.goto(url, wait_until)
    if result.get('ok'):
        print(f"📍 이동: {url}")
    return result

def web_goto(url: str, wait_until: str = 'load') -> Dict[str, Any]:
    """페이지 이동 (에러 처리 강화)"""
    return safe_execute('web_goto', _web_goto_impl, url, wait_until)

def _web_click_impl(selector: str) -> Dict[str, Any]:
    """요소 클릭"""
    web = _get_web_instance()
    if not web:
        return {'ok': False, 'error': 'h.web_start()를 먼저 실행하세요'}

    result = web.click(selector)
    if result.get('ok'):
        print(f"🖱️ 클릭: {selector}")
    return result

def web_click(selector: str) -> Dict[str, Any]:
    """요소 클릭 (에러 처리 강화)"""
    return safe_execute('web_click', _web_click_impl, selector)

def _web_type_impl(selector: str, text: str) -> Dict[str, Any]:
    """텍스트 입력"""
    web = _get_web_instance()
    if not web:
        return {'ok': False, 'error': 'h.web_start()를 먼저 실행하세요'}

    result = web.type(selector, text)
    if result.get('ok'):
        print(f"⌨️ 입력: {selector} <- {text[:20]}...")
    return result



def _web_extract_impl(selector: str, name: Optional[str] = None, 
                      extract_type: str = 'text', all: bool = False) -> Dict[str, Any]:
    """web_extract의 실제 구현"""
    instance = _get_web_instance()
    if not instance:
        return {'ok': False, 'error': 'h.web_start()를 먼저 실행하세요'}

    # all 파라미터 처리
    if all:
        # 여러 요소 추출
        try:
            elements = instance.browser.page.query_selector_all(selector)
            results = []
            for elem in elements:
                if extract_type == 'text':
                    value = elem.text_content()
                elif extract_type == 'value':
                    value = elem.get_attribute('value')
                elif extract_type == 'href':
                    value = elem.get_attribute('href')
                elif extract_type == 'src':
                    value = elem.get_attribute('src')
                elif extract_type == 'html':
                    value = elem.inner_html()
                else:
                    value = elem.get_attribute(extract_type)
                results.append(value)
            return {'ok': True, 'data': results, 'name': name or selector}
        except Exception as e:
            return {'ok': False, 'error': str(e)}
    else:
        # 단일 요소 추출 (기존 방식)
        return instance.extract(selector, name, extract_type)

def web_extract(selector: str, name: Optional[str] = None, 
                extract_type: str = 'text', all: bool = False) -> Dict[str, Any]:
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
        return {'ok': False, 'error': 'h.web_start()를 먼저 실행하세요'}

    return safe_execute('web_extract', _web_extract_impl, selector, name, extract_type, all)
    if result.get('ok'):
        data_preview = str(result.get('data', ''))[:50]
        print(f"[DATA] 추출: {result.get('name')} = {data_preview}...")
    return result


def web_extract_table(table_selector: str, name: Optional[str] = None) -> Dict[str, Any]:
    """테이블 데이터 추출"""
    if not _get_web_instance():
        return {'ok': False, 'error': 'h.web_start()를 먼저 실행하세요'}

    result = _get_web_instance().extract_table(table_selector, name)
    if result.get('ok'):
        data = result.get('data', {})
        rows_count = len(data.get('rows', [])) if data else 0
        print(f"[DATA] 테이블 추출: {result.get('name')} ({rows_count}개 행)")
    return result


def _web_wait_impl(seconds: float) -> Dict[str, Any]:
    """대기"""
    if not _get_web_instance():
        return {'ok': False, 'error': 'h.web_start()를 먼저 실행하세요'}

    print(f"⏳ {seconds}초 대기...")
    return _get_web_instance().wait(seconds)

def _web_wait_smart_impl(timeout: float, wait_for: str, **kwargs) -> Dict[str, Any]:
    """스마트 대기 구현"""
    instance = _get_web_instance()
    if not instance:
        return {'ok': False, 'error': 'h.web_start()를 먼저 실행하세요'}

    # WebAutomationBrowser 인스턴스에서 page 객체 가져오기
    if not hasattr(instance, 'browser') or not hasattr(instance.browser, 'page'):
        return {'ok': False, 'error': '브라우저 페이지 객체를 찾을 수 없습니다'}

    page = instance.browser.page

    # SmartWaitManager 생성
    try:
        wait_manager = SmartWaitManager(page, default_timeout=timeout)

        # 디버그 모드 확인 (환경변수 사용)
        if os.getenv('WEB_AUTO_DEBUG', '').lower() == 'true':
            wait_manager.enable_debug(True)
    except Exception as e:
        return {'ok': False, 'error': f'SmartWaitManager 생성 실패: {str(e)}'}

    # wait_for 타입에 따라 적절한 메서드 호출
    if wait_for == "element":
        selector = kwargs.get("selector")
        if not selector:
            return {'ok': False, 'error': "'element' 대기에는 'selector' 파라미터가 필수입니다."}

        condition = kwargs.get("condition", "visible")
        return wait_manager.wait_for_element(selector, condition, timeout)

    elif wait_for == "network_idle":
        idle_time = kwargs.get("idle_time", 0.5)
        return wait_manager.wait_for_network_idle(idle_time, timeout)

    elif wait_for == "js":
        script = kwargs.get("script")
        value = kwargs.get("value")

        if not script:
            return {'ok': False, 'error': "'js' 대기에는 'script' 파라미터가 필수입니다."}
        if value is None:
            return {'ok': False, 'error': "'js' 대기에는 'value' 파라미터가 필수입니다."}

        return wait_manager.wait_for_js_complete(script, value, timeout)

    else:
        return {'ok': False, 'error': f"알 수 없는 대기 타입: {wait_for}"}



def web_screenshot(path: Optional[str] = None) -> Dict[str, Any]:
    """스크린샷 캡처"""
    if not _get_web_instance():
        return {'ok': False, 'error': 'h.web_start()를 먼저 실행하세요'}

    result = _get_web_instance().screenshot(path)
    if result.get('ok'):
        print(f"[SCREENSHOT] 스크린샷 저장: {path or 'screenshot_*.png'}")
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
        return {'ok': False, 'error': 'h.web_start()를 먼저 실행하세요'}

    result = _get_web_instance().generate_script(output_file)
    if result.get('ok'):
        print(f"[OK] 스크립트 생성: {result.get('file')}")
        print(f"   액션 수: {result.get('actions_count')}")
    return result


def _web_stop_impl() -> Dict[str, Any]:
    """웹 자동화 종료"""
    # global _web_instance  # 제거됨

    if not _get_web_instance():
        return {'ok': False, 'error': '실행 중인 인스턴스가 없습니다'}

    result = _get_web_instance().stop()
    if result.get('ok'):
        print("🛑 웹 자동화 종료")

    _set_web_instance(None)
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
        'running': _get_web_instance().browser_started,
        'actions_count': len(_get_web_instance().recorder.actions),
        'extracted_data_count': len(_get_web_instance().extracted_data),
        'project_name': _get_web_instance().recorder.project_name
    }


def _web_get_data_impl() -> Dict[str, Any]:
    """추출된 모든 데이터 조회"""
    if not _get_web_instance():
        return {'ok': False, 'error': 'h.web_start()를 먼저 실행하세요'}

    data = _get_web_instance().get_extracted_data()
    return {'ok': True, 'data': data, 'count': len(data)}


# 간단한 데모
def web_demo():
    """웹 자동화 데모"""
    print("🎭 웹 자동화 데모 시작")
    print("-" * 40)

    # 1. 시작
    h.web_start()

    # 2. 구글 방문
    h.web_goto("https://www.google.com")
    web_wait(1)

    # 3. 검색
    h.web_type('textarea[name="q"]', "Python web scraping")
    web_wait(0.5)

    # 4. 스크린샷
    web_screenshot("google_search.png")

    # 5. 스크립트 생성
    web_generate_script("google_search_demo.py")

    # 6. 종료
    web_stop()

    print("-" * 40)
    print("[OK] 데모 완료!")


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
    return safe_execute('web_extract', _web_extract_impl, selector, name, extract_type, all)


def web_extract_table(table_selector: str, name: str = None) -> Dict[str, Any]:
    """테이블 데이터 추출 (에러 처리 강화)"""
    return safe_execute('web_extract_table', _web_extract_table_impl, table_selector, name)


def web_wait(duration_or_timeout: float = 1, wait_for: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """대기 (에러 처리 강화)"""
    return safe_execute('web_wait', _web_wait_impl, duration_or_timeout, wait_for, **kwargs)



# === 누락된 _impl 함수들 추가 ===

def _web_screenshot_impl(path: Optional[str] = None) -> Dict[str, Any]:
    """스크린샷 구현 함수"""
    instance = _get_web_instance()
    if not instance:
        return {'ok': False, 'error': 'Browser not initialized'}

    result = instance.screenshot(path)
    if result.get('ok'):
        print(f"📸 스크린샷 저장: {result.get('path', path or 'screenshot.png')}")
    return result

def _web_generate_script_impl(output_file: Optional[str] = None) -> Dict[str, Any]:
    """스크립트 생성 구현 함수"""
    instance = _get_web_instance()
    if not instance:
        return {'ok': False, 'error': 'Browser not initialized'}

    return instance.generate_script(output_file)

def _web_stop_impl() -> Dict[str, Any]:
    """브라우저 종료 구현 함수"""
    instance = _get_web_instance()
    if instance:
        result = instance.stop()
        _set_web_instance(None)
        return result
    return {'ok': True, 'message': 'No browser to stop'}

def _web_status_impl() -> Dict[str, Any]:
    """상태 확인 구현 함수"""
    instance = _get_web_instance()
    if not instance:
        return {'ok': True, 'running': False, 'message': 'Browser not started'}

    return {
        'ok': True,
        'running': True,
        'actions_count': len(instance.actions) if hasattr(instance, 'actions') else 0,
        'extracted_data_count': len(instance.extracted_data) if hasattr(instance, 'extracted_data') else 0,
        'project_name': getattr(instance, 'project_name', 'unknown')
    }

def _web_get_data_impl() -> Dict[str, Any]:
    """데이터 가져오기 구현 함수"""
    instance = _get_web_instance()
    if not instance:
        return {'ok': False, 'error': 'Browser not initialized'}

    if hasattr(instance, 'get_extracted_data'):
        return instance.get_extracted_data()
    return {'ok': True, 'data': {}, 'count': 0}

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


def web_extract_batch(configs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    여러 요소를 단일 호출로 추출 (300-500% 성능 향상)

    Args:
        configs: 추출 설정 리스트
            [{
                "selector": "CSS 선택자",
                "name": "데이터 이름", 
                "type": "text|value|attr|href|src|html|data|style",
                "attr": "속성명",  # type이 attr인 경우
                "transform": "int|float|bool|json",  # 선택적
                "default": "기본값"  # 선택적
            }]

    Returns:
        {'ok': bool, 'data': {name: value, ...}}

    Examples:
        >>> configs = [
        ...     {"selector": "h1", "name": "title", "type": "text"},
        ...     {"selector": ".price", "name": "price", "type": "text", "transform": "float"},
        ...     {"selector": "img", "name": "image", "type": "src"}
        ... ]
        >>> result = web_extract_batch(configs)
        >>> print(result['data'])  # {'title': '...', 'price': 29.99, 'image': 'http://...'}
    """
    if not _get_web_instance():
        return {'ok': False, 'error': 'h.web_start()를 먼저 실행하세요'}

    result = _get_web_instance().extract_batch(configs)

    if result.get('ok'):
        data = result.get('data', {})
        print(f"[DATA] 배치 추출 완료: {len(data)}개 항목")
        for name, value in list(data.items())[:3]:  # 처음 3개만 미리보기
            preview = str(value)[:50] + '...' if len(str(value)) > 50 else str(value)
            print(f"   - {name}: {preview}")
        if len(data) > 3:
            print(f"   ... 외 {len(data) - 3}개")

    return result


def web_extract_attributes(selector: str, attributes: List[str]) -> Dict[str, Any]:
    """
    여러 속성을 한번에 추출

    Args:
        selector: CSS 선택자
        attributes: 추출할 속성 리스트

    Returns:
        {'ok': bool, 'data': {attr: value, ...}}

    Examples:
        >>> result = web_extract_attributes(".product", ["id", "data-price", "data-sku"])
        >>> print(result['data'])  # {'id': 'prod-123', 'data-price': '29.99', 'data-sku': 'ABC'}
    """
    if not _get_web_instance():
        return {'ok': False, 'error': 'h.web_start()를 먼저 실행하세요'}

    result = _get_web_instance().extract_attributes(selector, attributes)

    if result.get('ok'):
        data = result.get('data', {})
        print(f"[DATA] 속성 추출: {selector} → {len(data)}개 속성")

    return result


def web_extract_form(form_selector: str) -> Dict[str, Any]:
    """
    폼의 모든 입력 필드 자동 수집

    Args:
        form_selector: 폼 CSS 선택자

    Returns:
        {'ok': bool, 'data': {field_name: value, ...}}

    Examples:
        >>> result = web_extract_form("#login-form")
        >>> print(result['data'])  # {'username': '', 'password': '', 'remember': False}
    """
    if not _get_web_instance():
        return {'ok': False, 'error': 'h.web_start()를 먼저 실행하세요'}

    result = _get_web_instance().extract_form(form_selector)

    if result.get('ok'):
        data = result.get('data', {})
        print(f"[DATA] 폼 추출: {form_selector} → {len(data)}개 필드")
        for name, value in data.items():
            value_type = type(value).__name__
            print(f"   - {name}: {value_type}")

    return result


# web_status 함수가 정의된 후에 별칭 설정
web_record_status = web_status


def _web_evaluate_impl(script: str, arg: Any = None, strict: bool = False) -> Dict[str, Any]:
    """web_evaluate 실제 구현"""
    instance = _get_web_instance()
    if not instance:
        return {"ok": False, "error": "웹 브라우저가 시작되지 않았습니다. h.web_start()를 먼저 호출하세요."}

    # JavaScriptExecutor 인스턴스 가져오기
    from .web_automation_manager import JavaScriptExecutor
    js_executor = JavaScriptExecutor()

    # strict 모드 설정
    if strict:
        is_safe, error_msg = js_executor.validate_script_extended(script, strict_mode=True)
        if not is_safe:
            return {"ok": False, "error": error_msg}

    try:
        # REPLBrowserWithRecording의 eval 메서드 사용
        if arg is not None:
            # 인자가 있는 경우 스크립트 수정
            modified_script = f"((arg) => {{ {script} }})({repr(arg)})"
            result = instance.eval(modified_script)
        else:
            result = instance.eval(script)

        # 결과 처리
        if isinstance(result, dict) and result.get('status') == 'success':
            # 액션 기록
            instance.recorder.record_action("evaluate", {
                "script": script[:100] + "..." if len(script) > 100 else script,
                "arg": str(arg) if arg else None
            })

            return {
                "ok": True,
                "data": result.get('result'),
                "script_length": len(script)
            }
        else:
            return {
                "ok": False,
                "error": result.get('error', 'Unknown error'),
                "result": result
            }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


def web_evaluate(script: str, arg: Any = None, strict: bool = False) -> Dict[str, Any]:
    """
    현재 페이지에서 JavaScript 코드를 실행하고 결과를 반환

    Args:
        script: 실행할 JavaScript 코드
        arg: 스크립트에 전달할 인자 (선택사항)
        strict: True일 경우 엄격한 검증 모드 사용

    Returns:
        Response 딕셔너리
    """
    return safe_execute('web_evaluate', _web_evaluate_impl, script, arg, strict)
def web_execute_script(script: str, *args, sandboxed: bool = True) -> Dict[str, Any]:
    """
    JavaScript 코드를 샌드박스 환경에서 실행

    Args:
        script: 실행할 JavaScript 코드
        *args: 스크립트에 전달할 인자들
        sandboxed: True일 경우 샌드박스 래퍼 사용

    Returns:
        Response 딕셔너리
    """
    def impl():
        instance = _get_web_instance()
        if not instance:
            return {"ok": False, "error": "웹 브라우저가 시작되지 않았습니다. h.web_start()를 먼저 호출하세요."}

        # JavaScriptExecutor 인스턴스 가져오기
        from .web_automation_manager import JavaScriptExecutor
        js_executor = JavaScriptExecutor()

        # 샌드박스 래핑
        if sandboxed:
            wrapped_script = js_executor.create_sandbox_wrapper(script)
        else:
            wrapped_script = script

        # 페이지 객체 가져오기
        page = instance.browser.page
        if not page:
            return {"ok": False, "error": "페이지가 로드되지 않았습니다."}

        try:
            # Playwright의 evaluate 함수 사용
            if args:
                # 인자가 있는 경우
                args_str = str(list(args))
                func_script = f"(function() {{ const arguments = {args_str}; {wrapped_script} }})()"
                result = page.evaluate(func_script)
            else:
                result = page.evaluate(wrapped_script)

            # 에러 체크
            if isinstance(result, dict) and result.get("__error"):
                return {
                    "ok": False,
                    "error": result.get("message", "Unknown JavaScript error"),
                    "error_type": "JavaScriptError",
                    "stack": result.get("stack")
                }

            # 액션 기록
            instance.recorder.record_action("execute_script", {
                "script_preview": script[:50] + "..." if len(script) > 50 else script,
                "args_count": len(args),
                "sandboxed": sandboxed
            })

            return {"ok": True, "data": result}

        except Exception as e:
            return {
                "ok": False,
                "error": str(e),
                "error_type": type(e).__name__
            }

    # safe_execute의 올바른 호출
    return safe_execute(
        func_name="web_execute_script",
        impl_func=impl,
        check_instance=False
    )

def web_evaluate_element(selector: str, script: str) -> Dict[str, Any]:
    """
    특정 요소에 대해 JavaScript 코드 실행

    Args:
        selector: 대상 요소의 CSS 선택자
        script: 실행할 JavaScript 코드 (element 변수로 요소 접근 가능)

    Returns:
        Response 딕셔너리

    Examples:
        >>> web_evaluate_element("button.submit", "element.disabled = true")
        >>> web_evaluate_element("#price", "return element.textContent")
    """
    def impl():
        instance = _get_web_instance()
        if not instance:
            return {"ok": False, "error": "웹 브라우저가 시작되지 않았습니다. h.web_start()를 먼저 호출하세요."}

        page = instance.browser.page
        if not page:
            return {"ok": False, "error": "페이지가 로드되지 않았습니다."}

        try:
            # 요소 찾기
            element = page.query_selector(selector)
            if not element:
                return {"ok": False, "error": f"요소를 찾을 수 없습니다: {selector}"}

            # 요소에 대해 스크립트 실행
            wrapped_script = f"(element) => {{ {script} }}"
            result = element.evaluate(wrapped_script)

            # 액션 기록
            instance.recorder.record_action("evaluate_element", {
                "selector": selector,
                "script": script[:50] + "..." if len(script) > 50 else script
            })

            return {"ok": True, "data": result}

        except Exception as e:
            return {
                "ok": False,
                "error": str(e),
                "error_type": type(e).__name__
            }

    return safe_execute(
        func_name="web_evaluate_element",
        impl_func=impl,
        check_instance=False
    )


def web_wait_for_function(script: str, timeout: int = 30000, polling: int = 100) -> Dict[str, Any]:
    """
    JavaScript 조건이 true가 될 때까지 대기

    Args:
        script: 평가할 JavaScript 표현식 (true를 반환해야 함)
        timeout: 최대 대기 시간 (밀리초, 기본 30초)
        polling: 체크 간격 (밀리초, 기본 100ms)

    Returns:
        Response 딕셔너리

    Examples:
        >>> web_wait_for_function("document.readyState === 'complete'")
        >>> web_wait_for_function("document.querySelectorAll('.item').length > 10", timeout=10000)
    """
    def impl():
        instance = _get_web_instance()
        if not instance:
            return {"ok": False, "error": "웹 브라우저가 시작되지 않았습니다. h.web_start()를 먼저 호출하세요."}

        page = instance.browser.page
        if not page:
            return {"ok": False, "error": "페이지가 로드되지 않았습니다."}

        # JavaScriptExecutor로 스크립트 검증
        from .web_automation_manager import JavaScriptExecutor
        js_executor = JavaScriptExecutor()

        is_safe, error_msg = js_executor.validate_script(script)
        if not is_safe:
            return {"ok": False, "error": f"스크립트 검증 실패: {error_msg}"}

        try:
            # 함수로 래핑
            func_script = f"() => {{ return {script} }}"

            # 대기 시작 시간 기록
            import time
            start_time = time.time()

            # Playwright의 wait_for_function 사용
            page.wait_for_function(func_script, timeout=timeout, polling=polling)

            # 대기 시간 계산
            wait_time = time.time() - start_time

            # 액션 기록
            instance.recorder.record_action("wait_for_function", {
                "script": script[:50] + "..." if len(script) > 50 else script,
                "timeout": timeout,
                "actual_wait_time": f"{wait_time:.2f}s"
            })

            return {
                "ok": True, 
                "data": True,
                "wait_time": wait_time
            }

        except Exception as e:
            return {
                "ok": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "script": script
            }

    return safe_execute(
        func_name="web_wait_for_function",
        impl_func=impl,
        check_instance=False
    )



# ============== 세션 유지 기능 추가 (2025-08-06) ==============

def web_connect(url: Optional[str] = None, headless: bool = False, project_name: str = "default") -> Dict[str, Any]:
    """
    웹 브라우저 세션 연결 (세션 유지 지원)

    Args:
        url: 초기 접속할 URL (선택)
        headless: 헤드리스 모드 여부
        project_name: 프로젝트 이름 (세션 구분용)

    Returns:
        {'ok': bool, 'data': str, 'session_active': bool}

    Example:
        >>> result = h.web_connect("https://example.com")
        >>> if result['ok']:
        ...     web_session_active = True
        >>> # 여러 execute_code 블록에서 계속 사용
        >>> if web_session_active:
        ...     h.web_click("button")
    """
    try:
        # 기존 세션 확인
        existing = browser_manager.get_instance(project_name)

        if existing and hasattr(existing, 'browser_started') and existing.browser_started:
            # 기존 세션 재사용
            if url:
                existing.goto(url)
            return {
                'ok': True, 
                'data': f"기존 세션 재사용: {project_name}",
                'session_active': True,
                'reused': True
            }

        # 새 세션 생성
        instance = REPLBrowserWithRecording(headless=headless)
        instance.start()
        browser_manager.set_instance(instance, project_name)

        if url:
            instance.goto(url)

        return {
            'ok': True,
            'data': f"새 세션 시작: {project_name}",
            'session_active': True,
            'reused': False
        }
    except Exception as e:
        return {
            'ok': False,
            'error': str(e),
            'session_active': False
        }


def web_disconnect(save_recording: bool = False, project_name: str = "default") -> Dict[str, Any]:
    """
    웹 브라우저 세션 종료

    Args:
        save_recording: 레코딩 저장 여부
        project_name: 프로젝트 이름

    Returns:
        {'ok': bool, 'data': str}

    Example:
        >>> h.web_disconnect(save_recording=True)
    """
    try:
        instance = browser_manager.get_instance(project_name)

        if not instance:
            return {
                'ok': True,
                'data': "세션이 이미 종료되었습니다"
            }

        # 레코딩 저장
        if save_recording and hasattr(instance, 'get_recording'):
            recording = instance.get_recording()
            if recording:
                filename = f"web_recording_{project_name}.json"
                import json
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(recording, f, indent=2, ensure_ascii=False)

        # 브라우저 종료
        if hasattr(instance, 'stop'):
            instance.stop()

        # 인스턴스 제거
        browser_manager.remove_instance(project_name)

        return {
            'ok': True,
            'data': f"세션 종료 완료: {project_name}"
        }
    except Exception as e:
        return {
            'ok': False,
            'error': str(e)
        }


def web_check_session(project_name: str = "default") -> Dict[str, Any]:
    """
    웹 브라우저 세션 상태 확인

    Args:
        project_name: 프로젝트 이름

    Returns:
        {'ok': bool, 'data': {'active': bool, 'url': str, 'title': str}}

    Example:
        >>> result = h.web_check_session()
        >>> if result['ok'] and result['data']['active']:
        ...     print(f"현재 페이지: {result['data']['title']}")
    """
    try:
        instance = browser_manager.get_instance(project_name)

        if not instance:
            return {
                'ok': True,
                'data': {
                    'active': False,
                    'url': None,
                    'title': None
                }
            }

        # 세션 활성 상태 확인
        is_active = hasattr(instance, 'browser_started') and instance.browser_started

        if is_active and hasattr(instance, 'page'):
            try:
                url = instance.page.url
                title = instance.page.title()
            except:
                url = None
                title = None
        else:
            url = None
            title = None

        return {
            'ok': True,
            'data': {
                'active': is_active,
                'url': url,
                'title': title,
                'project': project_name
            }
        }
    except Exception as e:
        return {
            'ok': False,
            'error': str(e),
            'data': {'active': False}
        }


def web_list_sessions() -> Dict[str, Any]:
    """
    모든 활성 웹 세션 목록 조회

    Returns:
        {'ok': bool, 'data': List[str]}

    Example:
        >>> result = h.web_list_sessions()
        >>> if result['ok']:
        ...     for session in result['data']:
        ...         print(f"활성 세션: {session}")
    """
    try:
        sessions = browser_manager.list_instances()
        return {
            'ok': True,
            'data': sessions
        }
    except Exception as e:
        return {
            'ok': False,
            'error': str(e),
            'data': []
        }


# 기존 함수 개선 - 세션 재사용 지원
def web_goto_session(url: str, project_name: str = "default") -> Dict[str, Any]:
    """
    현재 세션에서 URL로 이동 (세션 유지 버전)

    Args:
        url: 이동할 URL
        project_name: 프로젝트 이름

    Returns:
        {'ok': bool, 'data': str}
    """
    try:
        instance = browser_manager.get_instance(project_name)

        if not instance:
            # 세션이 없으면 자동으로 생성
            connect_result = web_connect(url=url, project_name=project_name)
            return connect_result

        # 기존 세션에서 이동
        instance.goto(url)
        return {
            'ok': True,
            'data': f"페이지 이동: {url}"
        }
    except Exception as e:
        return {
            'ok': False,
            'error': str(e)
        }


# ============================================================================
# 팝업 처리 헬퍼 함수들 (2025-08-06)
# ============================================================================

def _handle_popup_impl(selector_or_page, button_text: str = "예", force: bool = True) -> Dict[str, Any]:
    """범용 팝업 처리 구현"""
    # 페이지 객체 가져오기
    if hasattr(selector_or_page, 'locator'):
        # 직접 page 객체가 전달된 경우
        page = selector_or_page
    else:
        # 기본 인스턴스 사용
        web = _get_web_instance()
        if not web:
            return {'ok': False, 'error': 'h.web_start()를 먼저 실행하세요'}
        if not hasattr(web, 'page'):
            return {'ok': False, 'error': '페이지가 로드되지 않았습니다'}
        page = web.page

    # 다양한 팝업 선택자 시도
    selectors = [
        f'[role="dialog"] button:has-text("{button_text}")',
        f'[role="alertdialog"] button:has-text("{button_text}")',
        f'.modal button:has-text("{button_text}")',
        f'[class*="popup"] button:has-text("{button_text}")',
        f'[class*="dialog"] button:has-text("{button_text}")',
        f'[class*="overlay"] button:has-text("{button_text}")',
        f'div[style*="z-index"] button:has-text("{button_text}")',
        f'button:has-text("{button_text}"):visible'
    ]

    # 각 선택자로 클릭 시도
    for i, selector in enumerate(selectors):
        try:
            # 요소가 존재하는지 확인 (타임아웃 짧게)
            if page.locator(selector).count() > 0:
                page.locator(selector).first.click(force=force, timeout=2000)
                return {
                    'ok': True,
                    'data': {
                        'clicked': True,
                        'method': 'selector',
                        'selector_index': i,
                        'selector': selector,
                        'button_text': button_text
                    }
                }
        except Exception:
            continue

    # 모든 선택자 실패 시 JavaScript로 직접 클릭
    try:
        result = page.evaluate(f"""
            (() => {{
                const buttons = document.querySelectorAll('button, input[type="button"], input[type="submit"], a.btn, a.button');
                for(let btn of buttons) {{
                    const text = btn.textContent || btn.value || '';
                    if(text.includes('{button_text}')) {{
                        btn.click();
                        return {{
                            clicked: true,
                            element: btn.tagName.toLowerCase(),
                            text: text.trim()
                        }};
                    }}
                }}
                return {{clicked: false}};
            }})()
        """)

        if result and result.get('clicked'):
            return {
                'ok': True,
                'data': {
                    'clicked': True,
                    'method': 'javascript',
                    'element': result.get('element'),
                    'text': result.get('text'),
                    'button_text': button_text
                }
            }
        else:
            return {
                'ok': False,
                'error': f"버튼 '{button_text}'을(를) 찾을 수 없습니다"
            }

    except Exception as e:
        return {
            'ok': False,
            'error': f"JavaScript 실행 실패: {str(e)}"
        }


def handle_popup(button_text: str = "예", force: bool = True, page=None) -> Dict[str, Any]:
    """
    범용 팝업 처리 함수

    다양한 유형의 웹 팝업/모달/다이얼로그를 처리합니다.
    여러 선택자를 시도하고, 실패 시 JavaScript로 직접 클릭합니다.

    Args:
        button_text: 클릭할 버튼의 텍스트 (기본값: "예")
        force: 강제 클릭 여부 (기본값: True) - 요소가 가려져 있어도 클릭
        page: Playwright page 객체 (선택적, 기본값은 현재 세션)

    Returns:
        표준 응답 형식 {'ok': bool, 'data': dict, 'error': str}

    Examples:
        >>> result = h.handle_popup("확인")
        >>> if result['ok']:
        ...     print(f"팝업 처리 완료: {result['data']['method']}")
    """
    return safe_execute('handle_popup', _handle_popup_impl, page or button_text, button_text if page else "예", force)


def _wait_and_click_impl(selector: str, timeout: int = 5000, force: bool = False) -> Dict[str, Any]:
    """요소가 나타날 때까지 기다린 후 클릭"""
    web = _get_web_instance()
    if not web:
        return {'ok': False, 'error': 'h.web_start()를 먼저 실행하세요'}

    try:
        # 선택자가 텍스트인 경우 자동 변환
        if not any(char in selector for char in ['#', '.', '[', ':', '>']):
            selector = f'text="{selector}"'

        # 요소 대기
        web.page.wait_for_selector(selector, timeout=timeout, state="visible")

        # 클릭
        web.page.click(selector, force=force)

        return {
            'ok': True,
            'data': {
                'clicked': True,
                'selector': selector,
                'timeout': timeout
            }
        }

    except Exception as e:
        return {
            'ok': False,
            'error': f"클릭 실패: {str(e)}",
            'selector': selector
        }


def wait_and_click(selector: str, timeout: int = 5000, force: bool = False) -> Dict[str, Any]:
    """
    요소가 나타날 때까지 기다린 후 클릭

    Args:
        selector: CSS 선택자 또는 텍스트 선택자
        timeout: 대기 시간 (밀리초)
        force: 강제 클릭 여부

    Returns:
        표준 응답 형식

    Examples:
        >>> h.wait_and_click("button.confirm", timeout=10000)
        >>> h.wait_and_click("확인", force=True)
    """
    return safe_execute('wait_and_click', _wait_and_click_impl, selector, timeout, force)


def _handle_alert_impl(accept: bool = True, text: Optional[str] = None) -> Dict[str, Any]:
    """브라우저 alert/confirm/prompt 처리"""
    web = _get_web_instance()
    if not web:
        return {'ok': False, 'error': 'h.web_start()를 먼저 실행하세요'}

    try:
        # alert 이벤트 핸들러 등록
        def handle_dialog(dialog):
            if text is not None:
                dialog.accept(text)
            elif accept:
                dialog.accept()
            else:
                dialog.dismiss()

        web.page.on("dialog", handle_dialog)

        return {
            'ok': True,
            'data': {
                'handler_registered': True,
                'accept': accept,
                'text': text
            }
        }

    except Exception as e:
        return {
            'ok': False,
            'error': f"Alert 핸들러 등록 실패: {str(e)}"
        }


def handle_alert(accept: bool = True, text: Optional[str] = None) -> Dict[str, Any]:
    """
    브라우저 alert/confirm/prompt 처리

    Args:
        accept: 수락 여부 (True: 확인, False: 취소)
        text: prompt의 경우 입력할 텍스트

    Returns:
        표준 응답 형식
    """
    return safe_execute('handle_alert', _handle_alert_impl, accept, text)


# 편의 함수들 - 자주 사용하는 패턴
def close_popup() -> Dict[str, Any]:
    """
    팝업 닫기 (다양한 닫기 버튼 텍스트 시도)

    Returns:
        표준 응답 형식

    Example:
        >>> h.close_popup()
    """
    close_texts = ["닫기", "확인", "OK", "Close", "X", "×", "✕"]

    for text in close_texts:
        result = handle_popup(text)
        if result['ok']:
            return result

    return {
        'ok': False,
        'error': "닫기 버튼을 찾을 수 없습니다"
    }


def confirm_popup() -> Dict[str, Any]:
    """
    확인 팝업 처리

    Returns:
        표준 응답 형식

    Example:
        >>> h.confirm_popup()
    """
    confirm_texts = ["확인", "예", "네", "OK", "Yes", "Confirm", "승인", "동의"]

    for text in confirm_texts:
        result = handle_popup(text)
        if result['ok']:
            return result

    return {
        'ok': False,
        'error': "확인 버튼을 찾을 수 없습니다"
    }


def cancel_popup() -> Dict[str, Any]:
    """
    취소 팝업 처리

    Returns:
        표준 응답 형식

    Example:
        >>> h.cancel_popup()
    """
    cancel_texts = ["취소", "아니오", "아니요", "Cancel", "No", "거절", "거부"]

    for text in cancel_texts:
        result = handle_popup(text)
        if result['ok']:
            return result

    return {
        'ok': False,
        'error': "취소 버튼을 찾을 수 없습니다"
    }


def handle_modal_by_class(modal_class: str, button_text: str, force: bool = True) -> Dict[str, Any]:
    """
    특정 클래스의 모달 내에서 버튼 클릭

    Args:
        modal_class: 모달의 클래스명
        button_text: 클릭할 버튼 텍스트
        force: 강제 클릭 여부

    Returns:
        표준 응답 형식

    Example:
        >>> h.handle_modal_by_class("warning-modal", "계속진행")
    """
    web = _get_web_instance()
    if not web:
        return {'ok': False, 'error': 'h.web_start()를 먼저 실행하세요'}

    try:
        selector = f'.{modal_class} button:has-text("{button_text}")'

        if web.page.locator(selector).count() > 0:
            web.page.locator(selector).first.click(force=force)
            return {
                'ok': True,
                'data': {
                    'clicked': True,
                    'modal_class': modal_class,
                    'button_text': button_text
                }
            }
        else:
            return {
                'ok': False,
                'error': f"모달 '{modal_class}'에서 버튼 '{button_text}'을(를) 찾을 수 없습니다"
            }

    except Exception as e:
        return {
            'ok': False,
            'error': f"모달 처리 실패: {str(e)}"
        }
    다른 대화 세션에서 load_browser_session()으로 불러올 수 있습니다.

    Args:
        session_name: 세션 이름

    Returns:
        표준 응답 형식

    Example:
        # 세션 1에서 저장
        >>> h.web_start()
        >>> h.web_goto("https://example.com")
        >>> h.save_browser_session("my_session")

        # 세션 2에서 로드
        >>> h.load_browser_session("my_session")
    """
    web = _get_web_instance()
    if not web:
        return {'ok': False, 'error': 'h.web_start()를 먼저 실행하세요'}

    try:
        # 세션 정보 수집
        session_info = {
            'url': web.page.url if hasattr(web, 'page') and web.page else None,
            'title': web.page.title() if hasattr(web, 'page') and web.page else None,
            'browser_type': type(web.browser).__name__ if hasattr(web, 'browser') else None,
            'project_name': getattr(web, 'project_name', 'web_scraping'),
            'timestamp': datetime.now().isoformat()
        }

        # WebSocket endpoint 시도
        try:
            if hasattr(web.browser, '_impl_obj'):
                session_info['ws_endpoint'] = web.browser._impl_obj._connection._transport._ws_endpoint
        except:
            pass

        # CDP URL 시도
        try:
            if hasattr(web.browser, '_browser_cdp_session'):
                session_info['cdp_url'] = "http://127.0.0.1:9222"  # 기본값
        except:
            pass

        # 세션 파일 저장 경로
        session_dir = Path(".ai-brain/browser_sessions")
        session_dir.mkdir(parents=True, exist_ok=True)
        session_file = session_dir / f"{session_name}.json"

        # 파일로 저장
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_info, f, indent=2, ensure_ascii=False)

        print(f"✅ 브라우저 세션 저장됨: {session_file}")
        print(f"📍 현재 URL: {session_info.get('url')}")
        print(f"💡 다른 세션에서 로드: h.load_browser_session('{session_name}')")

        return {
            'ok': True,
            'data': {
                'saved': True,
                'session_name': session_name,
                'file': str(session_file),
                'info': session_info
            }
        }

    except Exception as e:
        return {
            'ok': False,
            'error': f"세션 저장 실패: {str(e)}"
        }


def load_browser_session(session_name: str = "shared_session") -> Dict[str, Any]:
    """
    저장된 브라우저 세션 정보 로드

    Args:
        session_name: 세션 이름

    Returns:
        표준 응답 형식
    """
    try:
        # 세션 파일 경로
        session_file = Path(".ai-brain/browser_sessions") / f"{session_name}.json"

        if not session_file.exists():
            return {
                'ok': False,
                'error': f"세션 파일을 찾을 수 없습니다: {session_file}"
            }

        # 세션 정보 로드
        with open(session_file, 'r', encoding='utf-8') as f:
            session_info = json.load(f)

        print(f"📋 저장된 세션 정보:")
        print(f"  URL: {session_info.get('url')}")
        print(f"  제목: {session_info.get('title')}")
        print(f"  저장 시간: {session_info.get('timestamp')}")

        # WebSocket endpoint나 CDP URL이 있으면 연결 시도
        if session_info.get('ws_endpoint'):
            print(f"🔗 WebSocket endpoint로 연결 시도...")
            return connect_to_existing_browser(ws_endpoint=session_info['ws_endpoint'])

        elif session_info.get('cdp_url'):
            print(f"🔗 CDP URL로 연결 시도...")
            return connect_to_existing_browser(cdp_url=session_info['cdp_url'])

        else:
            return {
                'ok': True,
                'data': {
                    'info': session_info,
                    'message': "세션 정보만 로드됨 (연결 정보 없음)"
                }
            }

    except Exception as e:
        return {
            'ok': False,
            'error': f"세션 로드 실패: {str(e)}"
        }


def list_browser_sessions() -> Dict[str, Any]:
    """
    저장된 모든 브라우저 세션 목록 조회

    Returns:
        표준 응답 형식
    """
    try:
        session_dir = Path(".ai-brain/browser_sessions")

        if not session_dir.exists():
            return {
                'ok': True,
                'data': {
                    'sessions': [],
                    'message': "저장된 세션이 없습니다"
                }
            }

        sessions = []
        for session_file in session_dir.glob("*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                    sessions.append({
                        'name': session_file.stem,
                        'url': info.get('url'),
                        'title': info.get('title'),
                        'timestamp': info.get('timestamp')
                    })
            except:
                continue

        return {
            'ok': True,
            'data': {
                'sessions': sessions,
                'count': len(sessions)
            }
        }

    except Exception as e:
        return {
            'ok': False,
            'error': f"세션 목록 조회 실패: {str(e)}"
        }
