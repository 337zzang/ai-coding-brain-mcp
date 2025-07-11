#!/usr/bin/env python3
"""AI Helpers Export 시스템 테스트"""

import sys
import os

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'python'))

print("=== AI Helpers Export 시스템 테스트 ===\n")

try:
    # ai_helpers 모듈 import
    import ai_helpers
    print("✅ ai_helpers 모듈 import 성공")
    
    # search_code 함수 확인
    print("\n🔍 search_code 함수 확인:")
    print(f"  - 'search_code' in dir(ai_helpers): {'search_code' in dir(ai_helpers)}")
    print(f"  - hasattr(ai_helpers, 'search_code'): {hasattr(ai_helpers, 'search_code')}")
    
    if hasattr(ai_helpers, 'search_code'):
        print("  - search_code 함수 시그니처:", ai_helpers.search_code.__doc__)
    
    # __all__ 확인
    print(f"\n📋 __all__ 정의 항목 수: {len(ai_helpers.__all__)}")
    
    # search 관련 함수들
    search_funcs = [name for name in ai_helpers.__all__ if 'search' in name]
    print(f"\n🔍 search 관련 함수들 ({len(search_funcs)}개):")
    for name in sorted(search_funcs):
        print(f"  - {name}")
    
    # 실제 export된 함수 확인
    exported = [name for name in ai_helpers.__all__ if hasattr(ai_helpers, name)]
    not_exported = [name for name in ai_helpers.__all__ if not hasattr(ai_helpers, name)]
    
    print(f"\n✅ 성공적으로 export된 함수: {len(exported)}개")
    if not_exported:
        print(f"❌ Export 실패한 함수 ({len(not_exported)}개):")
        for name in not_exported[:10]:  # 처음 10개만
            print(f"  - {name}")
    
    # HelpersWrapper 테스트
    print("\n=== HelpersWrapper 테스트 ===")
    from helpers_wrapper import HelpersWrapper
    
    helpers = HelpersWrapper(ai_helpers)
    print("✅ HelpersWrapper 생성 성공")
    
    # search_code 테스트
    print("\n🧪 search_code 함수 실행 테스트:")
    try:
        result = helpers.search_code("class HelpersWrapper", "*.py")
        print(f"  - 실행 결과: {type(result)}")
        if hasattr(result, 'ok'):
            print(f"  - 성공 여부: {result.ok}")
            if result.ok:
                data = result.get_data()
                print(f"  - 결과 타입: {type(data)}")
                if isinstance(data, dict):
                    print(f"  - 찾은 파일 수: {len(data)}")
    except Exception as e:
        print(f"  ❌ 에러: {e}")
    
    # list_functions 테스트
    print("\n🧪 list_functions 함수 실행 테스트:")
    try:
        result = helpers.list_functions()
        if hasattr(result, 'ok') and result.ok:
            data = result.get_data()
            print(f"  - 총 함수 수: {data.get('total_count', 0)}")
    except Exception as e:
        print(f"  ❌ 에러: {e}")
        
except Exception as e:
    print(f"\n❌ 테스트 실패: {e}")
    import traceback
    traceback.print_exc()
