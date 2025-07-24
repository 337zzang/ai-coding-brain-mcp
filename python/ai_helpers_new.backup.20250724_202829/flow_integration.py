"""
Flow 시스템 통합 모듈
- 단순 모드와 기존 모드 선택 가능
"""
import os
from typing import Optional, Union

# 환경변수로 모드 선택
FLOW_MODE = os.environ.get('FLOW_MODE', 'simple')  # 'simple' or 'legacy'


def get_flow_manager(project_path: Optional[str] = None) -> Union['SimpleFlowManager', 'FolderFlowManager']:
    """
    Flow Manager 인스턴스 반환

    환경변수 FLOW_MODE에 따라:
    - 'simple': 단순화된 시스템 (Flow ID 없음) - 기본값
    - 'legacy': 기존 시스템 (Flow ID 있음)
    """
    if FLOW_MODE == 'simple':
        from .simple_flow_manager import SimpleFlowManager
        return SimpleFlowManager(project_path)
    else:
        from .folder_flow_manager import FolderFlowManager
        return FolderFlowManager(project_path)


# 편의 함수들
def create_plan(name: str, description: str = ""):
    """Plan 생성 (현재 프로젝트)"""
    manager = get_flow_manager()

    if FLOW_MODE == 'simple':
        return manager.create_plan(name, description)
    else:
        # 기존 시스템은 flow_id 필요
        flow = manager.current_flow
        return manager.create_plan(flow.id, name)


def list_plans():
    """Plan 목록 (현재 프로젝트)"""
    manager = get_flow_manager()

    if FLOW_MODE == 'simple':
        return manager.list_plans()
    else:
        return manager.get_plans()


# ai_helpers_new/__init__.py에 추가
__all__ = [
    'get_flow_manager',
    'create_plan', 
    'list_plans',
    # ... 기타
]
