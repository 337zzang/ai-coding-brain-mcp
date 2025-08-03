#!/usr/bin/env python3
"""LazyHelperProxy 수정 테스트 스크립트"""

import sys
import os

# 프로젝트 경로 추가
if __file__.startswith('C:\\Users\\82106\\Desktop\\ai-coding-brain-mcp'):
    project_root = 'C:\\Users\\82106\\Desktop\\ai-coding-brain-mcp'
else:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
python_path = os.path.join(project_root, 'python')
sys.path.insert(0, python_path)

print(f"Python path added: {python_path}")
print("=== LazyHelperProxy Test ===\n")

# json_repl_session 임포트하여 LazyHelperProxy 테스트
try:
    # 파일 존재 확인
    json_repl_path = os.path.join(python_path, 'json_repl_session.py')
    print(f"Checking file: {json_repl_path}")
    print(f"File exists: {os.path.exists(json_repl_path)}")
    
    from json_repl_session import LazyHelperProxy
    print("[OK] LazyHelperProxy import success")
    
    # 새로운 LazyHelperProxy 인스턴스 생성
    test_h = LazyHelperProxy('test_helpers')
    print("[OK] LazyHelperProxy instance created")
    
    # read 함수 테스트
    print("\n--- Testing h.read function ---")
    try:
        read_func = test_h.read
        print(f"  [OK] h.read access success: {type(read_func)}")
        
        # 캐싱 확인
        if hasattr(test_h, 'read'):
            print("  [OK] Caching success: hasattr(h, 'read') = True")
        else:
            print("  [FAIL] Caching failed: hasattr(h, 'read') = False")
    except AttributeError as e:
        print(f"  [FAIL] h.read access failed: {e}")
    
    # 다른 함수들도 테스트
    test_functions = ['write', 'git_status', 'flow_project_with_workflow', 'get_current_project']
    print("\n--- Testing other functions ---")
    for func_name in test_functions:
        try:
            func = getattr(test_h, func_name)
            print(f"  [OK] h.{func_name}: Success")
        except AttributeError:
            print(f"  [FAIL] h.{func_name}: Failed")
    
    print("\n=== Test completed! ===")
    
except Exception as e:
    print(f"[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()
