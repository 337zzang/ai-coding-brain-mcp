# -*- coding: utf-8 -*-
import sys
import os

# 프로젝트 루트에서 실행
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(project_root)

print("=== O3 Helper Functions Test ===\n")
print(f"Working directory: {os.getcwd()}")

try:
    # ai_helpers_new import
    sys.path.insert(0, os.path.join(project_root, 'python'))
    import ai_helpers_new as h
    
    # 1. Check functions exist
    print("\n1. Function existence check:")
    funcs = ['ask_o3_practical', 'O3ContextBuilder', 'quick_o3_context']
    all_exist = True
    for func_name in funcs:
        if hasattr(h, func_name):
            print(f"  [OK] {func_name} - exists")
        else:
            print(f"  [FAIL] {func_name} - not found")
            all_exist = False
    
    if not all_exist:
        print("\nSome functions are missing. Checking available O3 functions:")
        o3_funcs = [attr for attr in dir(h) if 'o3' in attr.lower()]
        print(f"Available O3 functions: {o3_funcs}")
        sys.exit(1)
    
    # 2. Test O3ContextBuilder
    print("\n2. O3ContextBuilder test:")
    builder = h.O3ContextBuilder()
    print(f"  [OK] Builder created: {type(builder)}")
    
    # Test methods
    builder.add_context("Test", "Test content")
    builder.add_error("TypeError: test error", "test.py", 10)
    context = builder.build()
    print(f"  [OK] Context created: {len(context)} chars")
    
    # 3. Test quick_o3_context
    print("\n3. quick_o3_context test:")
    quick_builder = h.quick_o3_context("NameError: name 'x' is not defined", __file__, 20)
    quick_context = quick_builder.build()
    print(f"  [OK] Quick context created: {len(quick_context)} chars")
    
    print("\n[SUCCESS] All tests passed!")
    
except Exception as e:
    print(f"\n[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()
