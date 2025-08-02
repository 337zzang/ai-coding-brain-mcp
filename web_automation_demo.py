#!/usr/bin/env python3
"""
웹 자동화 헬퍼 함수 실제 사용 예제
- 세션 내 브라우저 자동화
- 진행사항 자동 스크래핑
"""

import time
import json
from datetime import datetime

def demo_search_and_scrape():
    """검색 및 스크래핑 데모"""
    print("🔍 검색 및 스크래핑 데모 시작")
    print("=" * 60)

    # 1. 브라우저 시작
    print("\n1️⃣ 브라우저 시작...")
    h.web_start(headless=False, project_name="search_demo")
    time.sleep(2)

    # 2. 현재 상태 확인
    status = h.web_status()
    print(f"✅ 브라우저 상태: {status['state']}")

    # 3. DuckDuckGo로 이동
    print("\n2️⃣ DuckDuckGo 검색 페이지로 이동...")
    h.web_goto("https://duckduckgo.com")
    time.sleep(1)

    # 4. 검색 수행
    print("\n3️⃣ 'Python web automation' 검색...")
    h.web_type("input[name='q']", "Python web automation")
    h.web_click("button[type='submit']")
    h.web_wait(3)  # 결과 로딩 대기

    # 5. 스크린샷 저장
    print("\n4️⃣ 검색 결과 스크린샷 저장...")
    screenshot_path = f"screenshot/search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    h.web_screenshot(screenshot_path)
    print(f"📸 스크린샷 저장: {screenshot_path}")

    # 6. 검색 결과 추출
    print("\n5️⃣ 검색 결과 추출...")
    try:
        # 개별 요소 추출
        first_result_title = h.web_extract(".result__title")
        print(f"첫 번째 결과: {first_result_title}")

        # 배치 추출
        results = h.web_extract_batch(".result", {
            "title": ".result__title",
            "url": ".result__url", 
            "snippet": ".result__snippet"
        })

        print(f"\n✅ 총 {len(results)}개 결과 추출")
        for i, result in enumerate(results[:3], 1):
            print(f"\n{i}. {result.get('title', 'N/A')}")
            print(f"   URL: {result.get('url', 'N/A')}")
            print(f"   설명: {result.get('snippet', 'N/A')[:100]}...")

    except Exception as e:
        print(f"⚠️ 추출 중 오류: {e}")

    # 7. 진행사항 확인
    print("\n6️⃣ 기록된 액션 확인...")
    record_status = h.web_record_status()
    print(f"기록 상태: {record_status}")

    actions = h.web_get_data()
    print(f"\n📊 총 {len(actions)}개 액션 기록됨:")
    for i, action in enumerate(actions[-5:], 1):  # 마지막 5개만
        print(f"  {i}. {action['action']} - {action.get('selector', 'N/A')}")

    # 8. 스크립트 생성
    print("\n7️⃣ 재사용 가능한 스크립트 생성...")
    script_path = "generated_search_scraper.py"
    h.web_generate_script(script_path)
    print(f"✅ 스크립트 생성: {script_path}")

    # 9. 브라우저 종료
    print("\n8️⃣ 브라우저 종료...")
    h.web_stop()
    print("✅ 데모 완료!")

    return actions

def demo_monitoring():
    """실시간 모니터링 데모"""
    print("\n📊 실시간 모니터링 데모")
    print("=" * 60)

    # 1. 브라우저 시작
    h.web_start(headless=False, project_name="monitoring_demo")

    # 2. 모니터링할 사이트들
    sites = [
        {"url": "https://example.com", "selector": "h1"},
        {"url": "https://httpbin.org/html", "selector": "h1"}
    ]

    # 3. 3회 모니터링
    for round in range(3):
        print(f"\n🔄 모니터링 라운드 {round + 1}/3")

        for site in sites:
            print(f"\n  📍 {site['url']} 확인 중...")
            h.web_goto(site['url'])
            time.sleep(1)

            # 데이터 추출
            try:
                content = h.web_extract(site['selector'])
                print(f"    내용: {content[:50]}...")

                # 스크린샷
                screenshot = f"screenshot/monitor_{round}_{site['url'].split('/')[2]}.png"
                h.web_screenshot(screenshot)
                print(f"    📸 스크린샷: {screenshot}")

            except Exception as e:
                print(f"    ❌ 오류: {e}")

        if round < 2:
            print("\n  ⏳ 10초 후 다음 라운드...")
            time.sleep(10)

    # 4. 수집된 데이터 저장
    all_actions = h.web_get_data()

    # JSON으로 저장
    with open("monitoring_log.json", "w", encoding="utf-8") as f:
        json.dump(all_actions, f, indent=2, ensure_ascii=False)

    print(f"\n✅ 모니터링 완료! 총 {len(all_actions)}개 액션 기록됨")
    print("📄 로그 저장: monitoring_log.json")

    h.web_stop()
    return all_actions

def demo_form_automation():
    """폼 자동화 데모"""
    print("\n📝 폼 자동화 데모")
    print("=" * 60)

    h.web_start(headless=False, project_name="form_demo")

    # W3Schools 폼 예제 사용
    print("\n1️⃣ W3Schools 폼 예제 페이지 이동...")
    h.web_goto("https://www.w3schools.com/html/html_forms.asp")
    time.sleep(2)

    print("\n2️⃣ 예제 폼으로 스크롤...")
    # Try It Yourself 버튼 찾아서 클릭
    try:
        h.web_click("a.w3-btn[href*='tryhtml_form_submit']")
        time.sleep(3)

        # 새 탭/창으로 전환될 수 있음
        print("\n3️⃣ 폼 작성...")

        # 폼 데이터 추출 (현재 상태)
        print("   현재 폼 구조 분석...")
        form_structure = h.web_extract_form("form")
        print(f"   폼 필드: {list(form_structure.keys()) if form_structure else 'N/A'}")

    except Exception as e:
        print(f"⚠️ 폼 페이지 접근 실패: {e}")
        print("   대체 페이지로 이동...")

        # 대체: httpbin.org 폼 테스트
        h.web_goto("https://httpbin.org/forms/post")
        time.sleep(2)

        # 폼 작성
        h.web_type("input[name='custname']", "Test User")
        h.web_type("input[name='custtel']", "123-456-7890") 
        h.web_type("textarea[name='comments']", "자동화 테스트 코멘트입니다.")
        h.web_click("input[value='small']")  # 피자 사이즈
        h.web_click("input[value='bacon']")  # 토핑

        # 제출 전 데이터 확인
        form_data = h.web_extract_form("form")
        print("\n4️⃣ 제출할 데이터:")
        for key, value in (form_data or {}).items():
            print(f"   {key}: {value}")

        # 스크린샷
        h.web_screenshot("screenshot/form_filled.png")
        print("\n📸 작성된 폼 스크린샷 저장")

    print("\n5️⃣ 스크립트 생성...")
    h.web_generate_script("form_automation_script.py")

    h.web_stop()
    print("\n✅ 폼 자동화 데모 완료!")

# 실행
if __name__ == "__main__":
    print("🚀 웹 자동화 헬퍼 함수 데모")
    print("=" * 80)

    # 선택 메뉴
    print("\n데모 선택:")
    print("1. 검색 및 스크래핑")
    print("2. 실시간 모니터링")  
    print("3. 폼 자동화")
    print("4. 전체 실행")

    choice = input("\n선택 (1-4): ").strip()

    if choice == "1":
        demo_search_and_scrape()
    elif choice == "2":
        demo_monitoring()
    elif choice == "3":
        demo_form_automation()
    elif choice == "4":
        demo_search_and_scrape()
        time.sleep(3)
        demo_monitoring()
        time.sleep(3)
        demo_form_automation()
    else:
        print("잘못된 선택입니다.")
