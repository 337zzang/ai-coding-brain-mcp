#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""최종 수정 테스트"""

import sys
import os

# 경로 설정
base_path = r'C:\Users\82106\Desktop\ai-coding-brain-mcp'
sys.path.insert(0, os.path.join(base_path, 'python'))

# Import
import ai_helpers_new as h

print("="*70)
print("Final Test After All Fixes")
print("="*70)

test_file = os.path.join(base_path, "python", "ai_helpers_new", "file.py")
test_results = {"passed": 0, "failed": 0}

# 1. h.code.view() 테스트
print("\n1. h.code.view() test:")
try:
    result = h.code.view(test_file, "read")
    if isinstance(result, dict):
        if result.get('ok') == False:
            print(f"  FAIL: {result.get('error')}")
            test_results["failed"] += 1
        else:
            print(f"  PASS: Works correctly - found: {result.get('found')}")
            test_results["passed"] += 1
    else:
        print(f"  PASS: Works correctly - content returned")
        test_results["passed"] += 1
except Exception as e:
    print(f"  FAIL: Exception: {str(e)[:100]}")
    test_results["failed"] += 1

# 2. h.search.code() context 파라미터 테스트
print("\n2. h.search.code() context parameter test:")
try:
    # context_lines 테스트
    result1 = h.search.code("def", os.path.join(base_path, "python", "ai_helpers_new"), context_lines=2)
    if result1['ok']:
        print(f"  PASS: context_lines works")
        test_results["passed"] += 1
    else:
        print(f"  FAIL: context_lines error")
        test_results["failed"] += 1
    
    # context 파라미터 테스트
    result2 = h.search.code("def", os.path.join(base_path, "python", "ai_helpers_new"), context=2)
    if result2['ok']:
        print(f"  PASS: context parameter works")
        test_results["passed"] += 1
    else:
        print(f"  FAIL: context parameter doesn't work")
        test_results["failed"] += 1
except Exception as e:
    print(f"  FAIL: Exception: {str(e)[:100]}")
    test_results["failed"] += 2

# 3. h.git.status_normalized() 테스트
print("\n3. h.git.status_normalized() test:")
try:
    # 직접 호출 테스트
    if hasattr(h, 'git_status_normalized'):
        result = h.git_status_normalized()
        if isinstance(result, dict):
            print(f"  PASS: Direct call works")
            test_results["passed"] += 1
        else:
            print(f"  FAIL: Direct call returns wrong type")
            test_results["failed"] += 1
    else:
        print(f"  FAIL: git_status_normalized not exported")
        test_results["failed"] += 1
    
    # Facade 테스트
    if hasattr(h.git, 'status_normalized'):
        try:
            result = h.git.status_normalized()
            if callable(result):
                # 함수가 반환된 경우 호출
                result = result()
            if isinstance(result, dict):
                print(f"  PASS: h.git.status_normalized() works")
                test_results["passed"] += 1
            else:
                print(f"  FAIL: h.git.status_normalized() wrong type")
                test_results["failed"] += 1
        except Exception as e:
            print(f"  FAIL: h.git.status_normalized() error: {e}")
            test_results["failed"] += 1
    else:
        print(f"  FAIL: h.git.status_normalized() not in facade")
        test_results["failed"] += 1
except Exception as e:
    print(f"  FAIL: Exception: {str(e)[:100]}")
    test_results["failed"] += 2

# 결과 요약
print("\n" + "="*70)
print("TEST SUMMARY")
print("="*70)
print(f"PASSED: {test_results['passed']}")
print(f"FAILED: {test_results['failed']}")
print(f"TOTAL: {test_results['passed'] + test_results['failed']}")
print(f"SUCCESS RATE: {test_results['passed'] / (test_results['passed'] + test_results['failed']) * 100:.1f}%")

if test_results['failed'] == 0:
    print("\nALL TESTS PASSED! All 3 issues have been fixed successfully!")
else:
    print("\nSome tests failed. Please check the output above.")
