#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
수정된 flow_project_with_workflow 함수 테스트 (인코딩 문제 해결)
"""
import sys
import os

# UTF-8 출력 강제
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 경로 추가
sys.path.insert(0, r'C:\Users\Administrator\Desktop\ai-coding-brain-mcp\python')

print("=" * 70)
print("Modified flow_project_with_workflow Function Test")
print("=" * 70)

try:
    import ai_helpers_new as h
    
    # 현재 디렉토리
    original_dir = os.getcwd()
    print(f"\nStart directory: {original_dir}")
    
    # goodwill 프로젝트로 전환
    print("\nSwitching to goodwill project...")
    print("-" * 40)
    
    # stdout 일시적으로 비활성화 (이모지 출력 방지)
    import contextlib
    with contextlib.redirect_stdout(None):
        result = h.flow_project_with_workflow("goodwill", auto_read_docs=False)
    
    # 결과 확인
    print(f"\nExecution complete")
    print(f"Status: {'SUCCESS' if result.get('ok') else 'FAILED'}")
    
    if result.get('ok'):
        data = result.get('data', {})
        
        print("\nTest Results:")
        print(f"  1. Directory changed: {'YES' if os.getcwd() != original_dir else 'NO'}")
        print(f"     Before: {original_dir}")
        print(f"     After: {os.getcwd()}")
        print(f"  2. current_dir key: {'EXISTS' if 'current_dir' in data else 'MISSING'}")
        print(f"  3. cwd key: {'EXISTS' if 'cwd' in data else 'MISSING'}")
        print(f"  4. Flow info: {'EXISTS' if data.get('flow') else 'MISSING'}")
        if data.get('flow'):
            print(f"     Plan count: {data['flow'].get('count', 0)}")
        print(f"  5. Git changes key: {'EXISTS' if data.get('git', {}).get('changes') is not None else 'MISSING'}")
        print(f"  6. Version: {data.get('_version', 'N/A')}")
        print(f"  7. Modified date: {data.get('_modified', 'N/A')}")
        
        # 성공 여부 판단
        all_passed = (
            os.getcwd() != original_dir and  # 디렉토리 변경됨
            'current_dir' in data and  # current_dir 키 있음
            'cwd' in data and  # cwd 키 있음
            data.get('_version') == '1.1.0'  # 버전 정보 있음
        )
        
        if all_passed:
            print("\n*** ALL CRITICAL ISSUES RESOLVED! ***")
        else:
            print("\n*** Some issues remain ***")
    else:
        print(f"\nError: {result.get('error', 'Unknown error')}")
        
except Exception as e:
    print(f"\nTest failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("Test complete!")
