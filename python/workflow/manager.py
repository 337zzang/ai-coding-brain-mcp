"""
Workflow Manager Adapter
========================
기존 WorkflowManager API를 새로운 WorkflowEngine으로 매핑
"""

from typing import Dict, Optional, Any
from .core.workflow_engine import WorkflowEngine
from .core.state_manager import TaskState


class WorkflowManager:
    """기존 API 호환성을 위한 어댑터"""

    _instances: Dict[str, 'WorkflowManager'] = {}

    def __init__(self, project_name: str):
        # 새로운 엔진 사용
        self.engine = WorkflowEngine(project_name)
        self.project_name = project_name

    @classmethod
    def get_instance(cls, project_name: str) -> 'WorkflowManager':
        """싱글톤 인스턴스 반환 (기존 API 호환)"""
        if project_name not in cls._instances:
            cls._instances[project_name] = cls(project_name)
        return cls._instances[project_name]

    # 기존 API 메서드들을 새 엔진으로 매핑

    def start_plan(self, name: str, description: str = "") -> str:
        """플랜 시작 (워크플로우 생성 및 시작)"""
        workflow_id = self.engine.create_workflow(name, description)
        self.engine.start_workflow(workflow_id)
        return workflow_id

    def add_task(self, title: str, description: str = "") -> str:
        """태스크 추가"""
        return self.engine.add_task(title, description)

    def start_task(self, task_id: str) -> bool:
        """태스크 시작"""
        return self.engine.start_task(task_id)

    def complete_task(self, task_id: str, note: str = "") -> bool:
        """태스크 완료"""
        return self.engine.complete_task(task_id, note)

    def fail_task(self, task_id: str, error: str) -> bool:
        """태스크 실패"""
        return self.engine.fail_task(task_id, error)

    def get_current_task(self) -> Optional[Dict[str, Any]]:
        """현재 활성 태스크 조회"""
        if self.engine.active_task_id:
            return self.engine.storage.load_task(self.engine.active_task_id)
        return None

    def get_status(self) -> Dict[str, Any]:
        """상태 조회"""
        status = self.engine.get_status()

        # 기존 API 형식으로 변환
        return {
            'status': 'active' if self.engine.active_workflow_id else 'idle',
            'plan_id': self.engine.active_workflow_id,
            'plan_name': status.get('workflow_name'),
            'current_task': self.get_current_task(),
            'total_tasks': status.get('tasks_in_workflow', 0)
        }

    def process_command(self, command: str) -> Dict[str, Any]:
        """명령 처리 (기존 API 호환)"""
        # 간단한 명령 파싱
        parts = command.strip().split(None, 1)
        if not parts:
            return {'success': False, 'message': 'Empty command'}

        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ''

        if cmd in ['/start', '/s']:
            plan_id = self.start_plan(args)
            return {'success': True, 'plan_id': plan_id}

        elif cmd in ['/task', '/t']:
            task_id = self.add_task(args)
            return {'success': True, 'task_id': task_id}

        elif cmd in ['/complete', '/c']:
            success = self.complete_task(self.engine.active_task_id, args)
            return {'success': success}

        elif cmd in ['/status']:
            return {'success': True, 'status': self.get_status()}

        else:
            return {'success': False, 'message': f'Unknown command: {cmd}'}
