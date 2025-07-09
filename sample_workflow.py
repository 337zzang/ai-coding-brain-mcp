def process_workflow(task_id: str, context: dict):
    """워크플로우 처리 함수"""
    try:
        # 컨텍스트 검증
        if not task_id or not context:
            raise ValueError("Invalid task_id or context")

        result = execute_task(task_id, context)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_task(task_id: str, context: dict):
    """태스크 실행 함수"""
    # 실제 구현
    print(f"Executing task {task_id} with context")
    return f"Task {task_id} completed"
