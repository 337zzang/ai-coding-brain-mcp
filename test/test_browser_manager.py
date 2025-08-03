"""
BrowserManager 단위 테스트
- 싱글톤 패턴 동작 검증
- list_instances 메서드 검증
- 인스턴스 관리 기능 검증
"""
import unittest
import sys
sys.path.insert(0, 'python')

from api.web_automation_manager import BrowserManager


class TestBrowserManager(unittest.TestCase):
    """BrowserManager 단위 테스트"""

    def setUp(self):
        """테스트 전 초기화"""
        # BrowserManager 인스턴스 가져오기 (싱글톤)
        self.manager = BrowserManager()
        # 모든 인스턴스 제거
        for instance_info in self.manager.list_instances():
            try:
                self.manager.remove_instance(instance_info['project'])
            except:
                pass

    def test_singleton_pattern(self):
        """싱글톤 패턴 검증"""
        manager1 = BrowserManager()
        manager2 = BrowserManager()

        # 동일한 인스턴스여야 함
        self.assertIs(manager1, manager2)
        print("✅ 싱글톤 패턴 검증 통과")

    def test_list_instances_empty(self):
        """빈 인스턴스 목록 검증"""
        instances = self.manager.list_instances()

        # 리스트여야 함
        self.assertIsInstance(instances, list)
        print("✅ list_instances가 리스트 반환 확인")

    def test_list_instances_with_data(self):
        """인스턴스 추가 후 목록 검증"""
        # 메타데이터 직접 추가 (실제 브라우저 생성 없이)
        self.manager._instance_metadata["test_project"] = {
            "active": True,
            "type": "test",
            "created_at": "2025-08-03"
        }

        instances = self.manager.list_instances()

        # 1개가 있어야 함
        self.assertEqual(len(instances), 1)
        # 프로젝트 이름 확인
        self.assertEqual(instances[0]["project"], "test_project")
        # 타입 확인
        self.assertEqual(instances[0]["type"], "test")
        print("✅ 인스턴스 추가 후 목록 검증 통과")

    def test_list_instances_only_active(self):
        """활성 인스턴스만 반환하는지 검증"""
        # 활성 인스턴스
        self.manager._instance_metadata["active_project"] = {
            "active": True,
            "type": "active"
        }
        # 비활성 인스턴스
        self.manager._instance_metadata["inactive_project"] = {
            "active": False,
            "type": "inactive"
        }

        instances = self.manager.list_instances()

        # 활성 인스턴스만 반환되어야 함
        self.assertEqual(len(instances), 1)
        self.assertEqual(instances[0]["project"], "active_project")
        print("✅ 활성 인스턴스 필터링 검증 통과")

    def test_no_attribute_error(self):
        """AttributeError가 발생하지 않는지 검증 (.h.append 버그 수정 확인)"""
        try:
            # 여러 인스턴스 추가
            for i in range(5):
                self.manager._instance_metadata[f"project_{i}"] = {
                    "active": True,
                    "type": f"type_{i}"
                }

            # list_instances 호출
            instances = self.manager.list_instances()

            # 5개가 반환되어야 함
            self.assertEqual(len(instances), 5)
            print("✅ .h.append 버그 수정 확인 - AttributeError 없이 정상 동작")

        except AttributeError as e:
            self.fail(f"AttributeError 발생: {e}")

    def tearDown(self):
        """테스트 후 정리"""
        # 메타데이터 정리
        self.manager._instance_metadata.clear()


if __name__ == "__main__":
    # 테스트 실행
    print("BrowserManager 단위 테스트 시작...\n")

    # 테스트 스위트 생성
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBrowserManager)

    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 결과 요약
    print(f"\n테스트 요약:")
    print(f"- 실행: {result.testsRun}개")
    print(f"- 성공: {result.testsRun - len(result.failures) - len(result.errors)}개")
    print(f"- 실패: {len(result.failures)}개")
    print(f"- 오류: {len(result.errors)}개")

    # 성공/실패 판정
    if len(result.failures) == 0 and len(result.errors) == 0:
        print("\n✅ 모든 테스트 통과!")
        exit(0)
    else:
        print("\n❌ 테스트 실패!")
        exit(1)
