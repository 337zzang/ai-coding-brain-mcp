"""
워크플로우 명령어 - 새로운 통합 시스템
"""
from typing import Dict, Any, Optional
import logging

from .flow_manager import FlowManager
from .commands import CommandRouter

logger = logging.getLogger(__name__)

# 전역 인스턴스
_flow_manager: Optional[FlowManager] = None
_command_router: Optional[CommandRouter] = None


def get_flow_manager() -> FlowManager:
    """Flow Manager 싱글톤"""
    global _flow_manager
    if _flow_manager is None:
        _flow_manager = FlowManager()
        logger.info("FlowManager 초기화")
    return _flow_manager


def get_command_router() -> CommandRouter:
    """Command Router 싱글톤"""
    global _command_router
    if _command_router is None:
        _command_router = CommandRouter(get_flow_manager())
        logger.info("CommandRouter 초기화")
    return _command_router


def wf(command: str) -> Dict[str, Any]:
    """
    워크플로우 명령어 실행

    사용 예:
        wf("/flow my-project")
        wf("/plan add 새 계획")
        wf("/task plan_001 새 작업")
        wf("/start task_001")
        wf("/complete task_001 완료!")
    """
    try:
        router = get_command_router()
        result = router.execute(command)

        # 결과 출력
        if result.get('ok'):
            if 'message' in result:
                print(result['message'])
            elif 'data' in result:
                print(result['data'])
        else:
            error = result.get('error', 'Unknown error')
            print(f"❌ 오류: {error}")

        return result

    except Exception as e:
        logger.error(f"wf() error: {e}")
        error_msg = f"명령 실행 중 오류: {str(e)}"
        print(f"❌ {error_msg}")
        return {'ok': False, 'error': error_msg}


def help_wf(command: Optional[str] = None) -> str:
    """도움말 표시"""
    router = get_command_router()
    help_text = router.help(command)
    print(help_text)
    return help_text


# 편의 함수들
def current_flow() -> Optional[str]:
    """현재 선택된 Flow"""
    manager = get_flow_manager()
    flow = manager.get_current_flow()
    return flow.name if flow else None


def current_project() -> Optional[str]:
    """현재 프로젝트"""
    manager = get_flow_manager()
    return manager.get_project()


def set_project(project: str):
    """프로젝트 설정"""
    manager = get_flow_manager()
    manager.set_project(project)
    print(f"프로젝트 설정: {project}")


# 초기화 메시지
def init_message():
    """초기화 메시지"""
    print("✅ Flow 시스템 v2.0 준비됨")
    print("도움말: help_wf()")


# Context Manager 호환 (더미)
class DummyContextManager:
    """레거시 코드 호환용 더미"""
    def add_event(self, *args, **kwargs):
        pass


# 레거시 호환
FlowManagerUnified = FlowManager
LegacyFlowAdapter = FlowManager
FlowCommandRouter = CommandRouter


# __init__.py에서 import할 항목들
__all__ = [
    'wf',
    'help_wf',
    'current_flow',
    'current_project',
    'set_project',
    'get_flow_manager',
    'init_message',
    'FlowManager',
    'CommandRouter'
]
