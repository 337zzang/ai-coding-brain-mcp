#!/usr/bin/env python3
"""
Search Functions 리팩토링 테스트
새로운 반환 형식과 기능을 검증
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from python.ai_helpers.search import search_code_content, search_files_advanced
from python.ai_helpers.search_wrappers import search_code, find_class, find_function, find_import
from python.ai_helpers.helper_result import HelperResult

def test_search_code_content():
    """search_code_content 테스트"""
    print("\n=== search_code_content 테스트 ===")

    # 기본 검색 테스트
    result = search_code_content(".", "def", "*.py", max_results=5)

    # 반환 타입 확인
    assert isinstance(result, HelperResult), f"Expected HelperResult, got {type(result)}"
    assert result.ok, "Search should succeed"

    # 데이터 구조 확인
    assert isinstance(result.data, list), f"Expected list, got {type(result.data)}"

    if result.data:
        first = result.data[0]
        print(f"✅ 결과 수: {len(result.data)}")

        # 필수 필드 확인
        required_fields = ['line_number', 'code_line', 'matched_text', 'file_path']
        for field in required_fields:
            assert field in first, f"Missing required field: {field}"
            print(f"✅ {field}: {type(first[field]).__name__}")

        # matched_text 확인
        assert 'def' in first['matched_text'], "matched_text should contain search pattern"
        print(f"✅ matched_text 예시: '{first['matched_text']}'")

    # context 옵션 테스트
    result_with_context = search_code_content(".", "def", "*.py", 
                                            max_results=2, include_context=True)
    if result_with_context.ok and result_with_context.data:
        first = result_with_context.data[0]
        assert 'context' in first, "Context should be included when requested"
        print("✅ include_context 옵션 작동 확인")

    # 메타데이터 확인
    if hasattr(result, 'metadata'):
        print(f"✅ 메타데이터 존재: {list(result.metadata.keys())}")

    print("✅ search_code_content 테스트 통과!")
    return True

def test_search_files_advanced():
    """search_files_advanced 테스트"""
    print("\n=== search_files_advanced 테스트 ===")

    # 기본 검색 (경로만)
    result = search_files_advanced(".", "*.py", max_results=10)

    assert isinstance(result, HelperResult), f"Expected HelperResult, got {type(result)}"
    assert result.ok, "Search should succeed"
    assert isinstance(result.data, list), f"Expected list, got {type(result.data)}"

    if result.data:
        first = result.data[0]
        assert isinstance(first, str), f"Expected string paths, got {type(first)}"
        print(f"✅ 파일 경로 리스트 반환: {len(result.data)}개")
        print(f"✅ 첫 번째 경로: {first}")

    # 상세 정보 포함 검색
    result_detailed = search_files_advanced(".", "*.py", max_results=5, return_details=True)
    if result_detailed.ok and result_detailed.data:
        first = result_detailed.data[0]
        assert isinstance(first, dict), "Detailed results should be dicts"
        assert 'file_path' in first, "Should have file_path field"
        print("✅ return_details 옵션 작동 확인")

    print("✅ search_files_advanced 테스트 통과!")
    return True

def test_wrapper_functions():
    """Wrapper 함수들 테스트"""
    print("\n=== Wrapper 함수 테스트 ===")

    # search_code 테스트
    result = search_code("class", ".", "*.py")
    assert isinstance(result, HelperResult), "search_code should return HelperResult"
    print("✅ search_code 작동 확인")

    # find_class 테스트
    result = find_class("HelperResult", ".")
    assert isinstance(result, HelperResult), "find_class should return HelperResult"
    if result.ok and result.data:
        print(f"✅ find_class: {len(result.data)}개 클래스 발견")

    # find_function 테스트
    result = find_function("search_code_content", ".")
    assert isinstance(result, HelperResult), "find_function should return HelperResult"
    if result.ok and result.data:
        print(f"✅ find_function: {len(result.data)}개 함수 발견")

    # find_import 테스트
    result = find_import("os", ".")
    assert isinstance(result, HelperResult), "find_import should return HelperResult"
    if result.ok and result.data:
        print(f"✅ find_import: {len(result.data)}개 import 발견")

    print("✅ 모든 wrapper 함수 테스트 통과!")
    return True

def test_backward_compatibility():
    """하위 호환성 테스트"""
    print("\n=== 하위 호환성 테스트 ===")

    result = search_code_content(".", "def", "*.py", max_results=3)

    # _legacy_format 확인
    if hasattr(result, '_legacy_format'):
        legacy = result._legacy_format
        assert 'success' in legacy, "Legacy format should have 'success'"
        assert 'results' in legacy, "Legacy format should have 'results'"
        assert 'searched_files' in legacy, "Legacy format should have 'searched_files'"
        print("✅ 레거시 형식 호환성 제공 확인")

    # HelperResult의 dict-like 접근
    # 참고: 현재 HelperResult가 dict를 data로 가지면 __getitem__이 작동
    if isinstance(result.data, dict) and 'results' in result.data:
        # 기존 코드처럼 접근 가능
        print("✅ 기존 dict 형식으로도 접근 가능")

    return True

def run_all_tests():
    """모든 테스트 실행"""
    print("=" * 60)
    print("Search Functions 리팩토링 테스트 시작")
    print("=" * 60)

    tests = [
        test_search_code_content,
        test_search_files_advanced,
        test_wrapper_functions,
        test_backward_compatibility
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"\n❌ {test.__name__} 실패: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"테스트 결과: {passed}개 통과, {failed}개 실패")
    print("=" * 60)

    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
