"""
AI Helpers New - Flow 시스템 v2.0
레거시 제거, 완전 리팩토링 버전
"""

# 도메인 모델
from .domain.models import Flow, Plan, Task, TaskStatus

# 저장소
from .repository.json_repository import JsonRepository

# 서비스
from .service.flow_service import FlowService

# 매니저
from .flow_manager import FlowManager

# 명령어
from .commands import CommandRouter, command

# 워크플로우
from .workflow_commands import (
    wf, 
    help_wf,
    current_flow,
    current_project,
    set_project,
    get_flow_manager
)

# Context (더미 - 호환성)
class ContextIntegration:
    """레거시 호환용 더미"""
    def record_flow_action(self, *args, **kwargs):
        pass
    def record_doc_action(self, *args, **kwargs):
        pass

# 레거시 호환 (임시)
FlowManagerUnified = FlowManager
LegacyFlowAdapter = FlowManager

# 초기화
import logging
logging.basicConfig(level=logging.INFO)

__version__ = "2.0.0"

__all__ = [
    # 핵심
    'FlowManager',
    'CommandRouter',
    'wf',
    'help_wf',

    # 모델
    'Flow',
    'Plan', 
    'Task',
    'TaskStatus',

    # 유틸리티
    'current_flow',
    'current_project',
    'set_project',

    # 레거시 호환
    'FlowManagerUnified',
    'LegacyFlowAdapter',
    'ContextIntegration'
]

# 초기화 메시지는 실제 사용시에만
print("✅ Flow 시스템 v2.0 로드됨")
