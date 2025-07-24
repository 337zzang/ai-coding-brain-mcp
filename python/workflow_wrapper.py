"""
워크플로우 래퍼 - FlowManagerUnified 사용
"""
import os
from typing import Dict, Any, Optional

# 전역 매니저 인스턴스
_manager: Optional[Any] = None

def get_workflow_manager():
    """워크플로우 매니저 인스턴스 가져오기"""
    global _manager

    if _manager is None:
        try:
            # o3 권장사항: LegacyFlowAdapter를 통해 연결
            from ai_helpers_new.flow_manager import FlowManager
            from ai_helpers_new.legacy_flow_adapter import LegacyFlowAdapter
            from ai_helpers_new.flow_command_router import FlowCommandRouter

            flow_manager = FlowManager(context_enabled=True)
            adapter = LegacyFlowAdapter(flow_manager)
            _manager = FlowCommandRouter(adapter)
            print("✅ FlowManager + LegacyFlowAdapter + FlowCommandRouter 초기화됨")
        except ImportError as e:
            print(f"⚠️ import 실패: {e}")
            # Fallback to FlowManagerUnified
            try:
                from ai_helpers_new.flow_manager_unified import FlowManagerUnified
                _manager = FlowManagerUnified()
                print("⚠️ FlowManagerUnified로 fallback")
            except ImportError:
                print("❌ 워크플로우 매니저를 찾을 수 없습니다")
                _manager = None

    return _manager

def wf(command: str, verbose: bool = False) -> Dict[str, Any]:
    """워크플로우 명령 실행

    Args:
        command: 실행할 명령어 (예: "/task add 새 작업")
        verbose: 상세 출력 여부

    Returns:
        Dict with 'ok' and 'data' or 'error'
    """
    try:
        manager = get_workflow_manager()
        if manager is None:
            return {'ok': False, 'error': '워크플로우 매니저를 초기화할 수 없습니다'}

        # FlowManagerUnified의 process_command 사용
        # FlowCommandRouter의 route 메서드 직접 사용
        if hasattr(manager, 'route'):
            result = manager.route(command)
        elif hasattr(manager, '_router') and hasattr(manager._router, 'route'):
            # FlowManagerUnified를 통한 명령 처리
            result = manager._router.route(command)
        elif hasattr(manager, 'process_command'):
            result = manager.process_command(command)
        elif hasattr(manager, 'handle_command'):
            # FlowManagerUnified의 handle_command 사용
            result = manager.handle_command(command)
        elif hasattr(manager, 'wf_command'):
            # 기존 WorkflowManager 호환성
            result = manager.wf_command(command, verbose)
        else:
            return {'ok': False, 'error': '지원되지 않는 매니저 타입'}

        # Context 시스템 출력 (활성화된 경우)
        if os.environ.get('CONTEXT_SYSTEM', 'off').lower() == 'on':
            if verbose:
                print("✅ Context System enabled")

        return result

    except Exception as e:
        return {'ok': False, 'error': f'명령 실행 중 오류: {str(e)}'}

# 호환성을 위한 별칭
workflow_command = wf
