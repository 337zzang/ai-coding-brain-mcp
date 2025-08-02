
"""
웹 자동화 실용 예제 모음
AI Coding Brain MCP - Web Automation Examples
"""

import asyncio
import os
import json
import csv
from datetime import datetime
from playwright.async_api import async_playwright

class WebAutomationExamples:
    """실용적인 웹 자동화 예제들"""

    def __init__(self):
        self.browser = None
        self.page = None
        self.results = []

    async def setup(self, headless=False):
        """브라우저 설정"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)
        self.page = await self.browser.new_page()

    async def cleanup(self):
        """정리"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    # 예제 1: 웹사이트 모니터링
    async def monitor_website_status(self, urls):
        """여러 웹사이트의 상태를 모니터링"""
        print("🔍 웹사이트 상태 모니터링")
        print("-" * 40)

        results = []
        for url in urls:
            try:
                start_time = datetime.now()
                response = await self.page.goto(url, timeout=10000)
                load_time = (datetime.now() - start_time).total_seconds()

                result = {
                    "url": url,
                    "status": response.status,
                    "ok": response.ok,
                    "load_time": f"{load_time:.2f}s",
                    "timestamp": datetime.now().isoformat()
                }
                results.append(result)

                status_icon = "✅" if response.ok else "❌"
                print(f"{status_icon} {url} - {response.status} ({load_time:.2f}s)")

            except Exception as e:
                results.append({
                    "url": url,
                    "status": "error",
                    "ok": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                print(f"❌ {url} - 오류: {str(e)[:50]}")

        # 결과 저장
        with open("website_monitoring.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        return results

    # 예제 2: 검색 결과 스크래핑
    async def scrape_search_results(self, query, max_results=10):
        """검색 결과 수집"""
        print(f"\n🔎 '{query}' 검색 결과 수집")
        print("-" * 40)

        # DuckDuckGo 사용 (더 간단함)
        await self.page.goto("https://duckduckgo.com")

        # 검색
        search_box = await self.page.wait_for_selector('input[name="q"]')
        await search_box.fill(query)
        await search_box.press("Enter")

        # 결과 대기
        await self.page.wait_for_selector('.result__body')

        # 결과 추출
        results = await self.page.evaluate("""(maxResults) => {
            const results = [];
            const items = document.querySelectorAll('.result');

            for (let i = 0; i < Math.min(items.length, maxResults); i++) {
                const item = items[i];
                const titleEl = item.querySelector('.result__title');
                const snippetEl = item.querySelector('.result__snippet');
                const urlEl = item.querySelector('.result__url');

                if (titleEl && snippetEl) {
                    results.push({
                        title: titleEl.textContent.trim(),
                        snippet: snippetEl.textContent.trim(),
                        url: urlEl ? urlEl.textContent.trim() : ''
                    });
                }
            }

            return results;
        }""", max_results)

        # 결과 출력 및 저장
        print(f"\n검색 결과 {len(results)}개 수집:")
        for i, result in enumerate(results[:5], 1):  # 처음 5개만 출력
            print(f"\n{i}. {result['title']}")
            print(f"   {result['snippet'][:100]}...")

        # CSV로 저장
        with open(f"search_results_{query.replace(' ', '_')}.csv", "w", 
                  encoding="utf-8", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['title', 'snippet', 'url'])
            writer.writeheader()
            writer.writerows(results)

        return results

    # 예제 3: 폼 자동 작성
    async def auto_fill_form(self, form_data):
        """폼 자동 작성 예제"""
        print("\n📝 폼 자동 작성")
        print("-" * 40)

        # 테스트 폼 페이지
        await self.page.goto("https://www.w3schools.com/html/tryit.asp?filename=tryhtml_form_submit")

        # iframe 전환
        frame = self.page.frame("iframeResult")
        if not frame:
            print("❌ 테스트 폼을 찾을 수 없습니다")
            return

        # 폼 작성
        for field_name, value in form_data.items():
            try:
                # 다양한 selector 시도
                selectors = [
                    f'input[name="{field_name}"]',
                    f'##{field_name}',
                    f'input[placeholder*="{field_name}"]'
                ]

                for selector in selectors:
                    try:
                        await frame.fill(selector, value)
                        print(f"✅ {field_name}: {value}")
                        break
                    except:
                        continue

            except Exception as e:
                print(f"⚠️ {field_name} 필드 작성 실패")

        # 스크린샷
        await self.page.screenshot(path="screenshot/form_filled.png")
        print("\n📸 스크린샷 저장: screenshot/form_filled.png")

    # 예제 4: 페이지 성능 측정
    async def measure_page_performance(self, url):
        """페이지 성능 측정"""
        print(f"\n⚡ 페이지 성능 측정: {url}")
        print("-" * 40)

        # 성능 메트릭 수집
        await self.page.goto(url)

        metrics = await self.page.evaluate("""() => {
            const timing = performance.timing;
            const navigation = performance.navigation;

            return {
                // 네비게이션 타이밍
                dns: timing.domainLookupEnd - timing.domainLookupStart,
                tcp: timing.connectEnd - timing.connectStart,
                request: timing.responseStart - timing.requestStart,
                response: timing.responseEnd - timing.responseStart,
                dom: timing.domComplete - timing.domLoading,
                load: timing.loadEventEnd - timing.loadEventStart,
                total: timing.loadEventEnd - timing.navigationStart,

                // 리소스 정보
                resources: performance.getEntriesByType('resource').length,

                // 메모리 사용량 (Chrome only)
                memory: performance.memory ? {
                    used: Math.round(performance.memory.usedJSHeapSize / 1048576),
                    total: Math.round(performance.memory.totalJSHeapSize / 1048576)
                } : null
            };
        }""")

        # 결과 출력
        print(f"\n📊 성능 메트릭:")
        print(f"  DNS 조회: {metrics['dns']}ms")
        print(f"  TCP 연결: {metrics['tcp']}ms")
        print(f"  요청 시간: {metrics['request']}ms")
        print(f"  응답 시간: {metrics['response']}ms")
        print(f"  DOM 로딩: {metrics['dom']}ms")
        print(f"  전체 로딩: {metrics['total']}ms")
        print(f"  리소스 수: {metrics['resources']}개")

        if metrics['memory']:
            print(f"  메모리 사용: {metrics['memory']['used']}MB / {metrics['memory']['total']}MB")

        return metrics

    # 예제 5: 스크린샷 비교 (시각적 회귀 테스트)
    async def visual_regression_test(self, url, baseline_path=None):
        """시각적 회귀 테스트"""
        print(f"\n📷 시각적 회귀 테스트: {url}")
        print("-" * 40)

        await self.page.goto(url)
        await self.page.wait_for_load_state('networkidle')

        # 현재 스크린샷
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        current_path = f"screenshot/visual_test_{timestamp}.png"
        await self.page.screenshot(path=current_path, full_page=True)

        print(f"✅ 스크린샷 저장: {current_path}")

        # 베이스라인과 비교 (실제로는 이미지 비교 라이브러리 사용)
        if baseline_path and os.path.exists(baseline_path):
            print(f"📊 베이스라인과 비교 중...")
            # 여기서는 간단히 파일 크기만 비교
            current_size = os.path.getsize(current_path)
            baseline_size = os.path.getsize(baseline_path)
            diff_percent = abs(current_size - baseline_size) / baseline_size * 100

            if diff_percent < 5:
                print(f"✅ 시각적 변화 없음 (차이: {diff_percent:.1f}%)")
            else:
                print(f"⚠️ 시각적 변화 감지 (차이: {diff_percent:.1f}%)")

        return current_path

# 실행 예제
async def run_examples():
    """모든 예제 실행"""
    examples = WebAutomationExamples()
    await examples.setup(headless=False)

    try:
        # 1. 웹사이트 모니터링
        await examples.monitor_website_status([
            "https://example.com",
            "https://google.com",
            "https://github.com"
        ])

        # 2. 검색 결과 수집
        await examples.scrape_search_results("Python web scraping", max_results=10)

        # 3. 폼 자동 작성
        await examples.auto_fill_form({
            "fname": "Test",
            "lname": "User",
            "email": "test@example.com"
        })

        # 4. 성능 측정
        await examples.measure_page_performance("https://example.com")

        # 5. 시각적 테스트
        await examples.visual_regression_test("https://example.com")

    finally:
        await examples.cleanup()

    print("\n✅ 모든 예제 실행 완료!")

if __name__ == "__main__":
    asyncio.run(run_examples())
