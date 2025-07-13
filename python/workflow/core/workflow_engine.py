"""
Workflow Engine
===============
상태 기반 워크플로우 엔진 - 기존 manager.py를 대체
"""

from typing import Dict, List, Optional, Any
import uuid
import time
from datetime import datetime
from contextlib import contextmanager

from .state_manager import StateManager, WorkflowState, TaskState
from ..messaging.message_controller import MessageController
from .storage import WorkflowStorage


class WorkflowEngine:
    """워크플로우 엔진 - 핵심 로직만 포함"""

    def __init__(self, project_name: str, config: Optional[Dict] = None):
        self.project_name = project_name
        self.config = config or {}

        # 핵심 컴포넌트
        self.state_manager = StateManager()
        self.storage = WorkflowStorage(project_name)
        self.msg = MessageController(self.config.get('messaging', {}))

        # 현재 활성 워크플로우
        self.active_workflow_id: Optional[str] = None
        self.active_task_id: Optional[str] = None

        # 로드
        self._load_state()

    def create_workflow(self, name: str, description: str = "") -> str:
        """새 워크플로우 생성"""
        workflow_id = str(uuid.uuid4())

        workflow_data = {
            'id': workflow_id,
            'name': name,
            'description': description,
            'created_at': datetime.now().isoformat(),
            'tasks': []
        }

        # 상태 설정
        self.state_manager.set_workflow_state(workflow_id, WorkflowState.DRAFT)

        # 저장
        self.storage.save_workflow(workflow_id, workflow_data)

        # 메시지 발행
        self.msg.emit('workflow_created', workflow_id, {
            'name': name,
            'description': description
        })

        return workflow_id

    def start_workflow(self, workflow_id: str) -> bool:
        """워크플로우 시작"""
        # 상태 전이
        transition = self.state_manager.set_workflow_state(workflow_id, WorkflowState.ACTIVE)
        if not transition:
            return False

        self.active_workflow_id = workflow_id

        # 메시지 발행
        self.msg.emit_transition(workflow_id, *transition.split('>'), {
            'workflow_id': workflow_id
        })

        return True

    def add_task(self, title: str, description: str = "") -> str:
        """현재 워크플로우에 태스크 추가"""
        if not self.active_workflow_id:
            raise ValueError("No active workflow")

        task_id = str(uuid.uuid4())

        task_data = {
            'id': task_id,
            'title': title,
            'description': description,
            'created_at': datetime.now().isoformat(),
            'workflow_id': self.active_workflow_id
        }

        # 상태 설정
        self.state_manager.set_task_state(task_id, TaskState.PENDING)

        # 워크플로우에 태스크 추가
        workflow = self.storage.load_workflow(self.active_workflow_id)
        workflow['tasks'].append(task_id)
        self.storage.save_workflow(self.active_workflow_id, workflow)

        # 태스크 저장
        self.storage.save_task(task_id, task_data)

        # 메시지 발행
        self.msg.emit('task_added', task_id, {
            'title': title,
            'workflow_id': self.active_workflow_id
        })

        return task_id

    def start_task(self, task_id: str) -> bool:
        """태스크 시작"""
        # 상태 전이
        transition = self.state_manager.set_task_state(task_id, TaskState.ACTIVE)
        if not transition:
            return False

        self.active_task_id = task_id

        # 컨텍스트 수집
        context = {
            'git_status': self._get_git_status(),
            'start_time': time.time()
        }

        # 메시지 발행
        self.msg.emit_transition(task_id, *transition.split('>'), context)

        return True

    def complete_task(self, task_id: str, summary: str = "") -> bool:
        """태스크 완료"""
        # 상태 전이
        transition = self.state_manager.set_task_state(task_id, TaskState.COMPLETED)
        if not transition:
            return False

        # 태스크 데이터 업데이트
        task = self.storage.load_task(task_id)
        task['completed_at'] = datetime.now().isoformat()
        task['summary'] = summary
        self.storage.save_task(task_id, task)

        # 통계 수집
        stats = {
            'duration': time.time() - task.get('start_time', time.time()),
            'summary': summary
        }

        # 메시지 발행
        self.msg.emit_transition(task_id, *transition.split('>'))
        self.msg.emit_summary(task_id, 'completed', stats)

        # 활성 태스크 해제
        if self.active_task_id == task_id:
            self.active_task_id = None

        return True

    def fail_task(self, task_id: str, error: str) -> bool:
        """태스크 실패"""
        # 상태 전이
        transition = self.state_manager.set_task_state(task_id, TaskState.FAILED)
        if not transition:
            return False

        # 에러 메시지 발행
        self.msg.emit_error(task_id, 'task_failed', error)

        return True

    @contextmanager
    def task_execution(self, task_id: str):
        """태스크 실행 컨텍스트 (자동 시작/완료/실패 처리)"""
        self.start_task(task_id)
        try:
            with self.msg.suppress():  # 실행 중 메시지 억제
                yield
            self.complete_task(task_id)
        except Exception as e:
            self.fail_task(task_id, str(e))
            raise

    def get_status(self) -> Dict[str, Any]:
        """현재 상태 조회"""
        status = {
            'project': self.project_name,
            'active_workflow': self.active_workflow_id,
            'active_task': self.active_task_id,
            'workflow_count': len(self.state_manager.workflow_states),
            'task_count': len(self.state_manager.task_states)
        }

        if self.active_workflow_id:
            workflow = self.storage.load_workflow(self.active_workflow_id)
            status['workflow_name'] = workflow.get('name')
            status['tasks_in_workflow'] = len(workflow.get('tasks', []))

        return status

    def _get_git_status(self) -> Dict[str, Any]:
        """Git 상태 조회"""
        try:
            # helpers가 있으면 사용
            if 'helpers' in globals():
                git_status = helpers.git_status()
                return {
                    'modified': len(git_status.get('modified', [])),
                    'untracked': git_status.get('untracked_count', 0)
                }
        except:
            pass
        return {'modified': 0, 'untracked': 0}

    def _load_state(self):
        """저장된 상태 로드"""
        # 추후 구현
        pass

    def _save_state(self):
        """현재 상태 저장"""
        # 추후 구현  
        pass
