import sys
sys.path.insert(0, 'python')

from api.web_automation_manager import BrowserManager

def test_close_instance():
    """close_instance 메서드 테스트"""
    manager = BrowserManager()

    # 1. 존재하지 않는 인스턴스 종료 시도
    result = manager.close_instance("non_existent")
    assert result == False, "존재하지 않는 인스턴스는 False 반환해야 함"
    print("✅ Test 1 통과: 존재하지 않는 인스턴스 처리")

    # 2. Mock 인스턴스로 테스트
    class MockBrowser:
        def __init__(self):
            self.stopped = False

        def stop(self):
            self.stopped = True

    # Mock 인스턴스 추가
    mock_browser = MockBrowser()
    manager.set_instance(mock_browser, "test_project")

    # 인스턴스 존재 확인
    assert manager.get_instance("test_project") is not None, "인스턴스가 추가되어야 함"
    print("✅ Test 2 통과: Mock 인스턴스 추가")

    # close_instance 호출
    result = manager.close_instance("test_project")
    assert result == True, "close_instance는 True 반환해야 함"
    assert mock_browser.stopped == True, "브라우저가 종료되어야 함"
    assert manager.get_instance("test_project") is None, "인스턴스가 제거되어야 함"
    print("✅ Test 3 통과: 인스턴스 종료 및 제거")

    print("\n모든 테스트 통과! ✅")

if __name__ == "__main__":
    test_close_instance()
