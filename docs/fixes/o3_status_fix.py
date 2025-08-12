
# llm.py 수정 제안

def check_status(task_id):
    """작업 상태 확인 (파일 우선)"""
    # 1. 파일 기반 상태 확인
    task_file = f".o3_tasks/{task_id}.json"
    if os.path.exists(task_file):
        with open(task_file, "r", encoding="utf-8") as f:
            file_data = json.load(f)

            # 메모리 상태 동기화
            o3_tasks[task_id] = file_data

            return HelperResult(
                ok=True,
                data=file_data
            )

    # 2. 메모리 fallback
    if task_id in o3_tasks:
        return HelperResult(
            ok=True,
            data=o3_tasks[task_id]
        )

    return HelperResult(
        ok=False,
        error=f"Task {task_id} not found"
    )
