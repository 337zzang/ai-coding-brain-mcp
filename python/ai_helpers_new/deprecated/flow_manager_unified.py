# flow_manager_unified.py
"""
FlowManagerUnified - 새로운 FlowManager로의 리다이렉트
레거시 호환성을 위해 유지
"""

import warnings
from .flow_manager import FlowManager
from .legacy_flow_adapter import LegacyFlowAdapter


class FlowManagerUnified(LegacyFlowAdapter):
    """
    기존 FlowManagerUnified 인터페이스 유지
    내부적으로는 새로운 FlowManager 사용
    """

    def __init__(self, context_manager=None, repository=None):
        # 레거시 파라미터 무시
        if repository or context_manager:
            warnings.warn(
                "repository와 context_manager 파라미터는 더 이상 사용되지 않습니다.",
                DeprecationWarning,
                stacklevel=2
            )

        # 새로운 FlowManager 사용
        manager = FlowManager(context_enabled=True)
        super().__init__(manager)

        # 추가 호환성
        self.repository = None  # 레거시 코드를 위해
        self.context_manager = context_manager

    def handle_command(self, command: str):
        """레거시 명령어 처리"""
        # 새 시스템에서는 직접 메서드 호출
        warnings.warn(
            "handle_command는 더 이상 사용되지 않습니다. 직접 메서드를 호출하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        return {"ok": False, "error": "handle_command is deprecated"}


# 레거시 import를 위한 별칭
FlowManagerWithContext = FlowManagerUnified


def get_flow_manager_unified(**kwargs):
    """팩토리 함수 (레거시)"""
    return FlowManagerUnified(**kwargs)
