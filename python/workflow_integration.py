"""
워크플로우 통합 모듈
WorkflowManager와 WorkflowCommands를 통합 관리
프로젝트별 독립 인스턴스 지원 (Task 1 개선)
"""

import os
from typing import Optional, Tuple
from python.workflow.workflow_manager import WorkflowManager
from python.workflow.commands import WorkflowCommands
from python.helper_result import HelperResult

# 전역 인스턴스 관리 (프로젝트별)
_workflow_instances = {}  # {project_name: (manager, commands)}
_current_project_name = None


def reset_workflow_instance(project_name: Optional[str] = None):
    """특정 프로젝트의 워크플로우 인스턴스 초기화

    Args:
        project_name: 초기화할 프로젝트명. None이면 모든 인스턴스 초기화
    """
    global _workflow_instances, _current_project_name

    if project_name is None:
        # 모든 인스턴스 초기화
        _workflow_instances.clear()
        _current_project_name = None
        return True
    elif project_name in _workflow_instances:
        # 특정 프로젝트 인스턴스만 제거
        del _workflow_instances[project_name]
        if _current_project_name == project_name:
            _current_project_name = None
        return True
    return False


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
        # 프로젝트별 workflow.json 경로 계산
        # 참고: WorkflowManager는 현재 디렉토리 기준으로 memory/workflow.json을 사용
        # 따라서 프로젝트 디렉토리에서 실행되어야 함
        manager = WorkflowManager()
        commands = WorkflowCommands(manager)
        _workflow_instances[project_name] = (manager, commands)

    return _workflow_instances[project_name]


def get_current_project_name() -> Optional[str]:
    """현재 활성 프로젝트명 반환"""
    return _current_project_name


def switch_project_workflow(new_project_name: str):
    """프로젝트 전환 시 워크플로우 인스턴스도 전환

    ContextManager.switch_project()에서 호출용
    """
    global _current_project_name

    # 이전 프로젝트와 다른 경우에만 처리
    if _current_project_name != new_project_name:
        _current_project_name = new_project_name
        # 새 프로젝트의 인스턴스를 미리 생성하지 않음
        # get_workflow_instance() 호출 시 자동 생성됨
        return True
    return False


def process_workflow_command(command: str) -> str:
    """워크플로우 명령어 처리"""
    try:
        manager, commands = get_workflow_instance()
        result = commands.process_command(command)
        return result.data.get('message', str(result.data))
    except Exception as e:
        return f"오류: {str(e)}"


# AI 헬퍼 함수들
def submit_task_plan(task_id: str, subtasks: list) -> HelperResult:
    """AI가 생성한 작업 계획 제출"""
    try:
        manager, commands = get_workflow_instance()
        result = commands.submit_task_plan(task_id, subtasks)
        return result
    except Exception as e:
        return HelperResult(ok=False, data=None, error=str(e))


def get_workflow_status() -> HelperResult:
    """워크플로우 상태 조회"""
    try:
        manager, commands = get_workflow_instance()
        result = commands.handle_status()
        return HelperResult(ok=True, data=result, error=None)
    except Exception as e:
        return HelperResult(ok=False, data=None, error=str(e))


def get_current_task() -> HelperResult:
    """현재 작업 조회"""
    try:
        manager, commands = get_workflow_instance()
        result = commands.handle_current()
        return HelperResult(ok=True, data=result, error=None)
    except Exception as e:
        return HelperResult(ok=False, data=None, error=str(e))


def workflow_list_tasks() -> HelperResult:
    """작업 목록 조회"""
    try:
        manager, commands = get_workflow_instance()
        result = commands.handle_tasks()
        return HelperResult(ok=True, data=result, error=None)
    except Exception as e:
        return HelperResult(ok=False, data=None, error=str(e))


# 하위 호환성을 위한 별칭
workflow = lambda command: HelperResult(
    ok=True, 
    data={'message': process_workflow_command(command)}, 
    error=None
)
