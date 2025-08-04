"""
Flow API - 핵심 비즈니스 로직
분리일: 2025-08-03
원본: simple_flow_commands.py
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from .domain.models import Plan, Task, TaskStatus
from .ultra_simple_flow_manager import UltraSimpleFlowManager
from .repository.ultra_simple_repository import UltraSimpleRepository
from .task_logger import EnhancedTaskLogger
# Response helpers
def ok_response(data=None, message=None):
    response = {'ok': True}
    if data is not None: response['data'] = data
    if message: response['message'] = message
    return response

def error_response(error, data=None):
    response = {'ok': False, 'error': error}
    if data is not None: response['data'] = data
    return response
# from .flow_manager_utils import _generate_plan_id, _generate_task_id  # Not needed

# 필요한 추가 import들


# Helper functions
def get_manager() -> UltraSimpleFlowManager:
    """현재 프로젝트의 매니저 가져오기 (Session 기반)

    이 함수는 기존 코드와의 호환성을 위해 유지됩니다.
    내부적으로는 새로운 Session 시스템을 사용하며,
    ManagerAdapter를 통해 기존 인터페이스를 제공합니다.
    """
    # Get current session
    session = get_current_session()

    # Check if session is initialized with a project
    if not session.is_initialized:
        # Initialize with current directory
        project_path = os.getcwd()
        project_name = os.path.basename(project_path)
        session.set_project(project_name, project_path)

        # Notification about .ai-brain directory
        ai_brain_path = os.path.join(project_path, '.ai-brain', 'flow')
        if not os.path.exists(ai_brain_path):
            print(f"📁 새로운 Flow 저장소 생성: {project_name}/.ai-brain/flow/")
        else:
            print(f"📁 Flow 저장소 사용: {project_name}/.ai-brain/flow/")

    # Return adapter for backward compatibility
    # The adapter makes ContextualFlowManager look like UltraSimpleFlowManager
    return ManagerAdapter(session.flow_manager)



# Helper functions for converting domain objects to dicts
def _plan_to_dict(plan) -> Dict[str, Any]:
    """Convert Plan object to dict"""
    if isinstance(plan, dict):
        return plan

    return {
        'id': plan.id,
        'name': plan.name,
        'created_at': getattr(plan, 'created_at', ''),
        'updated_at': getattr(plan, 'updated_at', ''),
        'status': getattr(plan, 'status', 'active'),
        'metadata': getattr(plan, 'metadata', {}),
        'tasks': {
            task_id: _task_to_dict(task)
            for task_id, task in plan.tasks.items()
        } if hasattr(plan, 'tasks') else {}
    }

def _task_to_dict(task) -> Dict[str, Any]:
    """Convert Task object to dict"""
    if isinstance(task, dict):
        return task

    return {
        'id': task.id,
        'title': getattr(task, 'title', getattr(task, 'name', '')),
        'description': getattr(task, 'description', ''),
        'status': str(getattr(task, 'status', 'todo')),
        'created_at': getattr(task, 'created_at', ''),
        'updated_at': getattr(task, 'updated_at', ''),
        'priority': getattr(task, 'priority', 'normal'),
        'completed_at': getattr(task, 'completed_at', None)
    }

class FlowAPI:
    """Flow 시스템을 위한 고급 API

    Manager의 모든 기능 + 추가 기능들:
    - Context 기반 상태 관리 (전역 변수 없음)
    - 체이닝 가능한 메서드
    - 더 상세한 필터링과 검색
    """

    def __init__(self, manager: Optional[UltraSimpleFlowManager] = None):
        """FlowAPI 초기화

        Args:
            manager: 기존 매니저 인스턴스 (없으면 새로 생성)
        """
        self._manager = manager or UltraSimpleFlowManager()
        self._current_plan_id: Optional[str] = None
        self._context: Dict[str, Any] = {}
        self.last_resp: Optional[Dict[str, Any]] = None

    # Plan 관리 메서드

    def _res(self, ok: bool = True, data: Any = None, error: str = '') -> Dict[str, Any]:
        """표준 응답 형식 생성 헬퍼"""
        self.last_resp = {'ok': ok, 'data': data, 'error': error}
        return self.last_resp

    def _sync(self, plan_id: str) -> None:
        """Repository와 Manager 상태 동기화"""
        if hasattr(self._manager, 'refresh'):
            self._manager.refresh(plan_id)

    def create_plan(self, name: str, description: str = "") -> Dict[str, Any]:
        """새 Plan 생성"""
        plan = self._manager.create_plan(name)
        if description:
            plan.metadata["description"] = description
        self._current_plan_id = plan.id
        return self._res(True, _plan_to_dict(plan))

    def select_plan(self, plan_id: str) -> "FlowAPI":
        """Plan 선택 (체이닝 가능)"""
        plan = self._manager.get_plan(plan_id)
        if plan:
            self._current_plan_id = plan_id
            self._res(True, {'plan_id': plan_id, 'name': plan.name})
        else:
            self._res(False, None, f"Plan {plan_id} not found")
        return self


    def get_current_plan(self) -> Dict[str, Any]:
        """현재 선택된 Plan 정보 반환"""
        if self._current_plan_id:
            plan = self._manager.get_plan(self._current_plan_id)
            if plan:
                return self._res(True, _plan_to_dict(plan))
            else:
                return self._res(False, None, f"Plan {self._current_plan_id} not found")
        return self._res(False, None, "No plan selected")

    def list_plans(self, status: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """Plan 목록 조회 (필터링 가능)"""
        try:
            plans = self._manager.list_plans()
            if status:
                plans = [p for p in plans if p.status == status]
            plan_dicts = [_plan_to_dict(p) for p in plans[:limit]]
            return self._res(True, plan_dicts)
        except Exception as e:
            return self._res(False, None, str(e))

    def get_plan(self, plan_id: str) -> Dict[str, Any]:
        """특정 Plan 정보 가져오기"""
        plan = self._manager.get_plan(plan_id)
        if plan:
            return self._res(True, _plan_to_dict(plan))
        return self._res(False, None, f"Plan {plan_id} not found")

    def update_plan(self, plan_id: str, **kwargs) -> Dict[str, Any]:
        """Plan 정보 업데이트"""
        plan = self._manager.get_plan(plan_id)
        if not plan:
            return self._res(False, None, f"Plan {plan_id} not found")

        # 업데이트 가능한 필드들
        if "name" in kwargs:
            plan.name = kwargs["name"]
        if "description" in kwargs and hasattr(plan, 'metadata'):
            plan.metadata["description"] = kwargs["description"]
        if "status" in kwargs:
            plan.status = kwargs["status"]

        plan.updated_at = datetime.now().isoformat()
        if hasattr(self._manager, 'save_index'):
            self._manager.save_index()
        self._sync(plan_id)

        return self._res(True, _plan_to_dict(plan))

    def delete_plan(self, plan_id: str) -> Dict[str, Any]:
        """Plan 삭제"""
        success = self._manager.delete_plan(plan_id)
        if success and self._current_plan_id == plan_id:
            self._current_plan_id = None
        return self._res(success, {'deleted': plan_id} if success else None,
                        '' if success else f"Failed to delete plan {plan_id}")

    def create_task(self, plan_id: str, name: str, description: str = "") -> Dict[str, Any]:
        """Task 생성"""
        task = self._manager.create_task(plan_id, name)
        if task:
            if description and hasattr(task, 'description'):
                task.description = description
            self._sync(plan_id)
            return self._res(True, _task_to_dict(task))
        return self._res(False, None, f"Failed to create task in plan {plan_id}")

    def add_task(self, plan_id: str, title: str, **kwargs) -> Dict[str, Any]:
        """Task 추가 (create_task의 별칭)"""
        description = kwargs.get('description', '')
        return self.create_task(plan_id, title, description)

    def get_task(self, plan_id: str, task_id: str) -> Dict[str, Any]:
        """특정 Task 조회"""
        plan = self._manager.get_plan(plan_id)
        if not plan:
            return self._res(False, None, f"Plan {plan_id} not found")

        if hasattr(plan, 'tasks') and task_id in plan.tasks:
            task = plan.tasks[task_id]
            return self._res(True, _task_to_dict(task))
        return self._res(False, None, f"Task {task_id} not found")

    def get_task_by_number(self, plan_id: str, number: int) -> Dict[str, Any]:
        """번호로 Task 조회"""
        plan = self._manager.get_plan(plan_id)
        if not plan:
            return self._res(False, None, f"Plan {plan_id} not found")

        # Task 목록을 번호 순으로 정렬
        tasks = list(plan.tasks.values())
        if 0 < number <= len(tasks):
            task = tasks[number - 1]  # 1-based index
            return self._res(True, _task_to_dict(task))
        return self._res(False, None, f"Task number {number} not found (1-{len(tasks)})")
    
    def list_tasks(self, plan_id: str, status: Optional[str] = None) -> Dict[str, Any]:
        """Task 목록 조회"""
        plan = self._manager.get_plan(plan_id)
        if not plan:
            return self._res(False, None, f"Plan {plan_id} not found")

        tasks = []
        if hasattr(plan, 'tasks'):
            for task in plan.tasks.values():
                task_dict = _task_to_dict(task)
                if not status or task_dict.get('status') == status:
                    tasks.append(task_dict)

        return self._res(True, tasks)

    def update_task(self, plan_id: str, task_id: str, **kwargs) -> Dict[str, Any]:
        """Task 정보 업데이트"""
        plan = self._manager.get_plan(plan_id)
        if not plan:
            return self._res(False, None, f"Plan {plan_id} not found")

        if not hasattr(plan, 'tasks') or task_id not in plan.tasks:
            return self._res(False, None, f"Task {task_id} not found")

        task = plan.tasks[task_id]

        # 업데이트 가능한 필드들
        for field in ['title', 'description', 'status', 'priority']:
            if field in kwargs:
                setattr(task, field, kwargs[field])

        if hasattr(task, 'updated_at'):
            task.updated_at = datetime.now().isoformat()

        if hasattr(self._manager, 'save_index'):
            self._manager.save_index()
        self._sync(plan_id)

        return self._res(True, _task_to_dict(task))

    def update_task_status(self, plan_id: str, task_id: str, status: str) -> Dict[str, Any]:
        """Task 상태 업데이트 (편의 메서드)"""
        return self.update_task(plan_id, task_id, status=status)

    def search(self, query: str) -> Dict[str, Any]:
        """Plan과 Task 통합 검색"""
        query_lower = query.lower()

        # Plan 검색
        plans = []
        all_plans = self._manager.list_plans()
        for plan in all_plans:
            if query_lower in plan.name.lower():
                plans.append(_plan_to_dict(plan))

        # Task 검색
        tasks = []
        for plan in all_plans:
            if hasattr(plan, 'tasks'):
                for task_id, task in plan.tasks.items():
                    task_dict = _task_to_dict(task)
                    if query_lower in task_dict.get('title', '').lower() or                        query_lower in task_dict.get('description', '').lower():
                        task_dict['plan_id'] = plan.id
                        tasks.append(task_dict)

        return self._res(True, {'plans': plans, 'tasks': tasks})

    def get_stats(self) -> Dict[str, Any]:
        """전체 통계 정보"""
        plans = self._manager.list_plans()
        total_tasks = 0
        task_stats = {"todo": 0, "in_progress": 0, "done": 0}

        for plan in plans:
            if hasattr(plan, 'tasks'):
                total_tasks += len(plan.tasks)
                for task in plan.tasks.values():
                    status = str(getattr(task, 'status', 'todo')).lower()
                    if 'done' in status or 'completed' in status:
                        task_stats['done'] += 1
                    elif 'progress' in status:
                        task_stats['in_progress'] += 1
                    else:
                        task_stats['todo'] += 1

        stats = {
            "total_plans": len(plans),
            "total_tasks": total_tasks,
            "tasks_by_status": task_stats,
            "current_plan": self._current_plan_id
        }

        return self._res(True, stats)

    def set_context(self, key: str, value: Any) -> "FlowAPI":
        """컨텍스트 설정 (체이닝 가능)"""
        self._context[key] = value
        self._res(True, {key: value})
        return self

    def get_context(self, key: str) -> Any:
        """컨텍스트 조회"""
        return self._context.get(key)

    def clear_context(self) -> "FlowAPI":
        """컨텍스트 초기화 (체이닝 가능)"""
        self._context.clear()
        self._current_plan_id = None
        self._res(True, {})
        return self


# 싱글톤 인스턴스 관리
_flow_api_instance = None


def get_flow_api() -> FlowAPI:
    """FlowAPI 싱글톤 인스턴스 반환"""
    global _flow_api_instance
    if _flow_api_instance is None:
        _flow_api_instance = FlowAPI()
    return _flow_api_instance