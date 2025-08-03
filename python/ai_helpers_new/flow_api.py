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
        self._manager = manager or get_manager()
        self._current_plan_id: Optional[str] = None
        self._context: Dict[str, Any] = {}

    # Plan 관리 메서드
    def create_plan(self, name: str, description: str = "") -> Dict[str, Any]:
        """새 Plan 생성"""
        plan = self._manager.create_plan(name)
        if description:
            plan.metadata["description"] = description
        self._current_plan_id = plan.id
        return _plan_to_dict(plan)

    def select_plan(self, plan_id: str) -> "FlowAPI":
        """Plan 선택 (체이닝 가능)"""
        plan = self._manager.get_plan(plan_id)
        if plan:
            self._current_plan_id = plan_id
            self._res(True, {'plan_id': plan_id, 'name': plan.name})
        else:
            self._res(False, None, f"Plan {plan_id} not found")
        return self