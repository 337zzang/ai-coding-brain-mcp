"""
통합 Flow Manager
레거시 없는 깔끔한 구조
"""
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

from .service.flow_service import FlowService
from .domain.models import Flow, Plan, Task, TaskStatus
from .exceptions import FlowError, ValidationError

logger = logging.getLogger(__name__)


class FlowManager:
    """
    통합 Flow Manager
    - 단순하고 직관적인 API
    - 3단계 상태 관리 (TODO, DOING, DONE)
    - Context 자동 통합
    """

    def __init__(self, base_path: str = '.ai-brain'):
        self._service = FlowService()
        self._current_flow_id: Optional[str] = None
        self._current_project: Optional[str] = None

    # === Flow 관리 ===

    def create_flow(self, name: str, project: Optional[str] = None) -> str:
        """Flow 생성 - flow_id 반환"""
        flow = self._service.create_flow(name, project or self._current_project)
        self._current_flow_id = flow.id
        return flow.id

    def select_flow(self, flow_id: str) -> bool:
        """Flow 선택"""
        if self._service.get_flow(flow_id):
            self._current_flow_id = flow_id
            self._service.current_flow = flow_id
            return True
        return False

    def get_current_flow(self) -> Optional[Flow]:
        """현재 선택된 Flow"""
        if self._current_flow_id:
            return self._service.get_flow(self._current_flow_id)
        return None

    def list_flows(self, project: Optional[str] = None) -> List[Dict[str, Any]]:
        """Flow 목록 (간단한 정보만)"""
        flows = self._service.list_flows(project)
        return [{
            'id': f.id,
            'name': f.name,
            'project': f.project,
            'created': f.created_at,
            'plans': len(f.plans),
            'tasks': len(f.get_all_tasks())
        } for f in flows]

    def delete_flow(self, flow_id: str) -> bool:
        """Flow 삭제"""
        if self._current_flow_id == flow_id:
            self._current_flow_id = None
        return self._service.delete_flow(flow_id)

    # === Plan 관리 ===

    def add_plan(self, name: str, description: str = "", flow_id: Optional[str] = None) -> str:
        """Plan 추가 - plan_id 반환"""
        flow_id = flow_id or self._current_flow_id
        if not flow_id:
            raise ValidationError("No flow selected")

        plan = self._service.add_plan(flow_id, name, description)
        return plan.id

    def get_plans(self, flow_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Plan 목록"""
        flow_id = flow_id or self._current_flow_id
        if not flow_id:
            return []

        plans = self._service.list_plans(flow_id)
        return [{
            'id': p.id,
            'name': p.name,
            'status': p.status,
            'tasks': len(p.tasks),
            'completed_tasks': sum(1 for t in p.tasks.values() if t.status == TaskStatus.DONE)
        } for p in plans]

    def complete_plan(self, plan_id: str) -> bool:
        """Plan 수동 완료"""
        if not self._current_flow_id:
            return False
        return self._service.complete_plan(self._current_flow_id, plan_id)

    # === Task 관리 ===

    def add_task(self, plan_id: str, name: str, description: str = "") -> str:
        """Task 추가 - task_id 반환"""
        if not self._current_flow_id:
            raise ValidationError("No flow selected")

        task = self._service.add_task(self._current_flow_id, plan_id, name, description)
        return task.id

    def get_tasks(self, plan_id: str) -> List[Dict[str, Any]]:
        """Task 목록"""
        if not self._current_flow_id:
            return []

        tasks = self._service.list_tasks(self._current_flow_id, plan_id)
        return [{
            'id': t.id,
            'name': t.name,
            'status': t.status.value,
            'created': t.created_at,
            'started': t.started_at,
            'completed': t.completed_at
        } for t in tasks]

    def start_task(self, task_id: str) -> bool:
        """Task 시작 (TODO → DOING)"""
        plan_id, task = self._find_task(task_id)
        if not plan_id:
            return False

        return self._service.start_task(self._current_flow_id, plan_id, task_id)

    def complete_task(self, task_id: str, message: str = "") -> bool:
        """Task 완료 (DOING → DONE)"""
        plan_id, task = self._find_task(task_id)
        if not plan_id:
            return False

        return self._service.complete_task(self._current_flow_id, plan_id, task_id, message)

    def update_task_status(self, task_id: str, status: str) -> bool:
        """Task 상태 직접 변경"""
        plan_id, task = self._find_task(task_id)
        if not plan_id:
            return False

        return self._service.update_task_status(self._current_flow_id, plan_id, task_id, status)

    # === Context 관리 ===

    def add_task_note(self, task_id: str, note: str) -> bool:
        """Task에 노트 추가"""
        plan_id, task = self._find_task(task_id)
        if not plan_id:
            return False

        return self._service.add_task_action(
            self._current_flow_id, plan_id, task_id, 'note', {'content': note}
        )

    def get_task_context(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Task Context 조회"""
        plan_id, task = self._find_task(task_id)
        if task:
            return task.context
        return None

    # === 조회 및 통계 ===

    def get_flow_summary(self, flow_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Flow 요약 정보"""
        flow_id = flow_id or self._current_flow_id
        flow = self._service.get_flow(flow_id) if flow_id else None

        if not flow:
            return None

        all_tasks = flow.get_all_tasks()
        return {
            'id': flow.id,
            'name': flow.name,
            'project': flow.project,
            'created': flow.created_at,
            'plans': {
                'total': len(flow.plans),
                'completed': sum(1 for p in flow.plans.values() if p.status == 'completed')
            },
            'tasks': {
                'total': len(all_tasks),
                'todo': sum(1 for t in all_tasks if t.status == TaskStatus.TODO),
                'doing': sum(1 for t in all_tasks if t.status == TaskStatus.DOING),
                'done': sum(1 for t in all_tasks if t.status == TaskStatus.DONE)
            }
        }

    def get_stats(self) -> Dict[str, Any]:
        """전체 통계"""
        return self._service.get_stats()

    def search_tasks(self, query: str) -> List[Tuple[str, str, Task]]:
        """Task 검색 - (flow_id, plan_id, task) 반환"""
        results = []
        query_lower = query.lower()

        for flow in self._service.list_flows(include_archived=False):
            for plan in flow.plans.values():
                for task in plan.tasks.values():
                    if (query_lower in task.name.lower() or 
                        query_lower in task.description.lower()):
                        results.append((flow.id, plan.id, task))

        return results

    # === 프로젝트 관리 ===

    def set_project(self, project: str):
        """현재 프로젝트 설정"""
        self._current_project = project
        self._service.current_project = project

    def get_project(self) -> Optional[str]:
        """현재 프로젝트"""
        return self._current_project

    # === 유틸리티 ===

    def _find_task(self, task_id: str) -> Tuple[Optional[str], Optional[Task]]:
        """Task 찾기 - (plan_id, task) 반환"""
        if not self._current_flow_id:
            return None, None

        for plan_id, task in self._service.get_all_tasks(self._current_flow_id):
            if task.id == task_id:
                return plan_id, task

        return None, None

    def reload(self):
        """데이터 새로고침"""
        self._service.reload()
