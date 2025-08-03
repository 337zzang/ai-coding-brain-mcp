
# 웹 자동화 통합 테스트
import sys
sys.path.insert(0, 'python')

try:
    # 모듈 import 테스트
    from api.web_automation_helpers import _get_web_instance, _set_web_instance
    from api.web_automation_manager import BrowserManager
    print("✅ 모듈 import 성공")

    # BrowserManager 싱글톤 테스트
    manager1 = BrowserManager()
    manager2 = BrowserManager()
    assert manager1 is manager2, "싱글톤 패턴이 작동해야 함"
    print("✅ BrowserManager 싱글톤 테스트 통과")

    # Mock 브라우저 클래스
    class MockBrowser:
        def __init__(self, name):
            self.name = name
            self.stopped = False

        def stop(self):
            self.stopped = True

    # _set_web_instance 테스트
    mock = MockBrowser("test")
    _set_web_instance(mock)

    # _get_web_instance 테스트
    retrieved = _get_web_instance()
    assert retrieved is mock, "같은 인스턴스를 반환해야 함"
    print("✅ get/set_web_instance 테스트 통과")

    # BrowserManager를 통한 직접 접근도 작동
    assert manager1.get_instance("default") is mock, "BrowserManager도 같은 인스턴스 반환"
    print("✅ BrowserManager 통합 테스트 통과")

    # 전역 변수가 더 이상 사용되지 않는지 확인
    import api.web_automation_helpers as helpers
    assert not hasattr(helpers, '_web_instance'), "전역 변수가 제거되어야 함"
    print("✅ 전역 변수 제거 확인")

    print("\n모든 통합 테스트 통과! ✅✅✅")

except Exception as e:
    print(f"❌ 테스트 실패: {e}")
    import traceback
    traceback.print_exc()
