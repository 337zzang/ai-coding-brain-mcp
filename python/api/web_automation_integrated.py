"""
웹 자동화 통합 모듈
REPLBrowser와 ActionRecorder를 통합하여 REPL 환경에서 
브라우저를 제어하면서 모든 액션을 기록하고 스크래핑 코드를 자동 생성합니다.

작성일: 2025-01-27
"""
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime
from web_automation_errors import with_error_handling
from web_automation_extraction import AdvancedExtractionManager

# 로컬 임포트
from python.api.web_automation_repl import REPLBrowser
from python.api.web_automation_recorder import ActionRecorder
from python.api.web_automation_extraction import AdvancedExtractionManager


class REPLBrowserWithRecording:
    """
    REPLBrowser와 ActionRecorder를 통합한 클래스

    특징:
    - 브라우저 제어와 동시에 모든 액션 자동 기록
    - 스레드 안전성 보장
    - 데이터 추출 전용 메서드 제공
    - 스크래핑 코드 자동 생성
    """

    def __init__(self, headless: bool = False, project_name: str = "web_scraping"):
        """
        통합 브라우저 초기화

        Args:
            headless: 헤드리스 모드 여부
            project_name: 프로젝트 이름 (액션 기록용)
        """
        self.browser = REPLBrowser()
        self.recorder = ActionRecorder(project_name)
        self._lock = threading.Lock()  # 스레드 안전성
        self.browser_started = False
        self.extracted_data = {}  # 추출된 데이터 저장
        self.extraction_manager = None  # 초기화는 브라우저 시작 후

    def __enter__(self):
        """컨텍스트 매니저 진입"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.stop()

    @with_error_handling('start', check_instance=False)
    def start(self) -> Dict[str, Any]:
        """
        브라우저 시작

        Returns:
            실행 결과 딕셔너리
        """
        with self._lock:
            result = self.browser.start()

            # REPLBrowser 반환값 형식을 통합 형식으로 변환
            if result.get('status') == 'started':
                self.browser_started = True
                # AdvancedExtractionManager 초기화
                if hasattr(self.browser, 'page') and self.browser.page:
                    self.extraction_manager = AdvancedExtractionManager(self.browser.page)
                self.recorder.record_action('browser_start', True, 
                                          timestamp=datetime.now().isoformat())
                return {'ok': True, 'message': result.get('message', '브라우저 시작 완료')}
            else:
                return {'ok': False, 'error': result.get('message', '알 수 없는 오류')}

    @with_error_handling('stop', check_instance=False)
    def stop(self) -> Dict[str, Any]:
        """
        브라우저 종료

        Returns:
            실행 결과 딕셔너리
        """
        with self._lock:
            if self.browser_started:
                self.recorder.record_action('browser_stop', True,
                                          timestamp=datetime.now().isoformat())
                result = self.browser.stop()
                self.browser_started = False
                return result
            return {'ok': False, 'error': '브라우저가 시작되지 않았습니다'}

    @with_error_handling('goto')
    def goto(self, url: str, wait_until: str = 'load') -> Dict[str, Any]:
        """
        페이지 이동 + 액션 기록

        Args:
            url: 이동할 URL
            wait_until: 대기 조건 ('load', 'domcontentloaded', 'networkidle')

        Returns:
            실행 결과 딕셔너리
        """
        with self._lock:
            result = self.browser.goto(url, wait_until)
            if result.get('ok'):
                self.recorder.record_action('navigate', True, 
                                          url=url, 
                                          wait_until=wait_until)
            else:
                self.recorder.record_action('navigate', False, 
                                          url=url, 
                                          error=result.get('error'))
            return result

    @with_error_handling('click')
    def click(self, selector: str) -> Dict[str, Any]:
        """
        요소 클릭 + 액션 기록

        Args:
            selector: CSS 선택자

        Returns:
            실행 결과 딕셔너리
        """
        with self._lock:
            result = self.browser.click(selector)
            if result.get('ok'):
                self.recorder.record_action('click', True, selector=selector)
            else:
                self.recorder.record_action('click', False, 
                                          selector=selector,
                                          error=result.get('error'))
            return result

    @with_error_handling('type')
    def type(self, selector: str, text: str) -> Dict[str, Any]:
        """
        텍스트 입력 + 액션 기록

        Args:
            selector: CSS 선택자
            text: 입력할 텍스트

        Returns:
            실행 결과 딕셔너리
        """
        with self._lock:
            result = self.browser.type(selector, text)
            if result.get('ok'):
                self.recorder.record_action('input', True, 
                                          selector=selector,
                                          text=text)
            else:
                self.recorder.record_action('input', False,
                                          selector=selector,
                                          text=text,
                                          error=result.get('error'))
            return result


    @with_error_handling('extract')
    def extract(self, selector: str, name: Optional[str] = None, 
                extract_type: str = 'text') -> Dict[str, Any]:
        """
        데이터 추출 + 액션 기록

        Args:
            selector: CSS 선택자
            name: 데이터 이름 (자동 생성 가능)
            extract_type: 추출 타입 ('text', 'value', 'href', 'src', 'html')

        Returns:
            {'ok': bool, 'data': 추출된 데이터, 'name': 데이터 이름}
        """
        with self._lock:
            # JavaScript 코드 생성
            js_code = self._generate_extract_js(selector, extract_type)
            result = self.browser.eval(js_code)

            if result.get('status') == 'success':
                data = result.get('result', '')

                # 자동 이름 생성
                if not name:
                    name = f"data_{len(self.extracted_data)}"

                # 추출된 데이터 저장
                self.extracted_data[name] = data

                # 액션 기록
                self.recorder.record_action('extract', True,
                                          selector=selector,
                                          name=name,
                                          extract_type=extract_type,
                                          sample=str(data)[:100])

                return {'ok': True, 'data': data, 'name': name}
            else:
                self.recorder.record_action('extract', False,
                                          selector=selector,
                                          error=result.get('message', 'Unknown error'))
                return {'ok': False, 'error': result.get('message', 'Unknown error')}

    @with_error_handling('extract_table')
    def extract_table(self, table_selector: str, name: Optional[str] = None) -> Dict[str, Any]:
        """
        테이블 데이터 추출

        Args:
            table_selector: 테이블 CSS 선택자
            name: 데이터 이름

        Returns:
            {'ok': bool, 'data': {'headers': [...], 'rows': [[...], ...]}, 'name': str}
        """
        with self._lock:
            js_code = f"""
            (() => {{
                const table = document.querySelector('{table_selector}');
                if (!table) return null;

                // 헤더 추출
                const headers = Array.from(table.querySelectorAll('th')).map(th => th.innerText.trim());

                // 데이터 행 추출
                const rows = Array.from(table.querySelectorAll('tbody tr')).map(tr => 
                    Array.from(tr.querySelectorAll('td')).map(td => td.innerText.trim())
                );

                return {{headers, rows}};
            }})()
            """

            result = self.browser.eval(js_code)

            if result.get('ok'):
                data = result.get('data')
                if not name:
                    name = f"table_{len(self.extracted_data)}"

                self.extracted_data[name] = data

                self.recorder.record_action('extract_table', True,
                                          selector=table_selector,
                                          name=name,
                                          rows_count=len(data['rows']) if data else 0)

                return {'ok': True, 'data': data, 'name': name}
            else:
                return result


    def extract_batch(self, configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """배치 추출 - eval 기반 구현"""
        with self._lock:
            try:
                # JavaScript 코드 생성
                js_code = """
                (() => {
                    const results = {};
                    const configs = """ + str(configs) + """;

                    configs.forEach(config => {
                        try {
                            const element = document.querySelector(config.selector);
                            if (element) {
                                let value;
                                switch(config.type) {
                                    case 'text':
                                        value = element.textContent;
                                        break;
                                    case 'value':
                                        value = element.value;
                                        break;
                                    case 'attr':
                                        value = element.getAttribute(config.attr);
                                        break;
                                    case 'href':
                                        value = element.href;
                                        break;
                                    case 'src':
                                        value = element.src;
                                        break;
                                    default:
                                        value = element.textContent;
                                }
                                results[config.name] = value;
                            } else if (config.default !== undefined) {
                                results[config.name] = config.default;
                            }
                        } catch (e) {
                            console.error('Extract error:', e);
                        }
                    });

                    return results;
                })()
                """

                # 실행
                eval_result = self.browser.eval(js_code)

                if eval_result.get('status') == 'success':
                    data = eval_result.get('result', {})
                    result = {'ok': True, 'data': data}
                else:
                    result = {'ok': False, 'error': 'Eval failed', 'details': eval_result}

                # 액션 기록
                self.recorder.record_action('extract_batch', result.get('ok', False),
                                          configs_count=len(configs),
                                          results_count=len(result.get('data', {})))

                return result

            except Exception as e:
                return {'ok': False, 'error': str(e)}

    def extract_attributes(self, selector: str, attributes: List[str]) -> Dict[str, Any]:
        """속성 추출 - eval 기반 구현"""
        with self._lock:
            try:
                js_code = f"""
                (() => {{
                    const elements = document.querySelectorAll('{selector}');
                    const results = [];
                    const attrs = {attributes};

                    elements.forEach(el => {{
                        const item = {{}};
                        attrs.forEach(attr => {{
                            item[attr] = el.getAttribute(attr);
                        }});
                        results.push(item);
                    }});

                    return results;
                }})()
                """

                eval_result = self.browser.eval(js_code)

                if eval_result.get('status') == 'success':
                    data = eval_result.get('result', [])
                    result = {'ok': True, 'data': data}
                else:
                    result = {'ok': False, 'error': 'Eval failed'}

                self.recorder.record_action('extract_attributes', result.get('ok', False),
                                          selector=selector,
                                          attributes_count=len(attributes))

                return result

            except Exception as e:
                return {'ok': False, 'error': str(e)}

    def extract_form(self, form_selector: str) -> Dict[str, Any]:
        """폼 추출 - AdvancedExtractionManager 사용"""
        with self._lock:
            result = self.extraction_manager.extract_form(form_selector)

            # 액션 기록
            self.recorder.record_action('extract_form', result.get('ok', False),
                                      selector=form_selector,
                                      fields_count=len(result.get('data', {})))

            return result

    def _generate_extract_js(self, selector: str, extract_type: str) -> str:
        """JavaScript 코드 생성 헬퍼"""
        if extract_type == 'text':
            return f"document.querySelector('{selector}')?.innerText?.trim() || ''"
        elif extract_type == 'value':
            return f"document.querySelector('{selector}')?.value || ''"
        elif extract_type == 'href':
            return f"document.querySelector('{selector}')?.href || ''"
        elif extract_type == 'src':
            return f"document.querySelector('{selector}')?.src || ''"
        elif extract_type == 'html':
            return f"document.querySelector('{selector}')?.innerHTML || ''"
        else:
            return f"document.querySelector('{selector}')?.innerText?.trim() || ''"

    @with_error_handling('screenshot')
    def screenshot(self, path: str = None) -> Dict[str, Any]:
        """스크린샷 캡처"""
        with self._lock:
            if not path:
                path = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

            result = self.browser.screenshot(path)
            if result.get('ok'):
                self.recorder.record_action('screenshot', True, path=path)
            return result

    @with_error_handling('wait')
    def wait(self, duration_or_timeout: float = 1, wait_for: str = None, **kwargs) -> Dict[str, Any]:
        """
        단순 시간 대기 또는 지능형 스마트 대기를 수행합니다.

        Args:
            duration_or_timeout: 대기 시간(초) 또는 스마트 대기의 타임아웃
            wait_for: 스마트 대기 타입 ("element", "network_idle", "js")
            **kwargs: 스마트 대기 옵션
        """
        with self._lock:
            # 하위 호환성: wait_for가 없으면 기존 방식
            if wait_for is None:
                result = self.browser.wait(duration_or_timeout)
                if result.get('ok'):
                    self.recorder.record_action('wait', True, seconds=duration_or_timeout)
                return result

            # 스마트 대기 사용
            try:
                # SmartWaitManager 생성
                wait_manager = SmartWaitManager(self.browser.page, default_timeout=duration_or_timeout)

                # 디버그 모드 확인
                if hasattr(self, 'debug') and self.debug:
                    wait_manager.enable_debug(True)

                # wait_for 타입에 따라 처리
                if wait_for == "element":
                    selector = kwargs.get("selector", "")
                    condition = kwargs.get("condition", "visible")
                    result = wait_manager.wait_for_element(selector, condition, duration_or_timeout)

                elif wait_for == "network_idle":
                    idle_time = kwargs.get("idle_time", 0.5)
                    result = wait_manager.wait_for_network_idle(idle_time, duration_or_timeout)

                elif wait_for == "js":
                    script = kwargs.get("script", "")
                    value = kwargs.get("value")
                    result = wait_manager.wait_for_js_complete(script, value, duration_or_timeout)

                else:
                    result = {"ok": False, "error": f"알 수 없는 대기 타입: {wait_for}"}

                # 레코더에 기록
                if result.get('ok'):
                    wait_info = {
                        "wait_for": wait_for,
                        "timeout": duration_or_timeout,
                        "wait_time": result.get("data", {}).get("wait_time", 0)
                    }
                    wait_info.update(kwargs)
                    self.recorder.record_action('wait_smart', True, **wait_info)

                return result

            except Exception as e:
                return {"ok": False, "error": f"스마트 대기 실행 중 오류: {str(e)}"}

    def eval(self, script: str) -> Dict[str, Any]:
        """JavaScript 실행"""
        with self._lock:
            return self.browser.eval(script)

    def get_content(self) -> Dict[str, Any]:
        """페이지 HTML 가져오기"""
        with self._lock:
            return self.browser.get_content()

    def generate_script(self, output_file: str = None) -> Dict[str, Any]:
        """
        기록된 액션으로 스크래핑 스크립트 생성

        Args:
            output_file: 출력 파일 경로

        Returns:
            생성 결과
        """
        if not output_file:
            output_file = f"generated_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"

        # 커스텀 스크립트 생성 로직으로 개선
        return self._generate_improved_script(output_file)

    def _generate_improved_script(self, output_file: str) -> Dict[str, Any]:
        """개선된 스크립트 생성"""
        try:
            # 액션 분석
            urls = [a['params']['url'] for a in self.recorder.actions 
                   if a['type'] == 'navigate']
            selectors = {}

            for action in self.recorder.actions:
                if 'selector' in action['params']:
                    sel = action['params']['selector']
                    name = action['params'].get('name', f"selector_{len(selectors)}")
                    selectors[name] = sel

            # 스크립트 생성 - 문자열 연결 방식 사용
            script_lines = [
                '#!/usr/bin/env python3',
                '"""',
                '자동 생성된 웹 스크래핑 스크립트',
                f'생성일: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                f'URL: {urls[0] if urls else "N/A"}',
                '"""',
                '',
                '# === 설정 ===',
                f'URL = "{urls[0] if urls else ""}"',
                'SELECTORS = {'
            ]

            # 선택자 추가
            for k, v in selectors.items():
                script_lines.append(f'    "{k}": "{v}",')
            script_lines.append('}')
            script_lines.append('')

            # 메인 함수
            script_lines.extend([
                '# === 메인 함수 ===',
                'def main():',
                '    from python.api.web_automation_repl import REPLBrowser',
                '    ',
                '    browser = REPLBrowser()',
                '    extracted_data = {}',
                '    ',
                '    try:',
                '        # 브라우저 시작',
                '        print("🌐 브라우저 시작...")',
                '        browser.start()',
                '        '
            ])

            # 액션별 코드 생성
            for action in self.recorder.actions:
                if action['type'] == 'navigate':
                    script_lines.extend([
                        '        # 페이지 이동',
                        f'        print("📍 이동: {action["params"]["url"]}")',
                        f'        browser.goto("{action["params"]["url"]}")',
                        '        '
                    ])
                elif action['type'] == 'click':
                    script_lines.extend([
                        '        # 클릭',
                        f'        browser.click("{action["params"]["selector"]}")',
                        '        '
                    ])
                elif action['type'] == 'input':
                    script_lines.extend([
                        '        # 텍스트 입력',
                        f'        browser.type("{action["params"]["selector"]}", "{action["params"]["text"]}")',
                        '        '
                    ])
                elif action['type'] == 'extract':
                    name = action['params'].get('name', 'unknown')
                    selector = action['params']['selector']
                    script_lines.extend([
                        f'        # 데이터 추출: {name}',
                        f'        result = browser.eval("document.querySelector(\'{selector}\')?.innerText?.trim() || \'\'")',
                        '        if result.get("ok"):',
                        f'            extracted_data["{name}"] = result.get("data")',
                        f'            print(f"✅ {name}: {{result.get(\'data\')[:50]}}...")',
                        '        '
                    ])

            script_lines.extend([
                '        return extracted_data',
                '        ',
                '    except Exception as e:',
                '        print(f"❌ 오류 발생: {e}")',
                '        return None',
                '    finally:',
                '        browser.stop()',
                '        print("✅ 브라우저 종료")',
                '',
                'if __name__ == "__main__":',
                '    data = main()',
                '    if data:',
                '        print(f"\n📊 추출 완료: {len(data)}개 데이터")',
                '        for key, value in data.items():',
                '            print(f"  - {key}: {str(value)[:50]}...")'
            ])

            # 스크립트 조합
            script = '\n'.join(script_lines)

            # 파일 저장
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(script)
                return {
                    'ok': True,
                    'path': output_file,
                    'size': len(script),
                    'actions_count': len(self.recorder.actions),
                    'message': f'스크립트가 생성되었습니다: {output_file}'
                }
            except Exception as write_error:
                return {'ok': False, 'error': str(write_error)}

        except Exception as e:
            return {'ok': False, 'error': str(e)}
    def get_extracted_data(self) -> Dict[str, Any]:
        """추출된 모든 데이터 반환"""
        return self.extracted_data.copy()
