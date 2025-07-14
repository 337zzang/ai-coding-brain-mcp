
import os
import json
from typing import Dict, Any, Optional
from pathlib import Path
import sys

sys.path.append('./python')
from ai_helpers.workflow.integrated_workflow import IntegratedWorkflowManager
from ai_helpers.protocols.stdout_protocol import StdoutProtocol

class WorkflowAdapter:
    '''기존 helpers 함수들과 통합 워크플로우를 연결하는 어댑터'''

    def __init__(self):
        self.managers: Dict[str, IntegratedWorkflowManager] = {}
        self.current_project: Optional[str] = None
        self.global_protocol = StdoutProtocol()  # 전역 프로토콜

    def flow_project(self, project_name: str) -> Dict[str, Any]:
        '''helpers.flow_project의 통합 버전'''
        # 프로토콜로 섹션 시작
        self.global_protocol.section(f"PROJECT_FLOW:{project_name}")

        # 기존 flow_project 호출
        result = helpers.flow_project(project_name)

        # 통합 매니저 초기화 또는 가져오기
        if project_name not in self.managers:
            self.managers[project_name] = IntegratedWorkflowManager(project_name)

        self.current_project = project_name

        # 프로토콜로 데이터 출력
        self.global_protocol.data('project', project_name)
        self.global_protocol.data('status', result.get('success', False))

        # 워크플로우 상태가 있으면 동기화
        if 'workflow_status' in result:
            self._sync_workflow_status(result['workflow_status'])

        self.global_protocol.end_section()
        return result

    def _sync_workflow_status(self, status: Dict) -> None:
        '''워크플로우 상태를 통합 시스템과 동기화'''
        if not self.current_project:
            return

        manager = self.managers[self.current_project]

        # 상태 동기화
        if status.get('plan_id'):
            manager.workflow_state.update({
                'plan_id': status['plan_id'],
                'plan_name': status.get('plan_name', ''),
                'total_tasks': status.get('total_tasks', 0),
                'completed_tasks': status.get('completed_tasks', 0)
            })

            # 진행 상황 프로토콜로 출력
            if status.get('total_tasks', 0) > 0:
                self.global_protocol.progress(
                    status['plan_id'],
                    status['completed_tasks'],
                    status['total_tasks']
                )

    def create_workflow_plan(self, plan_name: str, tasks: list) -> Dict:
        '''워크플로우 계획 생성 - 통합 시스템 활용'''
        if not self.current_project:
            return {'error': 'No project selected'}

        manager = self.managers[self.current_project]

        # 통합 시스템으로 워크플로우 시작
        plan_id = manager.start_workflow(plan_name, tasks)

        # helpers의 워크플로우 데이터와 동기화
        workflow_data = {
            'plan_id': plan_id,
            'plan_name': plan_name,
            'tasks': tasks,
            'created_at': manager.workflow_state['started_at']
        }

        # memory에 저장 (기존 호환성 유지)
        workflow_dir = f'./memory/workflows/{self.current_project}'
        os.makedirs(workflow_dir, exist_ok=True)

        workflow_file = f'{workflow_dir}/workflow_{plan_id}.json'
        helpers.create_file(workflow_file, json.dumps(workflow_data, indent=2))

        return {
            'success': True,
            'plan_id': plan_id,
            'manager': manager
        }

    def execute_workflow_task(self, task: Dict) -> Dict:
        '''워크플로우 작업 실행 - 프로토콜 추적 포함'''
        if not self.current_project:
            return {'error': 'No project selected'}

        manager = self.managers[self.current_project]

        # 통합 시스템으로 작업 실행
        result = manager.execute_task(task)

        # 실행 결과를 memory에도 저장 (기존 호환성)
        self._save_task_result(task['id'], result)

        return result

    def _save_task_result(self, task_id: str, result: Dict) -> None:
        '''작업 결과 저장'''
        if not self.current_project:
            return

        # 결과 디렉토리
        results_dir = f'./memory/workflows/{self.current_project}/results'
        os.makedirs(results_dir, exist_ok=True)

        # 결과 파일 저장
        result_file = f'{results_dir}/task_{task_id}_result.json'
        helpers.create_file(result_file, json.dumps(result, indent=2))

    def get_workflow_status(self) -> Dict:
        '''현재 워크플로우 상태 조회'''
        if not self.current_project:
            return {'error': 'No project selected'}

        manager = self.managers[self.current_project]
        return manager.get_status()

    def checkpoint(self, name: str, data: Any) -> str:
        '''체크포인트 생성'''
        if not self.current_project:
            return 'ERROR: No project selected'

        manager = self.managers[self.current_project]
        return manager.checkpoint(name, data)

    def next_action(self, action: str, params: Dict) -> None:
        '''다음 작업 지시'''
        if not self.current_project:
            self.global_protocol.next_action(action, params)
            return

        manager = self.managers[self.current_project]
        manager.next_action(action, params)

    def get_execution_history(self) -> Dict:
        '''전체 실행 히스토리 조회'''
        history = {
            'projects': {},
            'global_executions': 0,
            'global_errors': 0
        }

        for project, manager in self.managers.items():
            status = manager.get_status()
            history['projects'][project] = status
            history['global_executions'] += status['execution']['total']
            history['global_errors'] += status['execution']['errors']

        return history

# 전역 어댑터 인스턴스 생성
workflow_adapter = WorkflowAdapter()

# helpers에 통합 함수 추가 (monkey patching)
if hasattr(helpers, '__class__'):
    # 기존 함수 백업
    helpers._original_flow_project = helpers.flow_project

    # 통합 버전으로 교체
    helpers.flow_project_integrated = lambda project: workflow_adapter.flow_project(project)
    helpers.create_workflow_plan = workflow_adapter.create_workflow_plan
    helpers.execute_workflow_task = workflow_adapter.execute_workflow_task
    helpers.get_workflow_status = workflow_adapter.get_workflow_status
    helpers.workflow_checkpoint = workflow_adapter.checkpoint
    helpers.workflow_next_action = workflow_adapter.next_action

    print("✅ Helpers에 통합 워크플로우 함수 추가 완료")
