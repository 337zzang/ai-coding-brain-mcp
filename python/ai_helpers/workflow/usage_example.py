
# 통합 워크플로우 사용 예시

from ai_helpers.workflow.integrated_workflow import IntegratedWorkflowManager

# 1. 매니저 초기화
workflow = IntegratedWorkflowManager("my_project")

# 2. 워크플로우 시작
tasks = [
    {"id": "task1", "title": "코드 분석", "type": "code_analysis", "file_path": "./src"},
    {"id": "task2", "title": "테스트 실행", "type": "test_execution", "test_file": "test_main.py"},
    {"id": "task3", "title": "문서 생성", "type": "file_operation", "operation": "write", 
     "path": "docs/report.md", "content": "# 테스트 리포트\n..."}
]

plan_id = workflow.start_workflow("코드 검증 및 테스트", tasks)

# 3. 작업 실행
for task in tasks:
    result = workflow.execute_task(task)
    print(f"Task {task['id']}: {result['status']}")

    # 체크포인트 저장
    workflow.checkpoint(f"after_{task['id']}", result)

# 4. 상태 확인
status = workflow.get_status()
print(f"\n워크플로우 진행률: {status['workflow']['completed_tasks']}/{status['workflow']['total_tasks']}")
print(f"실행 오류: {status['execution']['errors']}개")

# 5. 다음 작업 지시
workflow.next_action("generate_report", {"format": "markdown", "include_metrics": True})
