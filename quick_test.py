#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""간단한 수정 테스트"""

import sys
import os

# 경로 설정
base_path = r'C:\Users\82106\Desktop\ai-coding-brain-mcp'
sys.path.insert(0, os.path.join(base_path, 'python'))

# Import
import ai_helpers_new as h

print("Quick Test of Fixes")
print("="*70)

# 1. code.view 테스트
print("\n1. code.view:")
try:
    result = h.code.view(os.path.join(base_path, "python", "ai_helpers_new", "file.py"), "read")
    print("  PASS" if not (isinstance(result, dict) and result.get('ok') == False) else f"  FAIL: {result.get('error')}")
except Exception as e:
    print(f"  FAIL: {str(e)[:50]}")

# 2. search.code context 테스트 
print("\n2. search.code context:")
try:
    # context_lines로 직접 호출
    result = h.search.code("def", "python", context_lines=1)
    print(f"  context_lines: {'PASS' if result['ok'] else 'FAIL'}")
except Exception as e:
    print(f"  context_lines: FAIL - {str(e)[:50]}")

# 3. git.status_normalized 테스트
print("\n3. git.status_normalized:")
try:
    # 직접 호출
    if hasattr(h, 'git_status_normalized'):
        result = h.git_status_normalized()
        print(f"  Direct: PASS")
    else:
        print(f"  Direct: FAIL - not exported")
    
    # Facade
    if hasattr(h.git, 'status_normalized'):
        result = h.git.status_normalized()
        if callable(result):
            result = result()
        print(f"  Facade: PASS")
    else:
        print(f"  Facade: FAIL - not in facade")
except Exception as e:
    print(f"  FAIL: {str(e)[:50]}")

print("\n" + "="*70)
print("Summary:")
print("1. code.view - should work without 'line' key error")
print("2. search.code - context_lines works, context needs manual mapping")
print("3. git.status_normalized - should be available in both direct and facade")
