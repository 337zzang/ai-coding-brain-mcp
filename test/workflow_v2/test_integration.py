"""
Workflow v2 통합 테스트
미해결 이슈를 고려하여 작성된 테스트 코드
"""
import unittest
import os
import sys
import json
from typing import Dict, Any

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'python'))


class TestWorkflowV2Integration(unittest.TestCase):
    """Workflow v2 시스템 통합 테스트"""

    @classmethod
    def setUpClass(cls):
        """테스트 클래스 초기화"""
        cls.test_project = "test_v2_project"
        cls.test_plan_name = "통합 테스트 플랜"
        cls.test_task_title = "테스트 태스크"

    def setUp(self):
        """각 테스트 전 실행"""
        # 테스트용 워크플로우 디렉토리 생성
        self.workflow_dir = os.path.join('memory', 'workflow_v2')
        os.makedirs(self.workflow_dir, exist_ok=True)

    def test_01_import_modules(self):
        """모듈 import 테스트"""
        try:
            from workflow.v2.models import WorkflowPlan, Task, TaskStatus, PlanStatus
            from workflow.v2.manager import WorkflowV2Manager
            self.assertTrue(True, "모든 모듈 import 성공")
        except ImportError as e:
            self.fail(f"Import 실패: {e}")

    def test_02_create_manager(self):
        """WorkflowV2Manager 생성 테스트"""
        try:
            from workflow.v2.manager import WorkflowV2Manager
            manager = WorkflowV2Manager(self.test_project)
            self.assertIsNotNone(manager, "Manager 생성 성공")
            self.assertEqual(manager.project_name, self.test_project)
        except Exception as e:
            self.fail(f"Manager 생성 실패: {e}")

    def test_03_create_plan(self):
        """플랜 생성 테스트"""
        try:
            from workflow.v2.manager import WorkflowV2Manager
            manager = WorkflowV2Manager(self.test_project)

            plan = manager.create_plan(self.test_plan_name, "테스트 설명")
            self.assertIsNotNone(plan, "플랜 생성 성공")
            self.assertEqual(plan.name, self.test_plan_name)
            self.assertEqual(len(plan.tasks), 0, "초기 태스크 수는 0")
        except Exception as e:
            self.fail(f"플랜 생성 실패: {e}")

    def test_04_add_task(self):
        """태스크 추가 테스트"""
        try:
            from workflow.v2.manager import WorkflowV2Manager
            manager = WorkflowV2Manager(self.test_project)

            # 플랜 생성
            manager.create_plan(self.test_plan_name, "테스트")

            # 태스크 추가
            task = manager.add_task(self.test_task_title, "테스트 설명")
            self.assertIsNotNone(task, "태스크 추가 성공")
            self.assertEqual(task.title, self.test_task_title)
            self.assertEqual(task.status.value, "todo")
        except Exception as e:
            self.fail(f"태스크 추가 실패: {e}")

    def test_05_handlers_api(self):
        """핸들러 API 테스트"""
        try:
            from workflow.v2.handlers import get_status, create_plan, add_task

            # 상태 조회
            result = get_status()
            self.assertTrue(hasattr(result, 'ok'), "HelperResult 반환")

            # 플랜 생성
            result = create_plan("핸들러 테스트", "설명")
            self.assertTrue(hasattr(result, 'ok'), "플랜 생성 API 작동")

            # 태스크 추가
            result = add_task("핸들러 태스크", "설명")
            self.assertTrue(hasattr(result, 'ok'), "태스크 추가 API 작동")
        except Exception as e:
            self.fail(f"핸들러 API 실패: {e}")

    def test_06_dispatcher(self):
        """명령어 디스패처 테스트"""
        try:
            from workflow.v2.dispatcher import execute_workflow_command

            # 상태 명령
            result = execute_workflow_command("/status")
            self.assertTrue(hasattr(result, 'ok'), "디스패처 작동")

            # 잘못된 명령
            result = execute_workflow_command("/invalid_command")
            self.assertTrue(hasattr(result, 'ok'), "에러 처리 작동")
            if result.ok:
                data = result.data if hasattr(result, 'data') else {}
                self.assertIn('error', data, "에러 메시지 포함")
        except Exception as e:
            self.fail(f"디스패처 실패: {e}")

    def test_07_context_integration(self):
        """컨텍스트 통합 테스트"""
        try:
            from workflow.v2.context_integration import get_context_integration

            integration = get_context_integration()
            self.assertIsNotNone(integration, "컨텍스트 통합 객체 생성")

            # 현재 컨텍스트 가져오기
            context = integration.get_current_context()
            self.assertIsInstance(context, dict, "컨텍스트는 딕셔너리")
        except Exception as e:
            self.fail(f"컨텍스트 통합 실패: {e}")

    def test_08_persistence(self):
        """데이터 영속성 테스트"""
        try:
            from workflow.v2.manager import WorkflowV2Manager

            # 첫 번째 매니저로 데이터 생성
            manager1 = WorkflowV2Manager("persist_test")
            plan = manager1.create_plan("영속성 테스트", "설명")
            task = manager1.add_task("태스크1", "설명1")

            # 두 번째 매니저로 데이터 로드
            manager2 = WorkflowV2Manager("persist_test")
            self.assertIsNotNone(manager2.current_plan, "플랜 로드 성공")
            self.assertEqual(manager2.current_plan.name, "영속성 테스트")
            self.assertEqual(len(manager2.current_plan.tasks), 1, "태스크 로드 성공")
        except Exception as e:
            self.fail(f"영속성 테스트 실패: {e}")

    def tearDown(self):
        """각 테스트 후 정리"""
        # 테스트 파일 정리 (선택적)
        pass

    @classmethod
    def tearDownClass(cls):
        """테스트 클래스 정리"""
        # 테스트용 파일 삭제 (선택적)
        pass


def run_tests():
    """테스트 실행"""
    # 테스트 러너 설정
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestWorkflowV2Integration)

    # 상세 출력으로 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
