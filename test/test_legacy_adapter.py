# test_legacy_adapter.py
'''
레거시 어댑터 테스트
'''

import os
import sys
import tempfile
import shutil
import pytest
import warnings

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

from ai_helpers_new.flow_manager import FlowManager
from ai_helpers_new.legacy_flow_adapter import LegacyFlowAdapter, create_flow_manager
from ai_helpers_new.exceptions import ValidationError


class TestLegacyAdapter:
    """레거시 어댑터 테스트"""

    @pytest.fixture
    def temp_dir(self):
        """임시 디렉토리"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def adapter(self, temp_dir):
        """테스트용 레거시 어댑터"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            manager = FlowManager(base_path=temp_dir, context_enabled=False)
            return LegacyFlowAdapter(manager)

    def test_legacy_flows_property(self, adapter):
        """레거시 flows 속성 테스트"""
        # 초기 상태
        assert adapter.flows == {}

        # Flow 생성
        flow_dict = adapter.create_flow('Test Flow')

        # flows 속성 확인
        flows = adapter.flows
        assert len(flows) == 1
        assert flow_dict['id'] in flows
        assert flows[flow_dict['id']]['name'] == 'Test Flow'

        # flows 속성 설정
        new_flows = {
            'flow1': {
                'id': 'flow1',
                'name': 'Flow 1',
                'plans': {},
                'created_at': '2025-01-01T00:00:00',
                'updated_at': '2025-01-01T00:00:00',
                'metadata': {}
            }
        }
        adapter.flows = new_flows

        # 변경 확인
        flows = adapter.flows
        assert 'flow1' in flows
        assert flows['flow1']['name'] == 'Flow 1'

    def test_legacy_current_flow(self, adapter):
        """레거시 current_flow 테스트"""
        # Flow 생성
        flow_dict = adapter.create_flow('Test Flow')

        # current_flow 확인
        current = adapter.current_flow
        assert current is not None
        assert current['id'] == flow_dict['id']

        # current_flow 설정 (딕셔너리)
        adapter.current_flow = flow_dict
        assert adapter.current_flow['id'] == flow_dict['id']

        # current_flow 설정 (문자열)
        adapter.current_flow = flow_dict['id']
        assert adapter.current_flow['id'] == flow_dict['id']

    def test_legacy_methods(self, adapter):
        """레거시 메서드 테스트"""
        # Flow 생성
        flow = adapter.create_flow('Test Flow')
        flow_id = flow['id']

        # Flow 조회
        retrieved = adapter.get_flow(flow_id)
        assert retrieved is not None
        assert retrieved['id'] == flow_id

        # Flow 목록
        flows = adapter.list_flows()
        assert len(flows) == 1
        assert flows[0]['id'] == flow_id

        # Plan 추가
        plan = adapter.add_plan(flow_id, 'Test Plan')
        assert plan['id'] is not None
        assert plan['name'] == 'Test Plan'

        # Task 추가
        task = adapter.add_task(flow_id, plan['id'], 'Test Task')
        assert task['id'] is not None
        assert task['name'] == 'Test Task'

        # Task 상태 업데이트
        adapter.update_task_status(flow_id, plan['id'], task['id'], 'in_progress')

        # Task context 업데이트
        adapter.update_task_context(flow_id, plan['id'], task['id'], {'key': 'value'})

        # Task 액션 추가
        adapter.add_task_action(flow_id, plan['id'], task['id'], 'test_action', {'detail': 'test'})

        # Flow 삭제
        adapter.delete_flow(flow_id)
        assert adapter.get_flow(flow_id) is None

    def test_legacy_stats(self, adapter):
        """레거시 통계 테스트"""
        # 데이터 생성
        flow = adapter.create_flow('Test Flow')
        plan = adapter.add_plan(flow['id'], 'Test Plan')
        task1 = adapter.add_task(flow['id'], plan['id'], 'Task 1')
        task2 = adapter.add_task(flow['id'], plan['id'], 'Task 2')

        # 하나 완료
        adapter.update_task_status(flow['id'], plan['id'], task1['id'], 'completed')

        # 통계 확인
        stats = adapter.get_stats()
        assert stats['flows'] == 1
        assert stats['plans'] == 1
        assert stats['tasks'] == 2
        assert stats['completed'] == 1
        assert stats['percentage'] == 50

    def test_legacy_save_load(self, adapter):
        """레거시 save/load 테스트"""
        # save와 load는 실제로는 아무것도 하지 않음 (자동 저장)
        adapter.save()  # 에러 없이 실행되어야 함
        adapter.load()  # 에러 없이 실행되어야 함

    def test_create_flow_manager_factory(self, temp_dir):
        """팩토리 함수 테스트"""
        # 일반 FlowManager
        manager = create_flow_manager(base_path=temp_dir)
        assert isinstance(manager, FlowManager)

        # 레거시 어댑터
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            legacy = create_flow_manager(legacy=True, base_path=temp_dir)
            assert isinstance(legacy, LegacyFlowAdapter)


# 실행
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
