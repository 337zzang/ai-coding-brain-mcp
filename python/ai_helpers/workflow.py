"""
Workflow Helpers - 워크플로우 전용 헬퍼 함수
V2 시스템을 사용하도록 업데이트됨
"""
import sys
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from .helper_result import HelperResult

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, os.path.join(str(project_root), 'python'))


# 기본 워크플로우 명령 - V2 시스템 사용
def workflow(command: str = "/status") -> HelperResult:
    """워크플로우 명령 실행 - V2 시스템 사용"""
    try:
        from workflow.v2 import execute_workflow_command
        return execute_workflow_command(command)
    except ImportError as e:
        return HelperResult.failure(f"V2 워크플로우 모듈 import 실패: {e}")
    except Exception as e:
        return HelperResult.failure(f"워크플로우 명령 실행 실패: {e}")


# 특화된 헬퍼 함수들
def workflow_plan(name: str, description: str = "", reset: bool = False) -> HelperResult:
    """새 플랜 생성"""
    cmd = f"/plan {name}"
    if description:
        cmd += f" | {description}"
    if reset:
        cmd += " --reset"
    return workflow(cmd)


def workflow_task(title: str, description: str = "") -> HelperResult:
    """태스크 추가"""
    cmd = f"/task {title}"
    if description:
        cmd += f" | {description}"
    return workflow(cmd)


def workflow_status() -> HelperResult:
    """현재 상태 조회"""
    return workflow("/status")


def workflow_done(notes: str = "") -> HelperResult:
    """현재 태스크 완료"""
    cmd = "/done"
    if notes:
        cmd += f" {notes}"
    return workflow(cmd)


def workflow_next() -> HelperResult:
    """다음 태스크로 이동"""
    return workflow("/next")


def workflow_current() -> HelperResult:
    """현재 태스크 정보"""
    return workflow("/current")


def workflow_history(limit: int = 10) -> HelperResult:
    """작업 이력 조회"""
    return workflow(f"/history {limit}")


def workflow_tasks() -> HelperResult:
    """전체 태스크 목록"""
    return workflow("/tasks")


def workflow_build() -> HelperResult:
    """프로젝트 빌드"""
    return workflow("/build")


def workflow_list() -> HelperResult:
    """플랜 목록 조회"""
    return workflow("/list")


def get_workflow_status() -> Dict[str, Any]:
    """워크플로우 상태 반환 (레거시 호환성)"""
    result = workflow_status()
    if result.ok:
        return result.get_data({})
    return {"error": result.error}


# Export
__all__ = [
    'workflow',
    'workflow_plan',
    'workflow_task',
    'workflow_status',
    'workflow_done',
    'workflow_next',
    'workflow_current',
    'workflow_history',
    'workflow_tasks',
    'workflow_build',
    'workflow_list',
    'get_workflow_status'
]
