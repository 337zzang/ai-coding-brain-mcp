"""
웹 브라우저 세션 관리자
AI Coding Brain MCP - Web Browser Session Manager
"""

from playwright.sync_api import sync_playwright
import os
from datetime import datetime

class WebSession:
    """동기식 웹 브라우저 세션"""

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        self.is_running = False

    def start(self, headless=False):
        """브라우저 시작"""
        if self.is_running:
            return "브라우저가 이미 실행 중입니다."

        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=headless,
                args=['--start-maximized']
            )
            self.page = self.browser.new_page()
            self.is_running = True
            return "✅ 브라우저가 시작되었습니다."
        except Exception as e:
            return f"❌ 브라우저 시작 실패: {e}"

    def goto(self, url):
        """URL로 이동"""
        if not self.is_running:
            return "❌ 브라우저가 실행되지 않았습니다."

        try:
            self.page.goto(url)
            self.page.wait_for_load_state("networkidle")
            title = self.page.title()
            return f"✅ 페이지 이동 완료: {title} ({url})"
        except Exception as e:
            return f"❌ 페이지 이동 실패: {e}"

    def screenshot(self, name=None):
        """스크린샷 저장"""
        if not self.is_running:
            return "❌ 브라우저가 실행되지 않았습니다."

        try:
            if not name:
                name = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            path = os.path.join("screenshot", f"{name}.png")
            os.makedirs("screenshot", exist_ok=True)
            self.page.screenshot(path=path)
            return f"✅ 스크린샷 저장: {path}"
        except Exception as e:
            return f"❌ 스크린샷 실패: {e}"

    def search(self, query):
        """검색"""
        if not self.is_running:
            return "❌ 브라우저가 실행되지 않았습니다."

        try:
            # 네이버 검색
            if "naver.com" in self.page.url:
                search_box = self.page.query_selector("#query")
                if search_box:
                    search_box.fill(query)
                    search_box.press("Enter")
                    self.page.wait_for_load_state("networkidle")
                    return f"✅ 네이버에서 '{query}' 검색 완료"

            # 구글 검색
            elif "google.com" in self.page.url:
                search_box = self.page.query_selector('textarea[name="q"], input[name="q"]')
                if search_box:
                    search_box.fill(query)
                    search_box.press("Enter")
                    self.page.wait_for_load_state("networkidle")
                    return f"✅ 구글에서 '{query}' 검색 완료"

            else:
                return "❌ 현재 페이지에서 검색창을 찾을 수 없습니다."

        except Exception as e:
            return f"❌ 검색 실패: {e}"

    def click(self, text=None, selector=None):
        """요소 클릭 (텍스트 또는 selector)"""
        if not self.is_running:
            return "❌ 브라우저가 실행되지 않았습니다."

        try:
            if text:
                # 텍스트로 찾기
                element = self.page.get_by_text(text).first
                element.click()
                return f"✅ 클릭 완료: '{text}'"
            elif selector:
                element = self.page.wait_for_selector(selector, timeout=5000)
                element.click()
                return f"✅ 클릭 완료: {selector}"
            else:
                return "❌ text 또는 selector를 지정하세요."
        except Exception as e:
            return f"❌ 클릭 실패: {e}"

    def get_info(self):
        """현재 페이지 정보"""
        if not self.is_running:
            return "❌ 브라우저가 실행되지 않았습니다."

        try:
            title = self.page.title()
            url = self.page.url
            return f"📄 현재 페이지:\n  제목: {title}\n  URL: {url}"
        except Exception as e:
            return f"❌ 정보 조회 실패: {e}"

    def back(self):
        """뒤로 가기"""
        if not self.is_running:
            return "❌ 브라우저가 실행되지 않았습니다."

        try:
            self.page.go_back()
            return "✅ 뒤로 가기 완료"
        except Exception as e:
            return f"❌ 뒤로 가기 실패: {e}"

    def stop(self):
        """브라우저 종료"""
        if not self.is_running:
            return "❌ 브라우저가 실행되지 않았습니다."

        try:
            self.browser.close()
            self.playwright.stop()
            self.is_running = False
            return "✅ 브라우저가 종료되었습니다."
        except Exception as e:
            return f"❌ 브라우저 종료 실패: {e}"

    def analyze_page(self):
        """현재 페이지의 주요 요소들 분석"""
        if not self.is_running:
            return "❌ 브라우저가 실행되지 않았습니다."

        try:
            # JavaScript로 페이지 요소 분석
            analysis = self.page.evaluate("""() => {
                const elements = {
                    links: [],
                    buttons: [],
                    inputs: [],
                    images: [],
                    headings: [],
                    divs_with_id: [],
                    divs_with_class: []
                };

                // 링크 수집
                document.querySelectorAll('a').forEach((el, i) => {
                    if (i < 10 && el.textContent.trim()) {
                        elements.links.push({
                            text: el.textContent.trim().substring(0, 30),
                            href: el.href,
                            selector: el.id ? `#${el.id}` : el.className ? `.${el.className.split(' ')[0]}` : `a:nth-of-type(${i+1})`
                        });
                    }
                });

                // 버튼 수집
                document.querySelectorAll('button, input[type="button"], input[type="submit"]').forEach((el, i) => {
                    if (i < 10) {
                        elements.buttons.push({
                            text: el.textContent?.trim() || el.value || 'Button',
                            type: el.type,
                            selector: el.id ? `#${el.id}` : el.className ? `.${el.className.split(' ')[0]}` : `button:nth-of-type(${i+1})`
                        });
                    }
                });

                // 입력 필드 수집
                document.querySelectorAll('input[type="text"], input[type="search"], textarea').forEach((el, i) => {
                    if (i < 10) {
                        elements.inputs.push({
                            type: el.type || 'textarea',
                            placeholder: el.placeholder || '',
                            name: el.name || '',
                            id: el.id || '',
                            selector: el.id ? `#${el.id}` : el.name ? `[name="${el.name}"]` : `input:nth-of-type(${i+1})`
                        });
                    }
                });

                // ID가 있는 주요 div
                document.querySelectorAll('div[id]').forEach((el, i) => {
                    if (i < 10) {
                        elements.divs_with_id.push({
                            id: el.id,
                            selector: `#${el.id}`,
                            classes: el.className
                        });
                    }
                });

                // 제목 요소
                document.querySelectorAll('h1, h2, h3').forEach((el, i) => {
                    if (i < 10 && el.textContent.trim()) {
                        elements.headings.push({
                            tag: el.tagName,
                            text: el.textContent.trim().substring(0, 50),
                            selector: el.id ? `#${el.id}` : `${el.tagName.toLowerCase()}:nth-of-type(${i+1})`
                        });
                    }
                });

                return elements;
            }""")

            # 결과 포맷팅
            result = "📊 페이지 요소 분석 결과\n" + "="*50 + "\n"

            # 링크
            if analysis['links']:
                result += "\n🔗 주요 링크:\n"
                for link in analysis['links'][:5]:
                    result += f"  - '{link['text']}' → {link['selector']}\n"

            # 버튼
            if analysis['buttons']:
                result += "\n🔘 버튼:\n"
                for btn in analysis['buttons'][:5]:
                    result += f"  - '{btn['text']}' → {btn['selector']}\n"

            # 입력 필드
            if analysis['inputs']:
                result += "\n📝 입력 필드:\n"
                for inp in analysis['inputs'][:5]:
                    result += f"  - {inp['type']} → {inp['selector']}\n"

            # ID가 있는 주요 요소
            if analysis['divs_with_id']:
                result += "\n🏷️ ID가 있는 주요 요소:\n"
                for div in analysis['divs_with_id'][:5]:
                    result += f"  - {div['selector']}\n"

            return result

        except Exception as e:
            return f"❌ 분석 실패: {e}"

    def find_elements(self, selector, limit=10):
        """특정 셀렉터로 요소 찾기"""
        if not self.is_running:
            return "❌ 브라우저가 실행되지 않았습니다."

        try:
            elements = self.page.evaluate(f"""(selector) => {{
                const elements = document.querySelectorAll(selector);
                const results = [];

                elements.forEach((el, i) => {{
                    if (i < {limit}) {{
                        results.push({{
                            index: i,
                            tagName: el.tagName,
                            text: el.textContent?.trim().substring(0, 50) || '',
                            id: el.id || '',
                            classes: el.className || '',
                            href: el.href || '',
                            visible: el.offsetParent !== null
                        }});
                    }}
                }});

                return {{
                    total: elements.length,
                    results: results
                }};
            }}""", selector)

            result = f"🔍 '{selector}' 검색 결과: 총 {elements['total']}개\n"
            result += "-" * 40 + "\n"

            for el in elements['results']:
                result += f"[{el['index']}] <{el['tagName']}> "
                if el['id']:
                    result += f"id='{el['id']}' "
                if el['text']:
                    result += f"텍스트: '{el['text']}'"
                result += "\n"

            return result

        except Exception as e:
            return f"❌ 검색 실패: {e}"

    def highlight_element(self, selector):
        """요소 하이라이트"""
        if not self.is_running:
            return "❌ 브라우저가 실행되지 않았습니다."

        try:
            self.page.evaluate("""(selector) => {
                const element = document.querySelector(selector);
                if (element) {
                    element.style.border = '3px solid red';
                    element.style.backgroundColor = 'rgba(255, 0, 0, 0.1)';
                    setTimeout(() => {
                        element.style.border = '';
                        element.style.backgroundColor = '';
                    }, 3000);
                    return true;
                }
                return false;
            }""", selector)

            return f"✅ '{selector}' 요소를 3초간 빨간색으로 하이라이트합니다."

        except Exception as e:
            return f"❌ 하이라이트 실패: {e}"


# 사용 예시
if __name__ == "__main__":
    # 브라우저 세션 생성
    browser = WebSession()

    # 브라우저 시작
    print(browser.start())

    # 네이버로 이동
    print(browser.goto("https://www.naver.com"))

    # 페이지 분석
    print(browser.analyze_page())

    # 검색
    print(browser.search("Python"))

    # 스크린샷
    print(browser.screenshot("naver_python"))

    # 브라우저 종료
    print(browser.stop())
