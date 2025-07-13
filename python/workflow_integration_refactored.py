"""
Workflow Integration - Event-Based
==================================

이벤트 기반으로 리팩토링된 워크플로우 통합 모듈입니다.
더 이상 직접적인 상호 참조 없이 EventBus를 통해 통신합니다.
"""

import logging
from typing import Optional

from python.workflow.event_bus import event_bus
from python.workflow.event_types import EventType, create_project_event

logger = logging.getLogger(__name__)

# 전역 WorkflowManager 인스턴스 딕셔너리
_workflow_managers = {}


def switch_project_workflow(project_name: str):
    """
    프로젝트 전환 (이벤트 기반)

    이제 이 함수는 더 이상 필요하지 않지만, 
    하위 호환성을 위해 유지합니다.

    PROJECT_SWITCHED 이벤트를 구독하는 WorkflowManager가
    자체적으로 전환을 처리합니다.
    """
    logger.warning(
        "switch_project_workflow is deprecated. "
        "Use event-based project switching instead."
    )

    # 하위 호환성을 위해 이벤트 발행
    event = create_project_event(
        EventType.PROJECT_SWITCHED,
        project_name=project_name
    )
    event_bus.publish(event)


def get_workflow_manager(project_name: str):
    """
    프로젝트별 WorkflowManager 인스턴스 조회

    이벤트 기반 아키텍처에서는 직접 호출보다
    이벤트를 통한 통신을 권장합니다.
    """
    from python.workflow.manager import WorkflowV3Manager
    from python.workflow.workflow_event_adapter import inject_event_publishing

    if project_name not in _workflow_managers:
        # 새 인스턴스 생성
        manager = WorkflowV3Manager(project_name)

        # 이벤트 발행 기능 주입
        inject_event_publishing(manager)

        _workflow_managers[project_name] = manager
        logger.info(f"Created WorkflowManager for project: {project_name}")

    return _workflow_managers[project_name]


def cleanup_workflow_manager(project_name: str):
    """
    WorkflowManager 인스턴스 정리
    """
    if project_name in _workflow_managers:
        manager = _workflow_managers[project_name]

        # EventAdapter 정리
        if hasattr(manager, '_event_adapter'):
            manager._event_adapter.cleanup()

        # 상태 저장
        manager.save_data()

        # 인스턴스 제거
        del _workflow_managers[project_name]

        logger.info(f"Cleaned up WorkflowManager for project: {project_name}")


# === 이벤트 핸들러 등록 (모듈 로드 시) ===

def _on_project_switched(event):
    """PROJECT_SWITCHED 이벤트 핸들러"""
    if hasattr(event, 'project_name'):
        project_name = event.project_name

        # WorkflowManager 인스턴스 확인/생성
        manager = get_workflow_manager(project_name)

        # 상태 로드
        manager.load_data()

        logger.info(f"WorkflowManager switched to project: {project_name}")


# 이벤트 핸들러 등록
event_bus.subscribe(EventType.PROJECT_SWITCHED.value, _on_project_switched)

logger.info("Workflow integration initialized with event-based architecture")
