"""
test_workflow.py를 위한 단위 테스트
"""
import unittest
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_workflow import calculate_sum, calculate_product, greet_user, WorkflowTester

class TestWorkflowFunctions(unittest.TestCase):
    """워크플로우 함수들에 대한 단위 테스트"""

    def test_calculate_sum(self):
        """덧셈 함수 테스트"""
        self.assertEqual(calculate_sum(2, 3), 5)
        self.assertEqual(calculate_sum(-1, 1), 0)
        self.assertEqual(calculate_sum(0, 0), 0)

    def test_calculate_product(self):
        """곱셈 함수 테스트"""
        self.assertEqual(calculate_product(2, 3), 6)
        self.assertEqual(calculate_product(-2, 3), -6)
        self.assertEqual(calculate_product(0, 5), 0)

    def test_greet_user(self):
        """인사 함수 테스트"""
        self.assertEqual(greet_user("Claude"), "안녕하세요, Claude님!")
        self.assertEqual(greet_user("테스터"), "안녕하세요, 테스터님!")

class TestWorkflowTester(unittest.TestCase):
    """WorkflowTester 클래스 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.tester = WorkflowTester()

    def test_run_test_success(self):
        """성공 테스트"""
        result = self.tester.run_test("테스트1", 5, 5)
        self.assertTrue(result)
        self.assertEqual(len(self.tester.results), 1)

    def test_run_test_failure(self):
        """실패 테스트"""
        result = self.tester.run_test("테스트2", 5, 3)
        self.assertFalse(result)
        self.assertEqual(len(self.tester.results), 1)

    def test_get_summary(self):
        """요약 테스트"""
        self.tester.run_test("성공", 1, 1)
        self.tester.run_test("실패", 1, 2)

        summary = self.tester.get_summary()
        self.assertEqual(summary["total_tests"], 2)
        self.assertEqual(summary["passed"], 1)
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(summary["success_rate"], 0.5)

if __name__ == "__main__":
    print("🧪 단위 테스트 실행 중...")
    unittest.main(verbosity=2)
