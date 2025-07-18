
    elif command.startswith("/task"):
        # /task 명령어 처리 개선
        parts = command.split(maxsplit=2)  # 최대 3부분으로 분리

        if len(parts) == 1:
            # /task만 입력한 경우
            return workflow_manager.list_tasks()

        subcmd = parts[1] if len(parts) > 1 else ""

        if subcmd == "list":
            # /task list - 태스크 목록 표시
            return workflow_manager.list_tasks()
        elif subcmd == "add" and len(parts) > 2:
            # /task add [내용] - 태스크 추가
            task_desc = parts[2]
            workflow_manager.add_task(task_desc)
            return f"태스크 추가됨: {task_desc}"
        elif subcmd == "del" and len(parts) > 2:
            # /task del [번호] - 태스크 삭제
            try:
                task_index = int(parts[2]) - 1
                if workflow_manager.remove_task(task_index):
                    return f"태스크 {parts[2]} 삭제됨"
                else:
                    return "태스크 삭제 실패"
            except ValueError:
                return "올바른 태스크 번호를 입력하세요"
        else:
            # 구버전 호환성: /task [내용]은 태스크 추가로 처리
            if subcmd and subcmd not in ["list", "add", "del"]:
                task_desc = command[6:].strip()  # "/task " 이후 전체
                workflow_manager.add_task(task_desc)
                return f"태스크 추가됨: {task_desc}"
            else:
                return "사용법: /task list | /task add [내용] | /task del [번호]"
