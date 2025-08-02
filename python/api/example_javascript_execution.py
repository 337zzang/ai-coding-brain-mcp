"""
JavaScript 실행 메커니즘 예제
작성일: 2025-08-02

이 스크립트는 웹 자동화에서 JavaScript를 활용하는 다양한 방법을 보여줍니다.
"""

# 필요한 모듈 import
from python.api.web_automation_helpers import (
    web_start, web_stop, web_goto,
    web_evaluate, web_execute_script,
    web_evaluate_element, web_wait_for_function
)


def example_basic_evaluation():
    """기본적인 JavaScript 실행 예제"""
    print("=== 기본 JavaScript 실행 예제 ===\n")

    # 브라우저 시작
    h.web_start(headless=False)
    h.web_goto("https://example.com")

    # 1. 간단한 표현식
    title = web_evaluate("document.title")["data"]
    print(f"페이지 제목: {title}")

    # 2. DOM 요소 개수
    link_count = web_evaluate("document.querySelectorAll('a').length")["data"]
    print(f"링크 개수: {link_count}")

    # 3. 현재 URL
    url = web_evaluate("window.location.href")["data"]
    print(f"현재 URL: {url}")

    web_stop()


def example_data_extraction():
    """데이터 추출 예제"""
    print("\n=== 데이터 추출 예제 ===\n")

    h.web_start(headless=False)
    h.web_goto("https://quotes.toscrape.com")

    # 모든 인용구 추출
    script = """
    const quotes = document.querySelectorAll('.quote');
    return Array.from(quotes).map(quote => ({
        text: quote.querySelector('.text').textContent,
        author: quote.querySelector('.author').textContent,
        tags: Array.from(quote.querySelectorAll('.tag')).map(tag => tag.textContent)
    }));
    """

    result = web_execute_script(script)
    if result["ok"]:
        quotes = result["data"]
        print(f"추출된 인용구 수: {len(quotes)}")

        # 첫 번째 인용구 출력
        if quotes:
            first = quotes[0]
            print(f"\n첫 번째 인용구:")
            print(f"  텍스트: {first['text']}")
            print(f"  저자: {first['author']}")
            print(f"  태그: {', '.join(first['tags'])}")

    web_stop()


def example_dynamic_interaction():
    """동적 상호작용 예제"""
    print("\n=== 동적 상호작용 예제 ===\n")

    h.web_start(headless=False)
    h.web_goto("https://www.w3schools.com/html/html_forms.asp")

    # 폼 필드 찾고 값 설정
    print("폼 필드에 값 입력...")

    # 첫 번째 입력 필드 찾기
    has_input = web_evaluate("document.querySelector('input[type=text]') !== null")["data"]

    if has_input:
        # 입력 필드에 값 설정
        web_evaluate_element(
            "input[type=text]", 
            "element.value = 'JavaScript로 입력한 텍스트'"
        )
        print("✓ 텍스트 입력 완료")

        # 입력된 값 확인
        value = web_evaluate_element(
            "input[type=text]",
            "return element.value"
        )["data"]
        print(f"입력된 값: {value}")

    web_stop()


def example_wait_conditions():
    """대기 조건 예제"""
    print("\n=== 대기 조건 예제 ===\n")

    h.web_start(headless=False)
    h.web_goto("https://httpbin.org/delay/2")

    print("페이지 로딩 대기 중...")

    # 페이지 완전 로드 대기
    result = web_wait_for_function("document.readyState === 'complete'")
    if result["ok"]:
        print(f"✓ 페이지 로드 완료 (대기 시간: {result['wait_time']:.2f}초)")

    # JSON 데이터 로드 확인
    has_pre = web_wait_for_function(
        "document.querySelector('pre') !== null",
        timeout=5000
    )

    if has_pre["ok"]:
        # JSON 데이터 추출
        json_text = web_evaluate("document.querySelector('pre').textContent")["data"]
        print(f"\n로드된 JSON 데이터 길이: {len(json_text)} 문자")

    web_stop()


def example_security_features():
    """보안 기능 예제"""
    print("\n=== 보안 기능 예제 ===\n")

    # 브라우저 없이 검증만 수행
    test_scripts = [
        ("document.title", True, "안전한 스크립트"),
        ("eval('alert(1)')", False, "eval 사용 - 위험"),
        ("document.cookie", False, "쿠키 접근 - 위험"),
        ("document.querySelector('.test')", True, "안전한 DOM 접근")
    ]

    print("스크립트 보안 검증:")
    for script, expected_safe, description in test_scripts:
        result = web_evaluate(script, strict=True)
        is_safe = result["ok"]
        status = "✓ 안전" if is_safe == expected_safe else "✗ 실패"
        print(f"  {status} - {description}: {script[:30]}...")
        if not is_safe and expected_safe:
            print(f"       오류: {result['error']}")


if __name__ == "__main__":
    print("JavaScript 실행 메커니즘 예제 스크립트\n")
    print("실행할 예제를 선택하세요:")
    print("1. 기본 JavaScript 실행")
    print("2. 데이터 추출")
    print("3. 동적 상호작용")
    print("4. 대기 조건")
    print("5. 보안 기능 테스트")
    print("6. 모든 예제 실행")

    choice = input("\n선택 (1-6): ")

    examples = {
        "1": example_basic_evaluation,
        "2": example_data_extraction,
        "3": example_dynamic_interaction,
        "4": example_wait_conditions,
        "5": example_security_features,
        "6": lambda: [f() for f in [
            example_basic_evaluation,
            example_data_extraction,
            example_dynamic_interaction,
            example_wait_conditions,
            example_security_features
        ]]
    }

    if choice in examples:
        examples[choice]()
        print("\n✅ 예제 실행 완료!")
    else:
        print("잘못된 선택입니다.")
