"""
웹 자동화 레코딩 헬퍼 함수들
REPLBrowserWithRecording을 사용하여 REPL 환경에서 쉽게 웹 자동화를 수행합니다.
from .web_automation_smart_wait import SmartWaitManager

작성일: 2025-01-27
"""
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
