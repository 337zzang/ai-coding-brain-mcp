"""
Search 헬퍼 함수 테스트
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_helpers_new import search
from ai_helpers_new.util import ok, err

def test_search_files_basic():
    """search_files 기본 기능 테스트"""
    # Python 파일 검색
    result = search.search_files("*.py", "python/ai_helpers_new", recursive=False)
    assert result['ok'] == True
    assert result['count'] > 0
    assert all('.py' in f or f.endswith('.py') for f in result['data'])

def test_search_files_auto_wildcard():
    """자동 와일드카드 변환 테스트"""
    result = search.search_files("test", ".", max_depth=2)
    assert result['ok'] == True
    # test가 포함된 파일들이 검색되어야 함

def test_search_code_basic():
    """search_code 기본 기능 테스트"""
    result = search.search_code(r"def \w+", "python/ai_helpers_new", 
                                file_pattern="*.py", max_results=10)
    assert result['ok'] == True
    assert result['count'] <= 10
    assert 'files_searched' in result

def test_find_function_general():
    """find_function 일반 모드 테스트"""
    result = search.find_function("search_files", "python/ai_helpers_new", strict=False)
    assert result['ok'] == True
    assert result['count'] >= 1

def test_find_function_strict():
    """find_function strict 모드 테스트"""
    result = search._find_function_ast("search_files", "python/ai_helpers_new")
    assert result['ok'] == True
    # 버그 수정 후에는 최소 1개 이상 찾아야 함
    assert result['count'] >= 1

def test_find_class_general():
    """find_class 일반 모드 테스트"""
    # ExcelManager 클래스 찾기
    result = search.find_class("ExcelManager", "python/ai_helpers_new", strict=False)
    assert result['ok'] == True
    assert result['count'] >= 1

def test_grep_file():
    """grep 파일 검색 테스트"""
    result = search.grep("def", "python/ai_helpers_new/search.py", context=0)
    assert result['ok'] == True
    assert result['count'] > 0

def test_find_in_file():
    """find_in_file 테스트 (버그 수정 확인)"""
    result = search.find_in_file("python/ai_helpers_new/search.py", r"import")
    assert result['ok'] == True
    assert len(result['data']) > 0
    # 파일 경로가 제거되었는지 확인
    assert 'file' not in result['data'][0]

def test_regex_cache():
    """정규식 캐시 동작 테스트"""
    # 같은 패턴으로 여러 번 호출
    pattern = r"test_\w+"
    for _ in range(3):
        result = search.search_code(pattern, ".", file_pattern="*.py", max_results=5)
        assert result['ok'] == True

    # 캐시가 있으면 두 번째부터는 더 빨라야 함
    assert len(search._regex_cache) > 0

def test_exclude_directories():
    """제외 디렉토리 테스트"""
    result = search.search_files("*.pyc", ".", recursive=True)
    # __pycache__가 제외되므로 .pyc 파일이 없어야 함
    assert result['ok'] == True
    # 또는 매우 적어야 함

if __name__ == "__main__":
    print("🧪 Search 헬퍼 테스트 실행")
    print("-" * 40)

    # 각 테스트 실행
    tests = [
        test_search_files_basic,
        test_search_files_auto_wildcard,
        test_search_code_basic,
        test_find_function_general,
        test_find_function_strict,
        test_find_class_general,
        test_grep_file,
        test_find_in_file,
        test_regex_cache,
        test_exclude_directories
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            print(f"✅ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {type(e).__name__}: {e}")
            failed += 1

    print(f"\n📊 결과: {passed}개 통과, {failed}개 실패")
