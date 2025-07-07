"""
MCP와 워크플로우 시스템 통합
Task 2: 프로젝트별 인스턴스 관리 구현
"""
import os
from typing import Dict, Any, Optional, Tuple
from python.workflow.workflow_manager import WorkflowManager
from python.workflow.commands import WorkflowCommands
from python.core.context_manager import get_context_manager


# 프로젝트별 워크플로우 인스턴스 관리
_workflow_instances: Dict[str, Tuple[WorkflowManager, WorkflowCommands]] = {}
_current_project_name: Optional[str] = None


def get_workflow_instance(project_name: Optional[str] = None) -> Tuple[WorkflowManager, WorkflowCommands]:
    """워크플로우 인스턴스 반환 (프로젝트별 관리)

    Args:
        project_name: 프로젝트명. None이면 현재 디렉토리명 사용

    Returns:
        (WorkflowManager, WorkflowCommands) 튜플
    """
    global _workflow_instances, _current_project_name

    # 프로젝트명 결정
    if project_name is None:
        project_name = os.path.basename(os.getcwd())

    # 현재 프로젝트 업데이트
    _current_project_name = project_name

    # 해당 프로젝트의 인스턴스가 없으면 생성
    if project_name not in _workflow_instances:
        manager = WorkflowManager()
        commands = WorkflowCommands(manager)
        _workflow_instances[project_name] = (manager, commands)
        print(f"✅ '{project_name}' 프로젝트의 워크플로우 인스턴스가 생성되었습니다.")

    return _workflow_instances[project_name]


def reset_workflow_instance(project_name: Optional[str] = None) -> bool:
    """특정 프로젝트의 워크플로우 인스턴스를 리셋

    Args:
        project_name: 리셋할 프로젝트명. None이면 현재 프로젝트

    Returns:
        성공 여부
    """
    global _workflow_instances, _current_project_name

    # 프로젝트명 결정
    if project_name is None:
        project_name = _current_project_name or os.path.basename(os.getcwd())

    # 인스턴스가 존재하면 제거
    if project_name in _workflow_instances:
        del _workflow_instances[project_name]
        print(f"✅ '{project_name}' 프로젝트의 워크플로우 인스턴스가 리셋되었습니다.")
        return True
    else:
        print(f"ℹ️ '{project_name}' 프로젝트의 워크플로우 인스턴스가 없습니다.")
        return False


def reset_all_workflow_instances() -> bool:
    """모든 워크플로우 인스턴스를 리셋"""
    global _workflow_instances

    count = len(_workflow_instances)
    _workflow_instances.clear()
    print(f"✅ {count}개의 워크플로우 인스턴스가 모두 리셋되었습니다.")
    return True


def switch_project_workflow(new_project_name: str) -> bool:
    """프로젝트 전환 시 워크플로우 인스턴스도 전환

    ContextManager.switch_project()에서 호출용
    """
    global _current_project_name

    # 이전 프로젝트와 다른 경우에만 처리
    if _current_project_name != new_project_name:
        _current_project_name = new_project_name
        # 새 프로젝트의 인스턴스를 미리 생성하지 않음
        # get_workflow_instance() 호출 시 자동 생성됨
        print(f"🔄 워크플로우가 '{new_project_name}' 프로젝트로 전환되었습니다.")
        return True
    return False


def get_current_project_name() -> Optional[str]:
    """현재 활성 프로젝트명 반환"""
    return _current_project_name


# 기존 함수들도 유지 (호환성)
def process_workflow_command(command: str) -> str:
    """워크플로우 명령 처리"""
    manager, commands = get_workflow_instance()
    result = commands.process_command(command)
    return result


def submit_task_plan(task_id: str, plan_content: str) -> Dict[str, Any]:
    """작업 계획 제출"""
    manager, commands = get_workflow_instance()
    # 구현 필요
    return {"success": True, "message": "Plan submitted"}


def complete_current_task(summary: str, details: list = None, outputs: dict = None) -> Dict[str, Any]:
    """현재 작업 완료"""
    manager, commands = get_workflow_instance()
    return commands.complete_current_task(summary, details, outputs)


def get_workflow_status() -> Dict[str, Any]:
    """워크플로우 상태 조회"""
    manager, commands = get_workflow_instance()
    return commands.handle_status("")


def get_current_task_info() -> Dict[str, Any]:
    """현재 작업 정보 조회"""
    manager, commands = get_workflow_instance()
    current_task = manager.get_current_task()
    if current_task:
        return {
            "id": current_task.id,
            "title": current_task.title,
            "description": current_task.description,
            "status": current_task.status.value
        }
    return None


# 헬퍼 함수들
def workflow_command(command: str):
    """워크플로우 명령 실행 헬퍼"""
    from ai_helpers import HelperResult
    return HelperResult(
        ok=True, 
        data=process_workflow_command(command), 
        error=None
    )


def workflow_plan(name: str, description: str = ""):
    """워크플로우 계획 생성 헬퍼"""
    manager, commands = get_workflow_instance()
    # 구현 필요
    pass


def workflow_complete():
    """현재 작업 완료 헬퍼"""
    manager, commands = get_workflow_instance()
    # 구현 필요
    pass
