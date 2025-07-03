"""
MCP와 워크플로우 시스템 통합
"""
# 절대 임포트 사용
from workflow.workflow_manager import WorkflowManager
from workflow.commands import WorkflowCommands
# from workflow.models import Dict[str, Any], Dict[str, Any]  # models.py에 없음
import json
from typing import Dict, Any


# 전역 워크플로우 매니저 인스턴스
_workflow_manager = None
_workflow_commands = None


def get_workflow_instance():
    """워크플로우 인스턴스 반환 (싱글톤)"""
    global _workflow_manager, _workflow_commands
    if _workflow_manager is None:
        _workflow_manager = WorkflowManager()
        _workflow_commands = WorkflowCommands(_workflow_manager)
    return _workflow_manager, _workflow_commands


def process_workflow_command(command: str) -> str:
    """워크플로우 명령어 처리 (MCP 호출용)"""
    _, commands = get_workflow_instance()
    result = commands.process_command(command)
    
    # 특별한 요청 처리
    if result.get('request_plan'):
        # AI가 계획을 수립해야 함
        return json.dumps({
            'type': 'request_plan',
            'task': result.get('task'),
            'message': '이 작업에 대한 상세 실행 계획을 수립해주세요.'
        }, ensure_ascii=False, indent=2)
    
    elif result.get('request_approval'):
        # 승인 요청
        return json.dumps({
            'type': 'request_approval',
            'task': result.get('current_task'),
            'message': '이 작업 계획을 검토하고 승인 여부를 결정해주세요.'
        }, ensure_ascii=False, indent=2)
    
    elif result.get('request_result'):
        # 작업 결과 요청
        return json.dumps({
            'type': 'request_result',
            'task': result.get('current_task'),
            'completion_note': result.get('completion_note'),
            'message': '작업을 완료하고 결과를 요약해주세요.'
        }, ensure_ascii=False, indent=2)
    
    elif result.get('request_build'):
        # 빌드 요청
        return json.dumps({
            'type': 'request_build',
            'message': 'build_project_context() MCP 도구를 실행합니다.'
        }, ensure_ascii=False, indent=2)
    
    # 일반 결과 반환
    return json.dumps(result, ensure_ascii=False, indent=2)


def submit_task_plan(task_id: str, plan_dict: dict) -> str:
    """작업 계획 제출"""
    _, commands = get_workflow_instance()
    # plan_dict에서 직접 값 추출
    steps = plan_dict.get('steps', [])
    estimated_time = plan_dict.get('estimated_time')
    tools = plan_dict.get('tools', [])
    risks = plan_dict.get('risks', [])
    criteria = plan_dict.get('criteria', [])
    
    result = commands.create_task_plan(task_id, steps, estimated_time, tools, risks, criteria)
    return json.dumps(result, ensure_ascii=False, indent=2)


def complete_current_task(summary: str, details: list = None, 
                         outputs: dict = None, issues: list = None, 
                         next_steps: list = None) -> str:
    """현재 작업 완료 처리"""
    _, commands = get_workflow_instance()
    result = commands.complete_current_task(summary, details, outputs, issues, next_steps)
    return json.dumps(result, ensure_ascii=False, indent=2)


def get_workflow_status() -> Dict[str, Any]:
    """워크플로우 상태 반환"""
    manager, _ = get_workflow_instance()
    return manager.get_status()


def get_current_task_info() -> Dict[str, Any]:
    """현재 작업 정보 반환"""
    manager, _ = get_workflow_instance()
    current_task = manager.get_current_task()
    if current_task:
        return current_task.to_dict()
    return {'message': '현재 진행 중인 작업이 없습니다.'}


# helpers에 추가할 함수들
def workflow_command(command: str) -> str:
    """워크플로우 명령어 처리 (helpers용)"""
    return process_workflow_command(command)


def workflow_plan(task_id: str, plan_dict: dict) -> str:
    """작업 계획 제출 (helpers용)"""
    return submit_task_plan(task_id, plan_dict)


def workflow_complete(summary: str, details: dict = None) -> str:
    """작업 완료 처리 (helpers용)"""
    return complete_current_task(
        summary=summary,
        details=details.get('details', []) if details else [],
        outputs=details.get('outputs', {}) if details else {},
        issues=details.get('issues', []) if details else [],
        next_steps=details.get('next_steps', []) if details else []
    )
