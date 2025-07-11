#!/usr/bin/env python3
import sys
import os

# 경로 설정
sys.path.insert(0, 'python')

print("AI Helpers Import 테스트")
print("=" * 50)

try:
    import ai_helpers
    print("✅ ai_helpers import 성공")
    
    # 주요 함수 확인
    functions = [
        'search_code', 'search_files_advanced', 'search_code_content',
        'workflow', 'read_file', 'git_status'
    ]
    
    print("\n함수 확인:")
    for func in functions:
        if hasattr(ai_helpers, func):
            print(f"  ✅ {func}")
        else:
            print(f"  ❌ {func}")
            
    print(f"\n총 export 함수 수: {len(ai_helpers.__all__)}")
    
except Exception as e:
    print(f"❌ Import 실패: {e}")
    import traceback
    traceback.print_exc()
