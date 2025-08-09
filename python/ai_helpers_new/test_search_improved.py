#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_search_improved.py - 개선된 search 모듈 테스트
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from search_improved import (
    search, is_binary_file, search_files_generator,
    search_code, search_function, search_class,
    get_statistics, clear_cache
)

def test_binary_detection():
    """바이너리 파일 감지 테스트"""
    print("🧪 Test 1: Binary File Detection")

    # 테스트용 바이너리 파일 생성
    test_binary = "test_binary.dat"
    with open(test_binary, 'wb') as f:
        f.write(b'\x00\x01\x02\x03')

    assert is_binary_file(test_binary) == True
    print("  ✅ Binary file detected correctly")

    # 텍스트 파일
    test_text = "test_text.txt"
    with open(test_text, 'w') as f:
        f.write("Hello World")

    assert is_binary_file(test_text) == False
    print("  ✅ Text file detected correctly")

    # 정리
    os.remove(test_binary)
    os.remove(test_text)

def test_generator():
    """제너레이터 기반 파일 탐색 테스트"""
    print("\n🧪 Test 2: File Generator")

    count = 0
    for file_path in search_files_generator(".", "*.py", max_depth=1):
        count += 1
        if count >= 5:  # 조기 종료 테스트
            break

    print(f"  ✅ Found {count} Python files (early exit works)")

def test_search_code():
    """코드 검색 테스트"""
    print("\n🧪 Test 3: Code Search")

    # 테스트 파일 생성
    test_file = "test_search.py"
    with open(test_file, 'w') as f:
        f.write("""
def hello_world():
    print("Hello World")

def test_function():
    pass
""")

    # 정규식 검색
    result = search_code("hello.*world", ".", test_file, use_regex=True)
    assert result['ok'] == True
    assert len(result['data']) > 0
    print("  ✅ Regex search works")

    # 리터럴 검색 (대소문자 무시)
    result = search_code("HELLO", ".", test_file, use_regex=False, case_sensitive=False)
    assert result['ok'] == True
    assert len(result['data']) > 0
    print("  ✅ Case-insensitive literal search works")

    # 컨텍스트 포함 검색
    result = search_code("print", ".", test_file, context_lines=1)
    assert result['ok'] == True
    if result['data']:
        assert result['data'][0].get('context') is not None
    print("  ✅ Context lines work")

    os.remove(test_file)

def test_ast_search():
    """AST 기반 검색 테스트"""
    print("\n🧪 Test 4: AST-based Search")

    # 테스트 파일 생성
    test_file = "test_ast.py"
    with open(test_file, 'w') as f:
        f.write("""
@decorator
def my_function(arg1, arg2):
    return arg1 + arg2

class MyClass(BaseClass):
    def method(self):
        pass
""")

    # 함수 검색
    result = search_function("my_function", ".")
    assert result['ok'] == True
    if result['data']:
        func = result['data'][0]
        assert func['mode'] == 'ast'  # mode가 'ast'인지 확인
        assert func['name'] == 'my_function'
        print(f"  ✅ Function search works (mode: {func['mode']})")

    # 클래스 검색
    result = search_class("MyClass", ".")
    assert result['ok'] == True
    if result['data']:
        cls = result['data'][0]
        assert cls['mode'] == 'ast'  # mode가 'ast'인지 확인
        assert 'BaseClass' in cls.get('bases', [])
        print(f"  ✅ Class search works (mode: {cls['mode']})")

    os.remove(test_file)

def test_statistics():
    """통계 함수 테스트"""
    print("\n🧪 Test 5: Statistics")

    result = get_statistics(".", include_tests=False)
    assert result['ok'] == True

    stats = result['data']
    assert 'total_files' in stats
    assert 'py_files' in stats
    assert 'test_files' in stats

    print(f"  ✅ Statistics work:")
    print(f"     - Total files: {stats['total_files']}")
    print(f"     - Python files: {stats['py_files']}")
    print(f"     - Test files: {stats['test_files']}")

def test_namespace():
    """네임스페이스 스타일 테스트"""
    print("\n🧪 Test 6: Namespace Style")

    # search.files()
    files = search.files("*.py", ".")
    assert isinstance(files, list)
    print(f"  ✅ search.files() works ({len(files)} files)")

    # search.statistics()
    stats = search.statistics(".")
    assert stats['ok'] == True
    print("  ✅ search.statistics() works")

if __name__ == "__main__":
    print("="*60)
    print("🔬 Testing Improved Search Module")
    print("="*60)

    try:
        test_binary_detection()
        test_generator()
        test_search_code()
        test_ast_search()
        test_statistics()
        test_namespace()

        print("\n" + "="*60)
        print("✅ All tests passed!")
        print("="*60)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
