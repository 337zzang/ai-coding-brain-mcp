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
from .repository.flow_repository import FlowRepository
from .service.task_logger import EnhancedTaskLogger
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
from .flow_manager_utils import _generate_plan_id, _generate_task_id

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
        self.manager = manager or get_manager()
        self._current_plan_id: Optional[str] = None
        self._context: Dict[str, Any] = {}

    # Plan 관리 메서드
    def create_plan(self, name: str, description: str = "") -> Dict[str, Any]:
        """새 Plan 생성"""
        plan = self.manager.create_plan(name)
        if description:
            plan.metadata["description"] = description
        self._current_plan_id = plan.id
        return _plan_to_dict(plan)

    def select_plan(self, plan_id: str) -> "FlowAPI":
        """Plan 선택 (체이닝 가능)"""
        plan = self.manager.get_plan(plan_id)
        if plan:
            self._current_plan_id = plan_id
        else:
            raise ValueError(f"Plan {plan_id} not found")
        return self

    def get_current_plan(self) -> Optional[Dict[str, Any]]:
        """현재 선택된 Plan 정보"""
        if self.get_current_plan_id():
            plan = self.manager.get_plan(self.get_current_plan_id())
            return _plan_to_dict(plan) if plan else None
        return None

    def list_plans(self, status: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Plan 목록 조회 (필터링 가능)"""
        plans = self.manager.list_plans()
        if status:
            plans = [p for p in plans if p.status == status]
        return [_plan_to_dict(p) for p in plans[:limit]]

    def update_plan(self, plan_id: str, **kwargs) -> Dict[str, Any]:
        """Plan 정보 업데이트"""
        plan = self.manager.get_plan(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        # 업데이트 가능한 필드들
        if "name" in kwargs:
            plan.name = kwargs["name"]
        if "description" in kwargs:
            plan.metadata["description"] = kwargs["description"]
        if "status" in kwargs:
            plan.status = kwargs["status"]

        plan.updated_at = datetime.now().isoformat()
        self.manager.save_index()
        return _plan_to_dict(plan)

    def delete_plan(self, plan_id: str) -> bool:
        """Plan 삭제"""
        return self.manager.delete_plan(plan_id)

    # Task 관리 메서드
    def add_task(self, plan_id: str, title: str, **kwargs) -> Dict[str, Any]:
        """Task 추가 (plan_id 명시적 지정)"""
        task = self.manager.create_task(plan_id, title)

        # 추가 속성 설정
        if "description" in kwargs:
            task.description = kwargs["description"]
        if "priority" in kwargs:
            task.priority = kwargs["priority"]
        if "tags" in kwargs:
            task.tags = kwargs["tags"]

        return _task_to_dict(task)

    def get_task(self, plan_id: str, task_id: str) -> Optional[Dict[str, Any]]:
        """특정 Task 조회"""
        plan = self.manager.get_plan(plan_id)
        if plan and task_id in plan.tasks:
            return _task_to_dict(plan.tasks[task_id])
        return None

    def list_tasks(self, plan_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Task 목록 조회"""
        plan = self.manager.get_plan(plan_id)
        if not plan:
            return []

        tasks = list(plan.tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]

        return [_task_to_dict(t) for t in tasks]

    def update_task(self, plan_id: str, task_id: str, **kwargs) -> Dict[str, Any]:
        """Task 정보 업데이트"""
        plan = self.manager.get_plan(plan_id)
        if not plan or task_id not in plan.tasks:
            raise ValueError(f"Task {task_id} not found in plan {plan_id}")

        task = plan.tasks[task_id]

        # 업데이트 가능한 필드들
        if "title" in kwargs:
            task.title = kwargs["title"]
        if "status" in kwargs:
            self.manager.update_task_status(plan_id, task_id, kwargs["status"])
        if "description" in kwargs:
            task.description = kwargs["description"]
        if "priority" in kwargs:
            task.priority = kwargs["priority"]

        task.updated_at = datetime.now().isoformat()
        self.manager.save_index()
        return _task_to_dict(task)

    def start_task(self, task_id: str) -> Dict[str, Any]:
        """Task 시작 (현재 Plan 컨텍스트 사용)"""
        if not self.get_current_plan_id():
            raise ValueError("No plan selected. Use select_plan() first.")
        return self.update_task(self.get_current_plan_id(), task_id, status="in_progress")

    def complete_task(self, task_id: str) -> Dict[str, Any]:
        """Task 완료 (현재 Plan 컨텍스트 사용)"""
        if not self.get_current_plan_id():
            raise ValueError("No plan selected. Use select_plan() first.")
        return self.update_task(self.get_current_plan_id(), task_id, status="done")

    # 고급 기능
    def get_stats(self) -> Dict[str, Any]:
        """전체 통계 정보"""
        plans = self.manager.list_plans()
        total_tasks = sum(len(p.tasks) for p in plans)

        task_stats = {"todo": 0, "in_progress": 0, "done": 0}
        for plan in plans:
            for task in plan.tasks.values():
                task_stats[task.status] = task_stats.get(task.status, 0) + 1

        return {
            "total_plans": len(plans),
            "active_plans": len([p for p in plans if p.status == "active"]),
            "total_tasks": total_tasks,
            "tasks_by_status": task_stats,
            "current_plan_id": self.get_current_plan_id()
        }

    def search(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """Plan과 Task 통합 검색"""
        query_lower = query.lower()

        # Plan 검색
        plans = []
        for plan in self.manager.list_plans():
            if query_lower in plan.name.lower():
                plans.append(_plan_to_dict(plan))

        # Task 검색
        tasks = []
        for plan in self.manager.list_plans():
            for task in plan.tasks.values():
                if query_lower in task.title.lower():
                    task_dict = _task_to_dict(task)
                    task_dict["plan_id"] = plan.id
                    task_dict["plan_name"] = plan.name
                    tasks.append(task_dict)

        return {"plans": plans, "tasks": tasks}

    # Context 관리
    def set_context(self, key: str, value: Any) -> "FlowAPI":
        """컨텍스트 설정 (체이닝 가능)"""
        self._context[key] = value
        return self

    def get_context(self, key: str) -> Any:
        """컨텍스트 조회"""
        return self._context.get(key)

    def clear_context(self) -> "FlowAPI":
        """컨텍스트 초기화"""
        self._context.clear()
        self._current_plan_id = None
        return self


