"""
HelpersWrapper 테스트
특히 list_functions() 오류 해결 확인
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python.helpers_wrapper import HelpersWrapper
from python.ai_helpers import AIHelpers
from ai_helpers.helper_result import HelperResult


def test_list_functions_binding():
    """list_functions 메서드가 올바르게 바인딩되는지 테스트"""
    print("🧪 list_functions 바인딩 테스트")
    
    # HelpersWrapper 인스턴스 생성
    ai_helpers = AIHelpers()
    wrapper = HelpersWrapper(ai_helpers)
    
    # 1. __dict__에 존재하는지 확인
    assert 'list_functions' in wrapper.__dict__, "list_functions가 __dict__에 없음"
    print("✅ list_functions가 __dict__에 존재")
    
    # 2. 바운드 메서드인지 확인
    method = wrapper.__dict__['list_functions']
    assert hasattr(method, '__self__'), "바운드 메서드가 아님"
    print("✅ 바운드 메서드로 올바르게 설정됨")
    
    # 3. 호출 가능한지 확인
    try:
        result = wrapper.list_functions()
        assert isinstance(result, HelperResult), "HelperResult를 반환하지 않음"
        assert result.ok, f"호출 실패: {result.error}"
        print("✅ 정상적으로 호출 가능")
    except TypeError as e:
        if "helpers_instance" in str(e):
            raise AssertionError("여전히 helpers_instance 인자 오류 발생")
        raise
    
    # 4. 데이터 확인
    data = result.get_data()
    assert 'total_count' in data, "total_count 필드 없음"
    assert 'functions' in data, "functions 필드 없음"
    assert data['total_count'] > 0, "함수가 하나도 없음"
    print(f"✅ {data['total_count']}개 함수 발견")
    
    return True


def test_other_override_methods():
    """다른 override 메서드들도 올바르게 바인딩되는지 테스트"""
    print("\n🧪 다른 override 메서드 테스트")
    
    ai_helpers = AIHelpers()
    wrapper = HelpersWrapper(ai_helpers)
    
    override_methods = ['workflow', 'read_file', 'list_functions']
    
    for method_name in override_methods:
        assert method_name in wrapper.__dict__, f"{method_name}이 __dict__에 없음"
        method = wrapper.__dict__[method_name]
        assert hasattr(method, '__self__'), f"{method_name}이 바운드 메서드가 아님"
        print(f"✅ {method_name}: 올바르게 바인딩됨")
    
    return True


def test_repeated_calls():
    """반복 호출 시 안정성 테스트"""
    print("\n🧪 반복 호출 안정성 테스트")
    
    ai_helpers = AIHelpers()
    wrapper = HelpersWrapper(ai_helpers)
    
    for i in range(5):
        try:
            result = wrapper.list_functions()
            assert result.ok, f"호출 #{i+1} 실패"
        except Exception as e:
            raise AssertionError(f"호출 #{i+1}에서 오류: {e}")
    
    print("✅ 5회 반복 호출 모두 성공")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("HelpersWrapper 영구적 해결 테스트")
    print("=" * 60)
    
    tests = [
        test_list_functions_binding,
        test_other_override_methods,
        test_repeated_calls
    ]
    
    all_passed = True
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ {test.__name__} 실패: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 모든 테스트 통과! list_functions() 오류가 영구적으로 해결되었습니다.")
    else:
        print("❌ 일부 테스트 실패")
    print("=" * 60)
