import sys
import os

# ai_helpers_new 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

print("=== O3 헬퍼 함수 테스트 ===\n")

try:
    import ai_helpers_new as h
    
    # 1. 함수 존재 확인
    print("1. 함수 존재 확인:")
    funcs = ['ask_o3_practical', 'O3ContextBuilder', 'quick_o3_context']
    for func_name in funcs:
        if hasattr(h, func_name):
            print(f"  ✅ {func_name} - 존재함")
        else:
            print(f"  ❌ {func_name} - 없음")
    
    # 2. O3ContextBuilder 테스트
    print("\n2. O3ContextBuilder 테스트:")
    builder = h.O3ContextBuilder()
    print(f"  ✅ 빌더 생성 성공: {type(builder)}")
    
    # 메서드 테스트
    builder.add_context("테스트", "테스트 내용")
    builder.add_error("TypeError: test error", "test.py", 10)
    context = builder.build()
    print(f"  ✅ 컨텍스트 생성: {len(context)}자")
    print(f"\n  생성된 컨텍스트:")
    print("-" * 50)
    print(context)
    print("-" * 50)
    
    # 3. quick_o3_context 테스트
    print("\n3. quick_o3_context 테스트:")
    quick_builder = h.quick_o3_context("NameError: name 'x' is not defined", __file__, 20)
    quick_context = quick_builder.build()
    print(f"  ✅ 빠른 컨텍스트 생성: {len(quick_context)}자")
    
    # 4. ask_o3_practical 파라미터 확인
    print("\n4. ask_o3_practical 시그니처:")
    import inspect
    sig = inspect.signature(h.ask_o3_practical)
    print(f"  {sig}")
    
    print("\n✅ 모든 테스트 통과!")
    
except Exception as e:
    print(f"\n❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
