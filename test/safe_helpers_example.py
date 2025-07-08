
def safe_workflow_status():
    """안전한 워크플로우 상태 확인"""
    status = helpers.workflow("/status")
    if not status.ok:
        return None

    # 중첩된 구조 안전하게 접근
    status_data = status.data.get('status', {})
    plan = status_data.get('plan', {})

    return {
        'name': plan.get('name', 'Unknown'),
        'progress': plan.get('progress', 0),
        'completed': plan.get('completed', 0),
        'total': plan.get('total', 0)
    }

def safe_current_task():
    """안전한 현재 태스크 확인"""
    current = helpers.workflow("/current")
    if not current.ok:
        return None

    task = current.data.get('current_task', {})
    if not isinstance(task, dict):
        return None

    return {
        'title': task.get('title', 'Unknown'),
        'description': task.get('description', ''),
        'status': str(task.get('status', '')).replace('TaskStatus.', '')
    }
