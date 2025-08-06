
"""
Enhanced TaskLogger helpers for automatic logging
"""
from typing import Optional, Dict, Any, List
from .flow_api import get_flow_api
from .task_logger import create_task_logger

def get_task_logger(plan_id: str, task_number: int = None) -> Optional['EnhancedTaskLogger']:
    """현재 Task의 Logger 가져오기 (자동 감지)"""
    try:
        # FlowAPI에서 현재 선택된 plan과 task 정보 가져오기
        api = get_flow_api()
        current_plan = api.get_current_plan()

        if not current_plan['ok']:
            return None

        if plan_id != current_plan['data']['id']:
            api.select_plan(plan_id)

        # Task 번호 자동 감지
        if task_number is None:
            # 현재 in_progress 상태인 task 찾기
            tasks = api.list_tasks(plan_id)['data']
            for i, task in enumerate(tasks, 1):
                if task.get('status') == 'in_progress':
                    task_number = i
                    task_title = task['title']
                    break
            else:
                # in_progress가 없으면 첫 번째 todo task
                for i, task in enumerate(tasks, 1):
                    if task.get('status') == 'todo':
                        task_number = i
                        task_title = task['title']
                        break
        else:
            tasks = api.list_tasks(plan_id)['data']
            if task_number <= len(tasks):
                task_title = tasks[task_number - 1]['title']
            else:
                return None

        if task_number:
            return create_task_logger(plan_id, task_number, task_title)

    except Exception as e:
        print(f"❌ TaskLogger 가져오기 실패: {e}")

    return None


def log_test_result(logger: 'EnhancedTaskLogger', 
                    test_name: str, 
                    success: bool, 
                    details: str = "",
                    errors: List[str] = None) -> Dict[str, Any]:
    """테스트 결과를 TaskLogger에 기록"""
    if not logger:
        return {"ok": False, "error": "No logger"}

    if success:
        # 성공한 테스트는 note로 기록
        result = logger.note(f"✅ {test_name}: {details}")
    else:
        # 실패한 테스트는 blocker로 기록
        severity = "high" if errors else "medium"
        error_msg = f"{test_name} 실패: {details}"
        if errors:
            error_msg += f" | 오류: {', '.join(errors)}"

        result = logger.blocker(
            issue=error_msg,
            severity=severity,
            solution="코드 수정 필요"
        )

    return {"ok": True, "event": result}


def log_code_change(logger: 'EnhancedTaskLogger',
                    file_path: str,
                    action: str = "modify",
                    summary: str = "",
                    before: str = "",
                    after: str = "") -> Dict[str, Any]:
    """코드 변경사항을 TaskLogger에 기록"""
    if not logger:
        return {"ok": False, "error": "No logger"}

    changes = {}
    if before and after:
        changes = {
            "before": before[:100] + "..." if len(before) > 100 else before,
            "after": after[:100] + "..." if len(after) > 100 else after
        }

    result = logger.code(
        action=action,
        file=file_path,
        summary=summary,
        changes=changes
    )

    return {"ok": True, "event": result}


def log_analysis(logger: 'EnhancedTaskLogger',
                 target: str,
                 findings: str) -> Dict[str, Any]:
    """분석 결과를 TaskLogger에 기록"""
    if not logger:
        return {"ok": False, "error": "No logger"}

    result = logger.analyze(target=target, findings=findings)
    return {"ok": True, "event": result}


def log_progress(logger: 'EnhancedTaskLogger',
                completed: List[str] = None,
                remaining: List[str] = None,
                new_items: List[str] = None) -> Dict[str, Any]:
    """진행 상황을 TaskLogger에 기록"""
    if not logger:
        return {"ok": False, "error": "No logger"}

    result = logger.todo_update(
        completed=completed or [],
        remaining=remaining or [],
        new_items=new_items or []
    )
    return {"ok": True, "event": result}
