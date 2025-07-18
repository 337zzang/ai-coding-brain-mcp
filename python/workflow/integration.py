"""
WorkflowV2 시스템 통합
기존 helpers와 완벽하게 통합하여 자동 추적 활성화
"""
import functools
from typing import Any, Callable
from .helper import workflow_v2, get_manager
from .auto_tracker import get_tracker

def track_helper_call(helper_name: str):
    """헬퍼 함수 호출 추적 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracker = get_tracker()
            result = func(*args, **kwargs)

            # 특정 헬퍼들에 대해 자동 추적
            if helper_name == "create_file" and len(args) > 0:
                tracker.track_file_creation(args[0])
            elif helper_name == "write_file" and len(args) > 0:
                tracker.track_file_modification(args[0])
            elif helper_name == "git_commit":
                tracker.track_git_commit()

            return result
        return wrapper
    return decorator

# 기존 workflow 명령어에 v2 통합
def workflow_integrated(command: str) -> str:
    """통합 워크플로우 명령어 처리"""
    # /v2로 시작하면 v2 시스템 사용
    if command.startswith("/v2"):
        return workflow_v2(command[3:].strip())

    # 기존 명령어는 v2로 리다이렉트
    parts = command.split()
    if not parts:
        return workflow_v2("help")

    cmd = parts[0].lower()

    # 명령어 매핑
    if cmd == "/task" and len(parts) > 1:
        if parts[1] == "add":
            return workflow_v2("task add " + " ".join(parts[2:]))
        elif parts[1] == "list":
            return workflow_v2("task list")
    elif cmd == "/status":
        return workflow_v2("status")
    elif cmd == "/next":
        # 다음 태스크 시작
        manager = get_manager()
        for task in manager.workflow.tasks:
            if task.status.value == "todo":
                return workflow_v2(f"start {task.id}")
        return "✅ 모든 태스크가 완료되었습니다"
    elif cmd == "/complete":
        # 현재 태스크 완료
        manager = get_manager()
        if manager.workflow.focus_task_id:
            summary = " ".join(parts[1:]) if len(parts) > 1 else None
            return workflow_v2(f"complete {manager.workflow.focus_task_id} {summary or ''}")
        return "❌ 진행 중인 태스크가 없습니다"

    # v1 명령어 안내
    return f"ℹ️ 워크플로우 v2를 사용합니다. /v2 help로 도움말을 확인하세요"

# 편의 함수들
def v2_task(name: str, tags: list = None) -> str:
    """빠른 태스크 추가"""
    tag_str = " ".join([f"#{tag}" for tag in tags]) if tags else ""
    return workflow_v2(f"task add {name} {tag_str}")

def v2_start() -> str:
    """다음 태스크 시작"""
    manager = get_manager()
    for task in manager.workflow.tasks:
        if task.status.value == "todo":
            return workflow_v2(f"start {task.id}")
    return "✅ 모든 태스크가 완료되었습니다"

def v2_done(summary: str = None) -> str:
    """현재 태스크 완료"""
    manager = get_manager()
    if manager.workflow.focus_task_id:
        from .auto_tracker import auto_complete_task
        if not summary:
            # 자동 요약 사용
            auto_complete_task(manager.workflow.focus_task_id)
            return ""
        return workflow_v2(f"complete {manager.workflow.focus_task_id} {summary}")
    return "❌ 진행 중인 태스크가 없습니다"

def v2_status() -> str:
    """상태 확인"""
    return workflow_v2("status")

def v2_report() -> str:
    """리포트 생성"""
    return workflow_v2("report")

# JSON 저장 위치 확인
def check_v2_files():
    """v2 파일 위치 확인"""
    import os
    workflow_file = "memory/workflow_v2.json"
    if os.path.exists(workflow_file):
        size = os.path.getsize(workflow_file)
        print(f"\n📁 WorkflowV2 파일: {workflow_file}")
        print(f"   크기: {size:,} bytes")

        # 간단한 내용 요약
        try:
            import json
            with open(workflow_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"   프로젝트: {data.get('project', 'N/A')}")
            print(f"   태스크 수: {len(data.get('tasks', []))}")
            print(f"   이벤트 수: {len(data.get('events', []))}")
        except:
            pass
    else:
        print(f"\n📁 WorkflowV2 파일이 아직 생성되지 않았습니다: {workflow_file}")

print("✅ WorkflowV2 통합 완료!")
print("\n사용 가능한 함수:")
print("  • workflow_integrated(command) - 통합 명령어")
print("  • v2_task(name, tags) - 태스크 추가")
print("  • v2_start() - 다음 태스크 시작")
print("  • v2_done(summary) - 현재 태스크 완료")
print("  • v2_status() - 상태 확인")
print("  • v2_report() - 리포트 생성")
