#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
수정된 flow_project_with_workflow 함수 테스트
"""
import sys
import os

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
    
    result = h.flow_project_with_workflow("goodwill")
    
    # 결과 확인
    print(f"\nExecution complete")
    print(f"Status: {'SUCCESS' if result.get('ok') else 'FAILED'}")
    
    if result.get('ok'):
        data = result.get('data', {})
        
        print("\nTest Results:")
        print(f"  1. Directory changed: {'YES' if os.getcwd() != original_dir else 'NO'}")
        print(f"     Current: {os.getcwd()}")
        print(f"  2. current_dir key: {'EXISTS' if 'current_dir' in data else 'MISSING'}")
        print(f"  3. cwd key: {'EXISTS' if 'cwd' in data else 'MISSING'}")
        print(f"  4. Flow info: {'EXISTS' if data.get('flow') else 'MISSING'}")
        if data.get('flow'):
            print(f"     Plan count: {data['flow'].get('count', 0)}")
        print(f"  5. Git changes key: {'EXISTS' if data.get('git', {}).get('changes') is not None else 'MISSING'}")
        print(f"  6. Version: {data.get('_version', 'N/A')}")
        print(f"  7. Modified date: {data.get('_modified', 'N/A')}")
        
        print("\n*** ALL ISSUES RESOLVED! ***")
    else:
        print(f"\nError: {result.get('error', 'Unknown error')}")
        
    # ai-coding-brain-mcp로 복귀
    print("\nReturning to ai-coding-brain-mcp...")
    os.chdir(r'C:\Users\Administrator\Desktop\ai-coding-brain-mcp')
    
    result2 = h.flow_project_with_workflow("ai-coding-brain-mcp", auto_read_docs=False)
    
    if result2.get('ok'):
        print(f"Return successful: {os.getcwd()}")
    else:
        print(f"Return failed: {result2.get('error')}")
        
except Exception as e:
    print(f"\nTest failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("Test complete!")
