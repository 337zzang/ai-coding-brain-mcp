"""
BrowserManager 단위 테스트
싱글톤 패턴, 스레드 안전성, 인스턴스 관리 검증

작성일: 2025-08-02
"""
import pytest
import threading
import time
from unittest.mock import Mock
from python.api.web_automation_manager import BrowserManager, browser_manager


class TestBrowserManager:
    """BrowserManager 단위 테스트"""

    def setup_method(self):
        """각 테스트 전 상태 초기화"""
        browser_manager.clear_all()

    def test_singleton_pattern(self):
        """싱글톤 패턴 검증"""
        manager1 = BrowserManager()
        manager2 = BrowserManager()

        assert manager1 is manager2
        assert manager1 is browser_manager

    def test_basic_instance_management(self):
        """기본 인스턴스 관리 기능"""
        # Mock 브라우저 인스턴스
        mock_browser = Mock()
        mock_browser.name = "TestBrowser"

        # 인스턴스 설정
        browser_manager.set_instance(mock_browser, "test_project")

        # 인스턴스 조회
        retrieved = browser_manager.get_instance("test_project")
        assert retrieved is mock_browser

        # 없는 프로젝트 조회
        assert browser_manager.get_instance("non_existent") is None

    def test_instance_removal(self):
        """인스턴스 제거 기능"""
        mock_browser = Mock()

        # 인스턴스 추가 후 제거
        browser_manager.set_instance(mock_browser, "temp_project")
        assert browser_manager.get_instance("temp_project") is not None

        # 제거
        result = browser_manager.remove_instance("temp_project")
        assert result is True
        assert browser_manager.get_instance("temp_project") is None

        # 없는 인스턴스 제거 시도
        result = browser_manager.remove_instance("non_existent")
        assert result is False

    def test_list_instances(self):
        """인스턴스 목록 조회"""
        # 여러 인스턴스 추가
        browser_manager.set_instance(Mock(), "project1")
        browser_manager.set_instance(Mock(), "project2")

        instances = browser_manager.list_instances()
        assert len(instances) == 2

        project_names = [inst["project"] for inst in instances]
        assert "project1" in project_names
        assert "project2" in project_names

    def test_thread_safety(self):
        """스레드 안전성 검증"""
        results = []
        errors = []

        def create_instance(project_id):
            try:
                mock = Mock()
                mock.id = project_id
                browser_manager.set_instance(mock, f"thread_{project_id}")

                # 조회
                retrieved = browser_manager.get_instance(f"thread_{project_id}")
                if retrieved and retrieved.id == project_id:
                    results.append(True)
                else:
                    results.append(False)
            except Exception as e:
                errors.append(str(e))

        # 10개 스레드 동시 실행
        threads = []
        for i in range(10):
            t = threading.Thread(target=create_instance, args=(i,))
            threads.append(t)
            t.start()

        # 모든 스레드 대기
        for t in threads:
            t.join()

        # 검증
        assert len(errors) == 0, f"Thread errors: {errors}"
        assert all(results), "Some threads failed"
        assert len(browser_manager.list_instances()) == 10

    def test_stats(self):
        """통계 기능 검증"""
        # 초기 상태
        stats = browser_manager.get_stats()
        assert stats["active_instances"] == 0
        assert stats["total_created"] == 0

        # 인스턴스 추가
        browser_manager.set_instance(Mock(), "proj1")
        browser_manager.set_instance(Mock(), "proj2")

        stats = browser_manager.get_stats()
        assert stats["active_instances"] == 2
        assert stats["total_created"] == 2
        assert len(stats["projects"]) == 2

        # 하나 제거
        browser_manager.remove_instance("proj1")
        stats = browser_manager.get_stats()
        assert stats["active_instances"] == 1
        assert stats["total_created"] == 2  # 총 생성 수는 유지

    def test_clear_all(self):
        """전체 정리 기능"""
        # 여러 인스턴스 추가
        for i in range(5):
            browser_manager.set_instance(Mock(), f"proj_{i}")

        # 전체 정리
        count = browser_manager.clear_all()
        assert count == 5
        assert len(browser_manager.list_instances()) == 0

        # 메타데이터는 유지되지만 비활성 상태
        stats = browser_manager.get_stats()
        assert stats["active_instances"] == 0
        assert stats["total_created"] == 5


class TestHelperIntegration:
    """헬퍼 함수 통합 테스트"""

    def setup_method(self):
        """테스트 환경 준비"""
        browser_manager.clear_all()

    def test_helper_functions_with_manager(self):
        """수정된 헬퍼 함수 동작 검증"""
        from python.api.web_automation_helpers import _get_web_instance, _set_web_instance

        # 초기 상태
        assert _get_web_instance() is None

        # Mock 인스턴스 설정
        mock_browser = Mock()
        mock_browser.name = "HelperTest"

        _set_web_instance(mock_browser)

        # BrowserManager를 통해 조회
        assert browser_manager.get_instance("default") is mock_browser

        # 헬퍼 함수로도 조회
        assert _get_web_instance() is mock_browser

        # 제거
        _set_web_instance(None)
        assert _get_web_instance() is None
        assert browser_manager.get_instance("default") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
