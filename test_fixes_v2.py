#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""수정사항 테스트 스크립트"""

import sys
import os

# 경로 추가
base_path = r'C:\Users\82106\Desktop\ai-coding-brain-mcp'
sys.path.insert(0, os.path.join(base_path, 'python'))

# Import
import ai_helpers_new as h

print("="*70)
print("3 fixes final test")
print("="*70)

# 절대 경로 사용
test_file = os.path.join(base_path, "python", "ai_helpers_new", "file.py")

# 1. h.code.view() 테스트
print("\n1. h.code.view() test:")
try:
    result = h.code.view(test_file, "read")
    if isinstance(result, dict):
        if result.get('ok') == False:
            print(f"  FAIL: {result.get('error')}")
        elif result.get('found') == False:
            print(f"  PASS: Function works, target not found")
        else:
            print(f"  PASS: Function works - found: {result.get('found')}")
    else:
        print(f"  PASS: Function works - content returned ({len(result)} chars)")
except Exception as e:
    print(f"  FAIL: Exception: {str(e)[:100]}")

# 2. h.search.code() context 테스트
print("\n2. h.search.code() context parameter test:")
try:
    # context 대신 context_lines 사용
    result = h.search.code("def", os.path.join(base_path, "python", "ai_helpers_new"), context_lines=2)
    if result['ok']:
        print(f"  PASS: Works with context_lines - {len(result.get('data', []))} results")
    else:
        print(f"  FAIL: {result.get('error')}")
        
    # context 파라미터 테스트
    result2 = h.search.code("def", os.path.join(base_path, "python", "ai_helpers_new"), context=2)
    if result2['ok']:
        print(f"  PASS: Works with context too - {len(result2.get('data', []))} results")
    else:
        print(f"  FAIL with context: {result2.get('error')}")
except Exception as e:
    print(f"  FAIL: Exception: {str(e)[:100]}")

# 3. h.git.status_normalized() 테스트
print("\n3. h.git.status_normalized() test:")
try:
    # __init__.py에서 import 확인
    if hasattr(h, 'git_status_normalized'):
        result = h.git_status_normalized()
        if isinstance(result, dict):
            print(f"  PASS: Function available and works")
            if 'branch' in result:
                print(f"     - branch: {result.get('branch')}")
    else:
        print(f"  FAIL: git_status_normalized not exported in __init__.py")
        
    # facade에서 확인
    if hasattr(h.git, 'status_normalized'):
        try:
            result = h.git.status_normalized()
            print(f"  PASS: h.git.status_normalized() exists and works")
        except:
            print(f"  FAIL: h.git.status_normalized() exists but fails")
    else:
        print(f"  FAIL: h.git.status_normalized() not in facade")
except Exception as e:
    print(f"  FAIL: Exception: {str(e)[:100]}")

print("\n" + "="*70)
print("Test Summary:")
print("="*70)
print("Expected fixes:")
print("1. h.code.view() - should handle missing 'line' key")
print("2. h.search.code() - should accept 'context' parameter")
print("3. h.git.status_normalized() - should be available in facade")
