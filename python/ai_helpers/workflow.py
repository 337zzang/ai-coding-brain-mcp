"""
Workflow Helpers - 워크플로우 전용 헬퍼 함수
문자열 명령 대신 함수 호출 방식 제공
"""
import sys
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from helper_result import HelperResult

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, os.path.join(str(project_root), 'python'))


def _ensure_workflow_module():
    """workflow_integration 모듈 확인 및 import"""
    try:
        from workflow_integration import (
            process_workflow_command,
            get_workflow_status as _get_status
        )
        return process_workflow_command, _get_status
    except ImportError:
        return None, None


# 기본 워크플로우 명령 (기존 호환성 유지)
def workflow(command: str = "/status") -> HelperResult:
    """워크플로우 명령 실행 - HelperResult 반환"""
    process_command, _ = _ensure_workflow_module()
    if not process_command:
        return HelperResult.failure("workflow_integration 모듈을 찾을 수 없습니다")

    try:
        result = process_command(command)
        
        # JSON 문자열인 경우 파싱 시도
        if isinstance(result, str):
            try:
                parsed = json.loads(result)
                result = parsed
            except Exception:
                # 파싱 실패하면 result 그대로 둠
                pass
        
        if isinstance(result, dict):
            if result.get('success', False):
                return HelperResult.success(result)
            else:
                return HelperResult.failure(result.get('error', 'Unknown error'))
        return HelperResult.success(result)
    except Exception as e:
        return HelperResult.failure(f"워크플로우 명령 실행 실패: {str(e)}")


# 전용 헬퍼 함수들

def get_workflow_status() -> HelperResult:
    """워크플로우 상태 조회"""
    _, get_status = _ensure_workflow_module()
    if not get_status:
        return HelperResult.failure("workflow_integration 모듈을 찾을 수 없습니다")

    try:
        status = get_status()
        return HelperResult.success(status)
    except Exception as e:
        return HelperResult.failure(f"상태 조회 실패: {str(e)}")


def workflow_init() -> HelperResult:
    """워크플로우 초기화"""
    return workflow("/init")


def workflow_plan(name: str, description: str = "") -> HelperResult:
    """새 계획 생성"""
    cmd = f"/plan {name}"
    if description:
        cmd += f" | {description}"
    return workflow(cmd)


def workflow_task(title: str, description: str = "") -> HelperResult:
    """새 작업 추가"""
    cmd = f"/task {title}"
    if description:
        cmd += f" | {description}"
    return workflow(cmd)


def workflow_approve(approval: str = "yes", notes: str = "") -> HelperResult:
    """현재 작업 승인"""
    cmd = f"/approve {approval}"
    if notes:
        cmd += f" | {notes}"
    return workflow(cmd)


def workflow_complete(summary: str = "") -> HelperResult:
    """현재 작업 완료"""
    if summary:
        return workflow(f"/complete | {summary}")
    return workflow("/complete")


def workflow_next() -> HelperResult:
    """다음 작업으로 이동"""
    return workflow("/next")


def workflow_list_tasks() -> HelperResult:
    """전체 작업 목록 조회"""
    return workflow("/tasks")


def workflow_skip(reason: str = "") -> HelperResult:
    """현재 작업 건너뛰기"""
    if reason:
        return workflow(f"/skip | {reason}")
    return workflow("/skip")


def workflow_reset() -> HelperResult:
    """워크플로우 초기화"""
    return workflow("/reset")


def workflow_save() -> HelperResult:
    """워크플로우 저장"""
    return workflow("/save")


def workflow_load() -> HelperResult:
    """워크플로우 로드"""
    return workflow("/load")


# 고급 기능

def get_current_task() -> HelperResult:
    """현재 작업 정보만 가져오기"""
    status = get_workflow_status()
    if status.ok and isinstance(status.data, dict):
        current_task = status.data.get('status', {}).get('current_task')
        if current_task:
            return HelperResult.success(current_task)
        else:
            return HelperResult.failure("현재 작업이 없습니다")
    return status


def get_plan_progress() -> HelperResult:
    """계획 진행률 가져오기"""
    status = get_workflow_status()
    if status.ok and isinstance(status.data, dict):
        plan = status.data.get('status', {}).get('plan', {})
        progress_info = {
            'name': plan.get('name', 'Unknown'),
            'total_tasks': plan.get('total_tasks', 0),
            'completed_tasks': plan.get('completed_tasks', 0),
            'progress_percent': 0
        }

        if progress_info['total_tasks'] > 0:
            progress_info['progress_percent'] = int(
                (progress_info['completed_tasks'] / progress_info['total_tasks']) * 100
            )

        return HelperResult.success(progress_info)
    return status


__all__ = [
    'workflow',
    'get_workflow_status',
    'workflow_init',
    'workflow_plan',
    'workflow_task',
    'workflow_approve',
    'workflow_complete',
    'workflow_next',
    'workflow_list_tasks',
    'workflow_skip',
    'workflow_reset',
    'workflow_save',
    'workflow_load',
    'get_current_task',
    'get_plan_progress'
]
