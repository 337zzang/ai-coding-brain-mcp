import pytest
import os
import json
import sys
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python.ai_helpers_new.workflow_manager import WorkflowManager, get_workflow_manager, wf


class TestWorkflowManager:
    """WorkflowManager 단위 테스트"""

    @pytest.fixture
    def temp_workflow_dir(self, tmp_path):
        """임시 워크플로우 디렉토리"""
        workflow_dir = tmp_path / ".ai-brain"
        workflow_dir.mkdir()
        return str(workflow_dir)

    @pytest.fixture
    def workflow_manager(self, temp_workflow_dir, monkeypatch):
        """테스트용 WorkflowManager 인스턴스"""
        monkeypatch.setattr('python.ai_helpers_new.workflow_manager.WORKFLOW_DIR', temp_workflow_dir)
        # 싱글톤 리셋
        if hasattr(WorkflowManager, '_instance'):
            delattr(WorkflowManager, '_instance')
        return get_workflow_manager()

    def test_initialization(self, workflow_manager, temp_workflow_dir):
        """초기화 테스트"""
        assert workflow_manager is not None
        assert os.path.exists(os.path.join(temp_workflow_dir, 'workflow.json'))

    def test_add_task(self, workflow_manager):
        """태스크 추가 테스트"""
        result = workflow_manager.add_task("테스트 태스크", "설명")

        assert result['ok'] == True
        assert 'task_id' in result['data']
        assert len(workflow_manager.workflow['tasks']) == 1

        task = workflow_manager.workflow['tasks'][0]
        assert task['name'] == "테스트 태스크"
        assert task['description'] == "설명"
        assert task['status'] == 'todo'

    def test_update_task(self, workflow_manager):
        """태스크 업데이트 테스트"""
        # 태스크 추가
        add_result = workflow_manager.add_task("원본 태스크")
        task_id = add_result['data']['task_id']

        # 상태 업데이트
        update_result = workflow_manager.update_task(task_id, status='in_progress')
        assert update_result['ok'] == True

        task = workflow_manager.workflow['tasks'][0]
        assert task['status'] == 'in_progress'
        assert task['updated_at'] is not None

    def test_task_lifecycle(self, workflow_manager):
        """태스크 생명주기 테스트"""
        # 생성
        add_result = workflow_manager.add_task("생명주기 테스트")
        task_id = add_result['data']['task_id']

        # 시작
        workflow_manager.update_task(task_id, status='in_progress')
        task = workflow_manager.get_current_task()
        assert task is not None
        assert task['status'] == 'in_progress'

        # 완료
        workflow_manager.update_task(task_id, status='completed')
        task = next(t for t in workflow_manager.workflow['tasks'] if t['id'] == task_id)
        assert task['status'] == 'completed'

    def test_list_tasks(self, workflow_manager):
        """태스크 목록 테스트"""
        # 여러 태스크 추가
        workflow_manager.add_task("태스크 1")
        workflow_manager.add_task("태스크 2")
        workflow_manager.add_task("태스크 3")

        result = workflow_manager.list_tasks()
        assert result['ok'] == True
        assert len(result['data']) == 3

    def test_wf_command_parsing(self, workflow_manager):
        """명령어 파싱 테스트"""
        # /task add
        result = workflow_manager.wf_command("/task add 새로운 작업")
        assert result['ok'] == True
        assert result['type'] == 'workflow_command'

        # /status
        result = workflow_manager.wf_command("/status")
        assert result['ok'] == True
        assert '진행률' in result['data']

        # /list
        result = workflow_manager.wf_command("/list")
        assert result['ok'] == True

    def test_invalid_commands(self, workflow_manager):
        """잘못된 명령어 처리 테스트"""
        # 잘못된 명령어
        result = workflow_manager.wf_command("/invalid")
        assert result['ok'] == False
        assert 'error' in result

        # 빈 명령어
        result = workflow_manager.wf_command("")
        assert result['ok'] == False

    def test_workflow_persistence(self, workflow_manager, temp_workflow_dir):
        """워크플로우 영속성 테스트"""
        # 태스크 추가
        workflow_manager.add_task("영속성 테스트")

        # 저장
        workflow_manager.save_workflow()

        # 파일 확인
        workflow_path = os.path.join(temp_workflow_dir, 'workflow.json')
        assert os.path.exists(workflow_path)

        # 내용 확인
        with open(workflow_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)

        assert len(saved_data['tasks']) == 1
        assert saved_data['tasks'][0]['name'] == "영속성 테스트"

    def test_singleton_pattern(self):
        """싱글톤 패턴 테스트"""
        manager1 = get_workflow_manager()
        manager2 = get_workflow_manager()

        assert manager1 is manager2

    def test_wf_helper_function(self, workflow_manager):
        """wf() 헬퍼 함수 테스트"""
        result = wf("/status")
        assert result['ok'] == True
        assert result['type'] == 'workflow_command'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
