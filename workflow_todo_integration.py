
def create_workflow_todos_integrated(workflow_plan, claude_todo_writer):
    """워크플로우 계획을 Claude Code TodoWrite와 통합된 todo로 변환"""
    manager = IntegratedWorkflowManager()
    todos = manager.create_workflow_with_todos(workflow_plan)

    # Claude Code TodoWrite에 적용
    claude_todo_writer(todos)

    return todos, manager

def sync_workflow_progress(workflow_plan, current_todos, task_todo_mapping):
    """현재 todo 상태를 기반으로 워크플로우 진행 상황 동기화"""
    for task in workflow_plan['tasks']:
        task_id = task['id']
        if task_id in task_todo_mapping:
            task_todo_ids = task_todo_mapping[task_id]
            task_todos = [todo for todo in current_todos if todo['id'] in task_todo_ids]
            completed_todos = [todo for todo in task_todos if todo['status'] == 'completed']

            progress = len(completed_todos) / len(task_todos) * 100 if task_todos else 0
            task['progress_percent'] = progress

            if progress == 100:
                task['status'] = 'completed'
            elif progress > 0:
                task['status'] = 'in_progress'

    return workflow_plan
