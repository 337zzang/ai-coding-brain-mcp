"""
Flow Manager Utilities - Manager 관련 유틸리티 함수
분리일: 2025-08-03
원본: simple_flow_commands.py
"""

import os
import json
from datetime import datetime
from typing import Optional

from .ultra_simple_flow_manager import UltraSimpleFlowManager
from .project import get_current_project

# 전역 변수 (레거시 호환성)
_manager = None
_current_plan_id = None


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

def get_current_plan_id() -> Optional[str]:
    """현재 선택된 Plan ID 반환 (호환성 유지)"""
    api = get_flow_api_instance()
    return api._current_plan_id

def set_current_plan_id(plan_id: Optional[str]) -> None:
    """현재 Plan ID 설정 (호환성 유지)"""
    api = get_flow_api_instance()
    api._current_plan_id = plan_id
_current_project_path: Optional[str] = None  # @deprecated - use get_current_session().project_context

