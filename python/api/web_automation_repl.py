"""
REPL용 Playwright 웹 자동화 모듈
JSON-REPL, IPython 등에서 브라우저를 계속 열어두고 제어 가능

사용법:
    from python.api.web_automation_repl import REPLBrowser
from .web_automation_errors import with_error_handling

    browser = REPLBrowser()
    browser.start()
    browser.goto("https://example.com")
    browser.click("button")
    browser.stop()
"""

import threading
import queue
import time
from typing import Dict, Any, Optional
from playwright.sync_api import sync_playwright
import logging

logger = logging.getLogger(__name__)


class REPLBrowser:
    """REPL 환경에서 사용하는 스레드 기반 브라우저 제어 클래스"""

    def __init__(self):
        self.command_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.thread: Optional[threading.Thread] = None
        self.running = False

    def _browser_thread(self):
        """브라우저 실행 스레드"""
        try:
            with sync_playwright() as p:
                # 브라우저 시작
                browser = p.chromium.launch(
                    headless=False,
                    args=['--disable-blink-features=AutomationControlled']
                )
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = context.new_page()

    def _process_command(self, page, cmd):
            """명령어 처리"""
            cmd_type = cmd.get("type")

            # 기본 명령어들
            if cmd_type == "goto":
                page.goto(cmd.get("url"))
                return {"status": "success"}

            elif cmd_type == "click":
                page.click(cmd.get("selector"))
                return {"status": "success"}

            elif cmd_type == "type":
                page.type(cmd.get("selector"), cmd.get("text"))
                return {"status": "success"}

            elif cmd_type == "wait":
                page.wait_for_timeout(cmd.get("timeout", 1000))
                return {"status": "success"}

            # SmartWaitManager 명령어
            elif cmd_type == "smart_wait":
                if not hasattr(self, 'smart_wait_manager') or self.smart_wait_manager is None:
                    return {"status": "error", "message": "SmartWaitManager not initialized"}

                wait_type = cmd.get("wait_type", "element")
                options = cmd.get("options", {})

                try:
                    if wait_type == "element":
                        result = self.smart_wait_manager.wait_for_element(
                            options.get("selector"),
                            options.get("state", "visible"),
                            options.get("timeout", 30000)
                        )
                    elif wait_type == "network_idle":
                        result = self.smart_wait_manager.wait_for_network_idle(
                            options.get("timeout", 30000)
                        )
                    elif wait_type == "js_complete":
                        result = self.smart_wait_manager.wait_for_js_complete(
                            options.get("condition"),
                            options.get("timeout", 30000)
                        )
                    else:
                        return {"status": "error", "message": f"Unknown wait type: {wait_type}"}

                    return {"status": "success", "data": result}
                except Exception as e:
                    return {"status": "error", "message": str(e)}

            # AdvancedExtractionManager 명령어
            elif cmd_type == "extract_batch":
                if not hasattr(self, 'extraction_manager') or self.extraction_manager is None:
                    return {"status": "error", "message": "ExtractionManager not initialized"}

                try:
                    configs = cmd.get("configs", [])
                    result = self.extraction_manager.extract_batch(configs)
                    return {"status": "success", "data": result}
                except Exception as e:
                    return {"status": "error", "message": str(e), "data": []}

            elif cmd_type == "extract_attributes":
                if not hasattr(self, 'extraction_manager') or self.extraction_manager is None:
                    return {"status": "error", "message": "ExtractionManager not initialized"}

                try:
                    selector = cmd.get("selector")
                    attributes = cmd.get("attributes", [])
                    result = self.extraction_manager.extract_attributes(selector, attributes)
                    return {"status": "success", "data": result}
                except Exception as e:
                    return {"status": "error", "message": str(e), "data": []}

            elif cmd_type == "extract_form":
                if not hasattr(self, 'extraction_manager') or self.extraction_manager is None:
                    return {"status": "error", "message": "ExtractionManager not initialized"}

                try:
                    form_selector = cmd.get("form_selector", "form")
                    result = self.extraction_manager.extract_form(form_selector)
                    return {"status": "success", "data": result}
                except Exception as e:
                    return {"status": "error", "message": str(e), "data": {}}

            # eval 폴백 (기존 동작 유지)
            elif "eval" in cmd:
                try:
                    eval(cmd["eval"])
                    return {"status": "success"}
                except Exception as e:
                    return {"status": "error", "message": str(e)}

            else:
                return {"status": "error", "message": f"Unknown command type: {cmd_type}"}
# Manager 초기화 (page 생성 후)
                try:
                    # SmartWaitManager 초기화
                    from python.api.web_automation_smart_wait import SmartWaitManager
                    self.smart_wait_manager = SmartWaitManager(page)
                    self.result_queue.put(("log", "SmartWaitManager 초기화 완료"))
                except Exception as e:
                    self.result_queue.put(("log", f"SmartWaitManager 초기화 실패: {str(e)}"))
                    self.smart_wait_manager = None

                try:
                    # AdvancedExtractionManager 초기화
                    from python.api.web_automation_extraction import AdvancedExtractionManager
                    self.extraction_manager = AdvancedExtractionManager(page)
                    self.result_queue.put(("log", "AdvancedExtractionManager 초기화 완료"))
                except Exception as e:
                    self.result_queue.put(("log", f"AdvancedExtractionManager 초기화 실패: {str(e)}"))
                    self.extraction_manager = None

                self.result_queue.put({
                    "status": "started",
                    "message": "브라우저 시작 완료"
                })

                # 명령 처리 루프
                while self.running:
                    try:
                        cmd = self.command_queue.get(timeout=0.1)
                        result = self._process_command(page, cmd)
                        self.result_queue.put(result)

                    except queue.Empty:
                        continue
                    except Exception as e:
                        self.result_queue.put({
                            "status": "error",
                            "message": f"명령 처리 오류: {str(e)}"
                        })

                # 정리
                context.close()
                browser.close()

        except Exception as e:
            self.result_queue.put({
                "status": "error",
                "message": f"브라우저 스레드 오류: {str(e)}"
            })

    def _process_command(self, page, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """명령 처리"""
        action = cmd.get("action")

        if action == "goto":
            page.goto(cmd["url"], wait_until=cmd.get("wait_until", "networkidle"))
            return {
                "status": "success",
                "action": "goto",
                "title": page.title(),
                "url": page.url
            }

        elif action == "click":
            page.click(cmd["selector"])
            return {
                "status": "success",
                "action": "click",
                "selector": cmd["selector"]
            }

        elif action == "type":
            page.type(cmd["selector"], cmd["text"])
            return {
                "status": "success",
                "action": "type",
                "selector": cmd["selector"]
            }

        elif action == "screenshot":
            path = cmd.get("path", f"screenshot_{int(time.time())}.png")
            page.screenshot(path=path)
            return {
                "status": "success",
                "action": "screenshot",
                "path": path
            }

        elif action == "wait":
            time.sleep(cmd.get("seconds", 1))
            return {
                "status": "success",
                "action": "wait",
                "seconds": cmd.get("seconds", 1)
            }

        elif action == "eval":
            result = page.evaluate(cmd["script"])
            return {
                "status": "success",
                "action": "eval",
                "result": result
            }

        elif action == "get_content":
            content = page.content()
            return {
                "status": "success",
                "action": "get_content",
                "content_length": len(content),
                "content": content[:1000] + "..." if len(content) > 1000 else content
            }

        elif action == "stop":
            self.running = False
            return {"status": "stopped", "message": "브라우저 종료 중"}

        else:
            return {
                "status": "error",
                "message": f"알 수 없는 액션: {action}"
            }

    def start(self) -> Dict[str, Any]:
        """브라우저 시작"""
        if self.thread and self.thread.is_alive():
            return {"status": "error", "message": "브라우저가 이미 실행 중입니다"}

        self.running = True
        self.thread = threading.Thread(target=self._browser_thread, daemon=True)
        self.thread.start()

        # 시작 확인
        try:
            result = self.result_queue.get(timeout=10)
            logger.info("브라우저 시작 성공")
            return result
        except queue.Empty:
            self.running = False
            return {"status": "error", "message": "브라우저 시작 시간 초과"}

    def _send_command(self, command: Dict[str, Any], timeout: float = 10) -> Dict[str, Any]:
        """명령 전송 및 결과 대기"""
        if not self.running or not self.thread or not self.thread.is_alive():
            return {"status": "error", "message": "브라우저가 실행 중이 아닙니다"}

        self.command_queue.put(command)

        try:
            return self.result_queue.get(timeout=timeout)
        except queue.Empty:
            return {"status": "error", "message": "응답 시간 초과"}

    # 사용자 메서드들
    def goto(self, url: str, wait_until: str = "networkidle") -> Dict[str, Any]:
        """페이지 이동"""
        return self._send_command({
            "action": "goto",
            "url": url,
            "wait_until": wait_until
        })

    def click(self, selector: str) -> Dict[str, Any]:
        """요소 클릭"""
        return self._send_command({"action": "click", "selector": selector})

    def type(self, selector: str, text: str) -> Dict[str, Any]:
        """텍스트 입력"""
        return self._send_command({
            "action": "type",
            "selector": selector,
            "text": text
        })

    def screenshot(self, path: str = None) -> Dict[str, Any]:
        """스크린샷 캡처"""
        return self._send_command({"action": "screenshot", "path": path})

    def wait(self, seconds: float = 1) -> Dict[str, Any]:
        """대기"""
        return self._send_command({"action": "wait", "seconds": seconds})

    def eval(self, script: str) -> Dict[str, Any]:
        """JavaScript 실행"""
        return self._send_command({"action": "eval", "script": script})

    def get_content(self) -> Dict[str, Any]:
        """페이지 HTML 가져오기"""
        return self._send_command({"action": "get_content"})

    def stop(self) -> Dict[str, Any]:
        """브라우저 종료"""
        result = self._send_command({"action": "stop"}, timeout=5)

        if self.thread:
            self.thread.join(timeout=5)

        self.running = False
        return result


# 편의 함수들
def quick_start():
    """빠른 시작 헬퍼"""
    browser = REPLBrowser()
    result = browser.start()

    if result["status"] == "started":
        print("✅ 브라우저 시작 완료!")
        print("사용법: browser.goto('https://example.com')")
        return browser
    else:
        print(f"❌ 시작 실패: {result['message']}")
        return None


# 사용 예제
if __name__ == "__main__":
    # REPL에서 실행 예제
    print("REPL 브라우저 테스트")
    print("-" * 50)

    # 브라우저 시작
    browser = REPLBrowser()
    print(browser.start())

    # 페이지 이동
    print(browser.goto("https://example.com"))

    # 스크린샷
    print(browser.screenshot("test.png"))

    # 종료
    print(browser.stop())
