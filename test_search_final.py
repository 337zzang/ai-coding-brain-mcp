#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
최종 통합 테스트 - 개선된 search.py
"""

import sys
import os
sys.path.insert(0, 'python')

# AI Helpers import
import ai_helpers_new as h

print("="*60)
print("[TEST] Search.py Improved Version Final Test")
print("="*60)

# Test 1: 네임스페이스 스타일
print("\n[Test 1] Namespace Style (h.search.*)")
try:
    files = h.search.files("*.py", ".", max_depth=0)
    print(f"  OK: h.search.files(): {len(files)} files found")

    stats = h.search.statistics(".")
    if stats['ok']:
        print(f"  OK: h.search.statistics(): {stats['data']['py_files']} Python files")
except Exception as e:
    print(f"  ERROR: {e}")

# Test 2: 새로운 함수들
print("\n[Test 2] New Functions")
try:
    # is_binary_file
    if hasattr(h, 'is_binary_file'):
        result = h.is_binary_file("test.txt")
        print(f"  OK: h.is_binary_file() available: {result}")
    else:
        print("  WARNING: h.is_binary_file() not available")

    # search_files_generator
    if hasattr(h, 'search_files_generator'):
        count = 0
        for _ in h.search_files_generator(".", "*.py", max_depth=0):
            count += 1
            if count >= 2:
                break
        print(f"  OK: h.search_files_generator() works: {count} files")
    else:
        print("  WARNING: h.search_files_generator() not available")

except Exception as e:
    print(f"  ERROR: {e}")

# Test 3: AST mode 확인
print("\n[Test 3] AST Mode Check")
try:
    result = h.search.function("test", ".")
    if result['ok'] and result['data']:
        mode = result['data'][0].get('mode', 'unknown')
        if mode == 'ast':
            print(f"  OK: AST mode correct: '{mode}'")
        else:
            print(f"  WARNING: Wrong mode: '{mode}' (expected 'ast')")
    else:
        print("  WARNING: No functions found for test")
except Exception as e:
    print(f"  ERROR: {e}")

# Test 4: 개선된 search_code
print("\n[Test 4] Improved search_code")
try:
    # use_regex 파라미터 테스트
    result = h.search_code("def.*test", ".", "*.py", max_results=2, use_regex=True)
    if result['ok']:
        print(f"  OK: Regex search: {len(result['data'])} matches")

    # case_sensitive 파라미터 테스트
    result = h.search_code("DEF", ".", "*.py", max_results=2, use_regex=False, case_sensitive=False)
    if result['ok']:
        print(f"  OK: Case-insensitive search: {len(result['data'])} matches")

    # context_lines 파라미터 테스트
    result = h.search_code("import", ".", "*.py", max_results=1, context_lines=2)
    if result['ok'] and result['data']:
        has_context = result['data'][0].get('context') is not None
        print(f"  OK: Context lines: {'included' if has_context else 'not included'}")

except Exception as e:
    print(f"  ERROR: {e}")

# Test 5: 캐시 함수
print("\n[Test 5] Cache Functions")
try:
    if hasattr(h, 'get_cache_info'):
        info = h.get_cache_info()
        if info['ok']:
            print(f"  OK: Cache info available: {len(info['data'])} caches")

    if hasattr(h, 'clear_cache'):
        result = h.clear_cache()
        if result['ok']:
            print(f"  OK: Cache cleared: {result['data']}")

except Exception as e:
    print(f"  ERROR: {e}")

print("\n" + "="*60)
print("[COMPLETE] All tests finished!")
print("="*60)
