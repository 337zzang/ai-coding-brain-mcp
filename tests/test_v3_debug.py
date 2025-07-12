#!/usr/bin/env python
"""V3 전환 테스트 스크립트"""
import sys
import traceback

print("=== V3 전환 디버깅 ===\n")

# 1. V3 직접 테스트
print("1. V3 모듈 직접 import:")
try:
    from python.workflow.v3.dispatcher import execute_workflow_command
    print("   ✅ V3 dispatcher import 성공")
    
    result = execute_workflow_command("/status")
    print(f"   ✅ V3 실행 성공: {result.get('success')}")
except Exception as e:
    print(f"   ❌ V3 에러: {e}")
    traceback.print_exc()

# 2. HelpersWrapper 테스트
print("\n2. HelpersWrapper import:")
try:
    from helpers_wrapper import HelpersWrapper
    print("   ✅ HelpersWrapper import 성공")
    
    helpers = HelpersWrapper('test')
    print("   ✅ HelpersWrapper 생성 성공")
    
    result = helpers.workflow("/status")
    print(f"   ✅ workflow 실행 성공: {result.ok}")
except Exception as e:
    print(f"   ❌ HelpersWrapper 에러: {e}")
    traceback.print_exc()

# 3. V2 참조 찾기
print("\n3. V2 참조 확인:")
import os
import ast

def find_v2_imports(file_path):
    """파일에서 v2 import 찾기"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        v2_imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and 'v2' in str(node.module):
                    v2_imports.append(f"Line {node.lineno}: from {node.module} import ...")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if 'v2' in alias.name:
                        v2_imports.append(f"Line {node.lineno}: import {alias.name}")
        
        return v2_imports
    except:
        return []

# Python 디렉토리의 주요 파일들 검사
files_to_check = [
    "python/helpers_wrapper.py",
    "python/__init__.py",
    "python/ai_helpers/__init__.py",
    "python/workflow/__init__.py",
    "python/workflow/v3/__init__.py"
]

for file_path in files_to_check:
    if os.path.exists(file_path):
        v2_refs = find_v2_imports(file_path)
        if v2_refs:
            print(f"\n   {file_path}:")
            for ref in v2_refs:
                print(f"     {ref}")
        else:
            print(f"   {file_path}: ✅ V2 참조 없음")

print("\n=== 테스트 완료 ===")
