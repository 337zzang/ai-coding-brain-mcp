#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""문법 검사 스크립트"""
import ast
import os
import sys

def check_syntax(file_path):
    """파일의 Python 문법을 검사"""
    print(f"\n[CHECK] Checking: {file_path}")
    if not os.path.exists(file_path):
        print(f"  [FAIL] File does not exist!")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        print(f"  [PASS] Syntax check passed!")
        return True
    except SyntaxError as e:
        print(f"  [FAIL] Syntax error!")
        print(f"     Line {e.lineno}: {e.msg}")
        if e.text:
            print(f"     Text: {e.text.rstrip()}")
            if e.offset:
                print(f"     Position: {' ' * (e.offset-1)}^")
        return False
    except Exception as e:
        print(f"  [FAIL] Other error: {type(e).__name__}: {e}")
        return False

# 검사할 파일들
files_to_check = [
    'python/json_repl_session.py',
    'python/git_version_manager.py',
    'python/enhanced_flow.py'
]

print("=" * 60)
print("Python Syntax Check Tool")
print("=" * 60)

all_passed = True
for file_path in files_to_check:
    if not check_syntax(file_path):
        all_passed = False

print("\n" + "=" * 60)
if all_passed:
    print("[PASS] All files passed syntax check!")
else:
    print("[FAIL] Some files have syntax errors!")
print("=" * 60)
