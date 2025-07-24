# test_flow_manager.py
'''
단순화된 FlowManager 테스트
'''

import os
import sys
import tempfile
import shutil
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

from ai_helpers_new.flow_manager import FlowManager
from ai_helpers_new.domain.models import TaskStatus
from ai_helpers_new.exceptions import ValidationError


class TestFlowManager:
    """FlowManager 통합 테스트"""

    @pytest.fixture
    def temp_dir(self):
        """임시 디렉토리"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def manager(self, temp_dir):
        """테스트용 FlowManager"""
        return FlowManager(base_path=temp_dir, context_enabled=False)

    def test_flow_lifecycle(self, manager):
        """Flow 생명주기 테스트"""
        # Flow 생성
        flow = manager.create_flow('Test Flow', project='test-project')
        assert flow.id is not None
        assert flow.name == 'Test Flow'
        assert flow.project == 'test-project'

        # Flow 조회
        retrieved = manager.get_flow(flow.id)
        assert retrieved is not None
        assert retrieved.id == flow.id

        # Flow 목록
        flows = manager.list_flows()
        assert len(flows) == 1
        assert flows[0].id == flow.id

        # 프로젝트별 목록
        project_flows = manager.list_flows(project='test-project')
        assert len(project_flows) == 1

        other_flows = manager.list_flows(project='other-project')
        assert len(other_flows) == 0

        # Flow 삭제
        manager.delete_flow(flow.id)
        assert manager.get_flow(flow.id) is None

    def test_plan_management(self, manager):
        """Plan 관리 테스트"""
        # Flow 생성
        flow = manager.create_flow('Test Flow')

        # Plan 생성
        plan = manager.create_plan(flow.id, 'Test Plan')
        assert plan.id is not None
        assert plan.name == 'Test Plan'

        # Flow에서 Plan 확인
        flow = manager.get_flow(flow.id)
        assert plan.id in flow.plans
        assert flow.plans[plan.id].name == 'Test Plan'

        # Plan 상태 업데이트
        manager.update_plan_status(flow.id, plan.id, True)
        flow = manager.get_flow(flow.id)
        assert flow.plans[plan.id].completed is True

        # Plan 삭제
        manager.delete_plan(flow.id, plan.id)
        flow = manager.get_flow(flow.id)
        assert plan.id not in flow.plans

    def test_task_management(self, manager):
        """Task 관리 테스트"""
        # Flow와 Plan 생성
        flow = manager.create_flow('Test Flow')
        plan = manager.create_plan(flow.id, 'Test Plan')

        # Task 생성
        task = manager.create_task(flow.id, plan.id, 'Test Task')
        assert task.id is not None
        assert task.name == 'Test Task'
        assert task.status == TaskStatus.TODO.value

        # Task 상태 업데이트
        manager.update_task_status(flow.id, plan.id, task.id, TaskStatus.IN_PROGRESS.value)
        flow = manager.get_flow(flow.id)
        updated_task = flow.plans[plan.id].tasks[task.id]
        assert updated_task.status == TaskStatus.IN_PROGRESS.value

        # Task context 업데이트
        context = {'key': 'value', 'number': 42}
        manager.update_task_context(flow.id, plan.id, task.id, context)
        flow = manager.get_flow(flow.id)
        assert flow.plans[plan.id].tasks[task.id].context['key'] == 'value'
        assert flow.plans[plan.id].tasks[task.id].context['number'] == 42

        # Task 삭제
        manager.delete_task(flow.id, plan.id, task.id)
        flow = manager.get_flow(flow.id)
        assert task.id not in flow.plans[plan.id].tasks

    def test_auto_plan_completion(self, manager):
        """Plan 자동 완료 테스트"""
        # Flow, Plan, Tasks 생성
        flow = manager.create_flow('Test Flow')
        plan = manager.create_plan(flow.id, 'Test Plan')

        task1 = manager.create_task(flow.id, plan.id, 'Task 1')
        task2 = manager.create_task(flow.id, plan.id, 'Task 2')

        # Plan은 아직 미완료
        flow = manager.get_flow(flow.id)
        assert flow.plans[plan.id].completed is False

        # 첫 번째 Task 완료
        manager.update_task_status(flow.id, plan.id, task1.id, TaskStatus.COMPLETED.value)
        flow = manager.get_flow(flow.id)
        assert flow.plans[plan.id].completed is False  # 아직 미완료

        # 두 번째 Task도 완료
        manager.update_task_status(flow.id, plan.id, task2.id, TaskStatus.COMPLETED.value)
        flow = manager.get_flow(flow.id)
        assert flow.plans[plan.id].completed is True  # 자동 완료!

    def test_current_flow_and_project(self, manager):
        """현재 Flow와 프로젝트 테스트"""
        # 프로젝트 설정
        manager.current_project = 'my-project'
        assert manager.current_project == 'my-project'

        # Flow 생성 (프로젝트 자동 적용)
        flow = manager.create_flow('Test Flow')
        assert flow.project == 'my-project'

        # 현재 Flow 설정
        assert manager.current_flow is not None
        assert manager.current_flow.id == flow.id

        # 다른 Flow로 변경
        flow2 = manager.create_flow('Another Flow')
        manager.current_flow = flow2.id
        assert manager.current_flow.id == flow2.id

    def test_statistics(self, manager):
        """통계 테스트"""
        # 데이터 생성
        flow1 = manager.create_flow('Flow 1')
        flow2 = manager.create_flow('Flow 2')

        plan1 = manager.create_plan(flow1.id, 'Plan 1')
        plan2 = manager.create_plan(flow1.id, 'Plan 2')
        plan3 = manager.create_plan(flow2.id, 'Plan 3')

        task1 = manager.create_task(flow1.id, plan1.id, 'Task 1')
        task2 = manager.create_task(flow1.id, plan1.id, 'Task 2')
        task3 = manager.create_task(flow2.id, plan3.id, 'Task 3')

        # 일부 Task 완료
        manager.update_task_status(flow1.id, plan1.id, task1.id, TaskStatus.COMPLETED.value)
        manager.update_task_status(flow2.id, plan3.id, task3.id, TaskStatus.REVIEWING.value)

        # 통계 확인
        stats = manager.get_statistics()
        assert stats['total_flows'] == 2
        assert stats['total_plans'] == 3
        assert stats['total_tasks'] == 3
        assert stats['completed_tasks'] == 2
        assert stats['completion_rate'] == 2/3

    def test_error_handling(self, manager):
        """에러 처리 테스트"""
        # 존재하지 않는 Flow
        with pytest.raises(ValidationError):
            manager.create_plan('non-existent', 'Plan')

        # 잘못된 Task 상태
        flow = manager.create_flow('Test')
        plan = manager.create_plan(flow.id, 'Plan')
        task = manager.create_task(flow.id, plan.id, 'Task')

        with pytest.raises(ValidationError):
            manager.update_task_status(flow.id, plan.id, task.id, 'invalid-status')


# 실행
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
