
import asyncio
import os
import json
from datetime import datetime
from playwright.async_api import async_playwright

class WebAutomationTestSuite:
    """웹 자동화 종합 테스트 스위트"""

    def __init__(self):
        self.results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": [],
            "screenshots": [],
            "start_time": datetime.now().isoformat(),
            "tests": []
        }
        self.browser = None
        self.page = None

    async def setup(self):
        """테스트 환경 설정"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=False,
            args=['--start-maximized']
        )
        context = await self.browser.new_context(viewport={'width': 1920, 'height': 1080})
        self.page = await context.new_page()

    async def teardown(self):
        """테스트 환경 정리"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def save_screenshot(self, name):
        """스크린샷 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{name}_{timestamp}.png"
        filepath = os.path.join("screenshot", filename)
        await self.page.screenshot(path=filepath)
        self.results["screenshots"].append(filepath)
        return filepath

    async def run_test(self, test_name, test_func):
        """개별 테스트 실행"""
        print(f"\n🧪 {test_name}")
        print("-" * 40)

        test_result = {
            "name": test_name,
            "status": "failed",
            "error": None,
            "duration": 0,
            "screenshot": None
        }

        start_time = datetime.now()
        try:
            await test_func()
            test_result["status"] = "passed"
            self.results["passed"] += 1
            print(f"✅ {test_name} - PASSED")
        except Exception as e:
            test_result["status"] = "failed"
            test_result["error"] = str(e)
            self.results["failed"] += 1
            self.results["errors"].append(f"{test_name}: {e}")
            print(f"❌ {test_name} - FAILED: {e}")

            # 실패 시 스크린샷
            try:
                screenshot = await self.save_screenshot(f"error_{test_name}")
                test_result["screenshot"] = screenshot
            except:
                pass

        test_result["duration"] = (datetime.now() - start_time).total_seconds()
        self.results["tests"].append(test_result)
        self.results["total_tests"] += 1

    # 테스트 케이스들
    async def test_basic_navigation(self):
        """기본 네비게이션 테스트"""
        await self.page.goto("https://example.com")
        assert "Example Domain" in await self.page.title()
        await self.save_screenshot("basic_navigation")

    async def test_google_search(self):
        """구글 검색 테스트"""
        await self.page.goto("https://www.google.com")
        search_box = await self.page.wait_for_selector('textarea[name="q"], input[name="q"]')
        await search_box.type("Playwright automation")
        await search_box.press("Enter")
        await self.page.wait_for_load_state("networkidle")
        await self.save_screenshot("google_search")

    async def test_javascript_execution(self):
        """JavaScript 실행 테스트"""
        await self.page.goto("https://example.com")

        # 간단한 JS 실행
        result = await self.page.evaluate("1 + 1")
        assert result == 2

        # DOM 조작
        await self.page.evaluate("""
            document.body.style.backgroundColor = '#f0f0f0';
            document.querySelector('h1').textContent = 'Modified by JS';
        """)

        # 변경 확인
        h1_text = await self.page.text_content("h1")
        assert h1_text == "Modified by JS"
        await self.save_screenshot("js_execution")

    async def test_form_interaction(self):
        """폼 상호작용 테스트"""
        await self.page.goto("https://www.w3schools.com/html/html_forms.asp")

        # 폼 요소 찾기 및 입력
        try:
            fname_input = await self.page.wait_for_selector('#fname', timeout=5000)
            await fname_input.fill("Test")

            lname_input = await self.page.wait_for_selector('#lname', timeout=5000)
            await lname_input.fill("User")

            await self.save_screenshot("form_filled")
        except:
            # 대체 테스트
            await self.page.goto("https://httpbin.org/forms/post")
            await self.page.fill('input[name="custname"]', "Test Customer")
            await self.page.fill('textarea[name="comments"]', "Automated test comment")
            await self.save_screenshot("httpbin_form")

    async def test_wait_strategies(self):
        """다양한 대기 전략 테스트"""
        await self.page.goto("https://example.com")

        # 요소 대기
        await self.page.wait_for_selector('h1', state='visible')

        # 네트워크 안정화 대기
        await self.page.wait_for_load_state('networkidle')

        # 타임아웃 테스트
        try:
            await self.page.wait_for_selector('.non-existent-element', timeout=1000)
        except:
            pass  # 예상된 타임아웃

        await self.save_screenshot("wait_strategies")

    async def test_multi_tab_handling(self):
        """멀티 탭 처리 테스트"""
        # 첫 번째 탭
        await self.page.goto("https://example.com")

        # 새 탭 열기
        new_page = await self.browser.new_page()
        await new_page.goto("https://www.python.org")

        # 탭 전환
        await self.page.bring_to_front()
        await self.save_screenshot("tab1_example")

        await new_page.bring_to_front()
        await self.save_screenshot("tab2_python")

        # 새 탭 닫기
        await new_page.close()

    async def test_responsive_design(self):
        """반응형 디자인 테스트"""
        await self.page.goto("https://getbootstrap.com")

        # 다양한 뷰포트 크기 테스트
        viewports = [
            {"name": "mobile", "width": 375, "height": 667},
            {"name": "tablet", "width": 768, "height": 1024},
            {"name": "desktop", "width": 1920, "height": 1080}
        ]

        for viewport in viewports:
            await self.page.set_viewport_size(viewport)
            await self.page.wait_for_timeout(500)
            await self.save_screenshot(f"responsive_{viewport['name']}")

    async def test_error_handling(self):
        """에러 처리 테스트"""
        # 404 페이지 테스트
        response = await self.page.goto("https://example.com/nonexistent-page-404")
        # 대부분의 사이트는 404를 반환하지 않고 200으로 커스텀 404 페이지를 보여줌

        # 타임아웃 테스트
        try:
            await self.page.goto("https://example.com", timeout=1)  # 매우 짧은 타임아웃
        except:
            pass  # 예상된 타임아웃

        await self.save_screenshot("error_handling")

    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 웹 자동화 종합 테스트 시작")
        print("=" * 60)

        await self.setup()

        # 테스트 목록
        tests = [
            ("기본 네비게이션", self.test_basic_navigation),
            ("구글 검색", self.test_google_search),
            ("JavaScript 실행", self.test_javascript_execution),
            ("폼 상호작용", self.test_form_interaction),
            ("대기 전략", self.test_wait_strategies),
            ("멀티 탭 처리", self.test_multi_tab_handling),
            ("반응형 디자인", self.test_responsive_design),
            ("에러 처리", self.test_error_handling)
        ]

        for test_name, test_func in tests:
            await self.run_test(test_name, test_func)

        await self.teardown()

        # 결과 저장
        self.results["end_time"] = datetime.now().isoformat()
        with open("test_report.json", "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        # 결과 출력
        print("\n" + "=" * 60)
        print("📊 테스트 결과 요약")
        print("=" * 60)
        print(f"총 테스트: {self.results['total_tests']}")
        print(f"✅ 성공: {self.results['passed']}")
        print(f"❌ 실패: {self.results['failed']}")
        print(f"📸 스크린샷: {len(self.results['screenshots'])}개")

        if self.results['errors']:
            print("\n❌ 에러 목록:")
            for error in self.results['errors']:
                print(f"   - {error}")

        print(f"\n📄 상세 보고서: test_report.json")

        return self.results['failed'] == 0

async def main():
    suite = WebAutomationTestSuite()
    success = await suite.run_all_tests()
    return success

if __name__ == "__main__":
    import sys
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
