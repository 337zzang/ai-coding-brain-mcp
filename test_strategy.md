# 리팩토링 테스트 전략

## 테스트 범위

### 1. 단위 테스트
```python
# test/test_task_manager.py
def test_create_task():
    manager = TaskManager()
    task = manager.create_task("Test task", "phase-1")
    assert task.id == "phase-1-task-1"
    assert task.status == TaskStatus.PENDING

def test_update_task_status():
    manager = TaskManager()
    task = manager.create_task("Test task", "phase-1")
    updated = manager.update_task_status(task.id, TaskStatus.IN_PROGRESS)
    assert updated.status == TaskStatus.IN_PROGRESS
    assert manager.get_current_task() == updated
```

### 2. 통합 테스트
```python
# test/test_workflow_integration.py
def test_complete_workflow():
    # Manager들의 협업 테스트
    task_manager = TaskManager()
    plan_manager = PlanManager()
    workflow = WorkflowService(task_manager, plan_manager)
    
    # 전체 워크플로우 실행
    plan = workflow.create_plan("Test Plan")
    workflow.add_phase("Phase 1")
    workflow.add_task("Task 1")
    workflow.start_next_task()
    workflow.complete_current_task()
    
    assert workflow.get_progress() == 100
```

### 3. 성능 테스트
- Task 생성: < 10ms
- Plan 로드: < 50ms
- 전체 워크플로우: < 200ms

### 4. 하위 호환성 테스트
- 모든 기존 API 엔드포인트 동작 확인
- 기존 컨텍스트 파일 로드 가능
- 기존 명령어 정상 작동
