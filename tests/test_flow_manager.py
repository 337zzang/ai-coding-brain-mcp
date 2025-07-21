import pytest
import os
import json
import sys

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python.ai_helpers_new.flow_manager import FlowManager, get_flow_manager, flow
from python.ai_helpers_new.models import Plan, Task


class TestFlowManager:
    """FlowManager 단위 테스트"""

    @pytest.fixture
    def temp_workflow_dir(self, tmp_path):
        """임시 워크플로우 디렉토리"""
        workflow_dir = tmp_path / ".ai-brain"
        workflow_dir.mkdir()
        return str(workflow_dir)

    @pytest.fixture
    def flow_manager(self, temp_workflow_dir, monkeypatch):
        """테스트용 FlowManager 인스턴스"""
        monkeypatch.setattr('python.ai_helpers_new.flow_manager.WORKFLOW_DIR', temp_workflow_dir)
        # 싱글톤 리셋
        import python.ai_helpers_new.flow_manager as fm_module
        fm_module._flow_manager_instance = None
        return get_flow_manager()

    def test_initialization(self, flow_manager, temp_workflow_dir):
        """초기화 테스트"""
        assert flow_manager is not None
        assert flow_manager.version == "2.0"
        assert os.path.exists(os.path.join(temp_workflow_dir, 'workflow.json'))

    def test_create_plan(self, flow_manager):
        """Plan 생성 테스트"""
        plan = flow_manager.create_plan("테스트 프로젝트", "테스트 목표")

        assert plan is not None
        assert plan.title == "테스트 프로젝트"
        assert plan.objective == "테스트 목표"
        assert plan.status == "active"
        assert plan.id in flow_manager.plans

    def test_create_task(self, flow_manager):
        """Task 생성 테스트"""
        # Plan 생성
        plan = flow_manager.create_plan("프로젝트")

        # Task 생성
        task = flow_manager.create_task("작업 1", plan.id, description="설명")

        assert task is not None
        assert task.title == "작업 1"
        assert task.description == "설명"
        assert task.plan_id == plan.id
        assert task in plan.tasks

    def test_auto_default_plan(self, flow_manager):
        """기본 Plan 자동 생성 테스트"""
        # Plan 없이 Task 생성
        task = flow_manager.create_task("독립 작업")

        assert task is not None
        assert len(flow_manager.plans) == 1

        default_plan = list(flow_manager.plans.values())[0]
        assert default_plan.title == "Default Plan"
        assert task in default_plan.tasks

    def test_plan_progress(self, flow_manager):
        """Plan 진행률 계산 테스트"""
        plan = flow_manager.create_plan("진행률 테스트")

        # 태스크 3개 생성
        task1 = flow_manager.create_task("작업 1", plan.id)
        task2 = flow_manager.create_task("작업 2", plan.id)
        task3 = flow_manager.create_task("작업 3", plan.id)

        assert plan.progress == 0.0

        # 하나 완료
        flow_manager.update_task(task1.id, status='completed')
        assert plan.progress == 33.33

        # 두 개 완료
        flow_manager.update_task(task2.id, status='completed')
        assert plan.progress == 66.67

        # 모두 완료
        flow_manager.update_task(task3.id, status='completed')
        assert plan.progress == 100.0

    def test_v1_migration(self, flow_manager, temp_workflow_dir):
        """v1 마이그레이션 테스트"""
        # v1 데이터 생성
        v1_data = {
            "version": "1.0",
            "tasks": [
                {
                    "id": "task_001",
                    "name": "v1 태스크 1",
                    "status": "done",
                    "created_at": "2024-01-01T00:00:00"
                },
                {
                    "id": "task_002",
                    "name": "v1 태스크 2",
                    "status": "todo",
                    "description": "설명"
                }
            ]
        }

        # v1 파일 저장
        workflow_path = os.path.join(temp_workflow_dir, 'workflow.json')
        with open(workflow_path, 'w') as f:
            json.dump(v1_data, f)

        # FlowManager 재생성 (마이그레이션 트리거)
        import python.ai_helpers_new.flow_manager as fm_module
        fm_module._flow_manager_instance = None
        fm = get_flow_manager()

        # 마이그레이션 확인
        assert len(fm.plans) == 1

        migrated_plan = list(fm.plans.values())[0]
        assert migrated_plan.id == "plan_migrated"
        assert len(migrated_plan.tasks) == 2

        # 태스크 내용 확인
        task1 = migrated_plan.tasks[0]
        assert task1.title == "v1 태스크 1"
        assert task1.status == "completed"  # done -> completed

        task2 = migrated_plan.tasks[1]
        assert task2.title == "v1 태스크 2"
        assert task2.status == "todo"

    def test_flow_command(self, flow_manager):
        """flow 명령어 테스트"""
        # Plan 생성
        plan = flow_manager.create_plan("테스트")
        flow_manager.create_task("작업", plan.id)

        # /flow 명령어
        result = flow_manager.wf_command("/flow")
        assert result['ok'] == True
        assert '활성 Plan: 테스트' in result['data']
        assert '진행률: 0.0%' in result['data']

    def test_data_persistence(self, flow_manager, temp_workflow_dir):
        """데이터 영속성 테스트"""
        # 데이터 생성
        plan = flow_manager.create_plan("영속성 테스트", priority=1, tags=['test'])
        task = flow_manager.create_task("작업", plan.id)

        # 저장
        flow_manager._save_data()

        # 새 인스턴스로 로드
        import python.ai_helpers_new.flow_manager as fm_module
        fm_module._flow_manager_instance = None
        new_fm = get_flow_manager()

        # 데이터 확인
        assert len(new_fm.plans) == 1
        loaded_plan = new_fm.get_plan(plan.id)
        assert loaded_plan is not None
        assert loaded_plan.title == "영속성 테스트"
        assert loaded_plan.priority == 1
        assert 'test' in loaded_plan.tags
        assert len(loaded_plan.tasks) == 1

    # === Phase 2 테스트 추가 ===

    def test_plan_search(self, flow_manager):
        """Plan 검색 테스트"""
        # 여러 Plan 생성
        plan1 = flow_manager.create_plan("API Development", tags=['backend', 'api'])
        plan2 = flow_manager.create_plan("UI Design", tags=['frontend', 'design'])
        plan3 = flow_manager.create_plan("Database Schema", tags=['backend', 'db'])

        # 태그로 검색
        backend_plans = flow_manager.find_plans(tags=['backend'])
        assert len(backend_plans) == 2

        # 텍스트 검색
        api_plans = flow_manager.find_plans(search='api')
        assert len(api_plans) == 1
        assert api_plans[0].title == "API Development"

        # 정렬
        sorted_plans = flow_manager.find_plans(sort_by='title')
        assert sorted_plans[0].title == "API Development"

    def test_task_dependencies(self, flow_manager):
        """Task 의존성 테스트"""
        plan = flow_manager.create_plan("Dependency Test")

        # Task 생성
        t1 = flow_manager.create_task("Task 1", plan.id)
        t2 = flow_manager.create_task("Task 2", plan.id)
        t3 = flow_manager.create_task("Task 3", plan.id)

        # 의존성 추가
        result = flow_manager.add_task_dependency(t2.id, t1.id)
        assert result['ok'] == True

        result = flow_manager.add_task_dependency(t3.id, t2.id)
        assert result['ok'] == True

        # 순환 의존성 방지
        result = flow_manager.add_task_dependency(t1.id, t3.id)
        assert result['ok'] == False
        assert 'circular' in result['error'].lower()

        # 실행 순서
        order = flow_manager.get_task_order(plan.id)
        assert len(order) == 3
        assert order[0].id == t1.id
        assert order[1].id == t2.id
        assert order[2].id == t3.id

    def test_task_move(self, flow_manager):
        """Task 이동 테스트"""
        plan1 = flow_manager.create_plan("Plan 1")
        plan2 = flow_manager.create_plan("Plan 2")

        # Task 생성
        task = flow_manager.create_task("Mobile Task", plan1.id)
        assert len(plan1.tasks) == 1
        assert len(plan2.tasks) == 0

        # 이동
        result = flow_manager.move_task(task.id, plan2.id)
        assert result['ok'] == True

        # 확인
        plan1 = flow_manager.get_plan(plan1.id)
        plan2 = flow_manager.get_plan(plan2.id)
        assert len(plan1.tasks) == 0
        assert len(plan2.tasks) == 1
        assert plan2.tasks[0].id == task.id

    def test_plan_statistics(self, flow_manager):
        """Plan 통계 테스트"""
        plan = flow_manager.create_plan("Stats Test")

        # 다양한 상태의 Task
        t1 = flow_manager.create_task("Done", plan.id)
        flow_manager.update_task(t1.id, status='completed')

        t2 = flow_manager.create_task("In Progress", plan.id)
        flow_manager.update_task(t2.id, status='in_progress')

        t3 = flow_manager.create_task("Todo", plan.id)

        # 통계 확인
        stats = flow_manager.get_plan_statistics(plan.id)
        assert stats['ok'] == True

        data = stats['data']
        assert data['total_tasks'] == 3
        assert data['completed_tasks'] == 1
        assert data['in_progress_tasks'] == 1
        assert data['todo_tasks'] == 1
        assert data['progress'] == 33.33
        assert data['health_score'] >= 0

    def test_plan_archive(self, flow_manager):
        """Plan 아카이브 테스트"""
        plan = flow_manager.create_plan("To Archive")
        assert plan.status == 'active'

        # 아카이브
        archived = flow_manager.archive_plan(plan.id)
        assert archived is not None
        assert archived.status == 'archived'

        # 아카이브된 Plan 검색
        active_plans = flow_manager.find_plans(status='active')
        assert plan not in active_plans

        archived_plans = flow_manager.find_plans(status='archived')
        assert archived in archived_plans



if __name__ == "__main__":
    pytest.main([__file__, "-v"])
