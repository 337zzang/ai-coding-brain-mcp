"""
Test FlowAPI Standard Interface
Task 3: FlowAPI 표준 인터페이스 확립 테스트
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'python')))

import pytest
import warnings
from ai_helpers_new import get_flow_api, get_flow_manager


class TestFlowAPIStandard:
    """FlowAPI 표준 인터페이스 테스트"""

    def setup_method(self):
        """각 테스트 전 실행"""
        self.api = get_flow_api()
        # 테스트용 Plan 생성
        result = self.api.create_plan("Test Plan")
        assert result['ok']
        self.plan_id = result['data']['id']

    def teardown_method(self):
        """각 테스트 후 정리"""
        # 생성한 Plan 삭제
        if hasattr(self, 'plan_id'):
            self.api.delete_plan(self.plan_id)

    def test_standard_response_format(self):
        """표준 응답 형식 테스트"""
        # 성공 케이스
        result = self.api.create_plan("Standard Response Test")
        assert 'ok' in result
        assert 'data' in result
        assert result['ok'] is True
        assert 'id' in result['data']

        # 실패 케이스
        result = self.api.get_plan("non-existent-plan")
        assert 'ok' in result
        assert 'error' in result
        assert result['ok'] is False

    def test_get_task_by_number(self):
        """get_task_by_number 메서드 테스트"""
        # Task 생성
        task_result = self.api.add_task(self.plan_id, "Test Task 1")
        assert task_result['ok']

        task_result2 = self.api.add_task(self.plan_id, "Test Task 2")
        assert task_result2['ok']

        # 번호로 Task 조회
        result = self.api.get_task_by_number(self.plan_id, 1)
        assert result['ok']
        assert result['data']['title'] == "Test Task 1"

        result = self.api.get_task_by_number(self.plan_id, 2)
        assert result['ok']
        assert result['data']['title'] == "Test Task 2"

        # 존재하지 않는 번호
        result = self.api.get_task_by_number(self.plan_id, 99)
        assert not result['ok']
        assert 'error' in result

    def test_manager_deprecation(self):
        """get_flow_manager deprecation 테스트"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            manager = get_flow_manager()

            # DeprecationWarning 발생 확인
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "get_flow_api()" in str(w[0].message)

    def test_all_methods_return_standard_format(self):
        """모든 메서드가 표준 형식 반환하는지 테스트"""
        # Plan 관련 메서드
        methods_to_test = [
            (self.api.list_plans, []),
            (self.api.get_current_plan, []),
            (self.api.get_stats, []),
            (self.api.update_plan, [self.plan_id, "Updated Name"]),
        ]

        for method, args in methods_to_test:
            result = method(*args)
            assert isinstance(result, dict), f"{method.__name__} should return dict"
            assert 'ok' in result, f"{method.__name__} should have 'ok' field"
            assert result['ok'] in [True, False], f"{method.__name__} 'ok' should be bool"

            if result['ok']:
                assert 'data' in result, f"{method.__name__} success should have 'data'"
            else:
                assert 'error' in result, f"{method.__name__} failure should have 'error'"


if __name__ == "__main__":
    # 테스트 실행
    test = TestFlowAPIStandard()

    print("🧪 FlowAPI 표준 인터페이스 테스트 시작")
    print("="*60)

    # setup
    test.setup_method()

    try:
        # 각 테스트 실행
        print("1. 표준 응답 형식 테스트...")
        test.test_standard_response_format()
        print("   ✅ 통과")

        print("2. get_task_by_number 테스트...")
        test.test_get_task_by_number()
        print("   ✅ 통과")

        print("3. Manager deprecation 테스트...")
        test.test_manager_deprecation()
        print("   ✅ 통과")

        print("4. 모든 메서드 표준 형식 반환 테스트...")
        test.test_all_methods_return_standard_format()
        print("   ✅ 통과")

        print("\n✨ 모든 테스트 통과!")

    finally:
        # cleanup
        test.teardown_method()
