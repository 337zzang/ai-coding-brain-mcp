
# Phase 4: 미구현 기능 완성 계획

## 📋 작업 목록

### Task 1: FlowManager 메서드 추가 (45분)
```python
# 추가할 메서드들:

def get_plans(self, flow_id: str = None) -> List[Plan]:
    """Flow의 모든 Plan 반환"""
    if flow_id is None:
        flow_id = self._current_flow_id
    flow = self.get_flow(flow_id)
    return list(flow.plans.values()) if flow else []

def get_tasks(self, flow_id: str, plan_id: str) -> List[Task]:
    """Plan의 모든 Task 반환"""
    flow = self.get_flow(flow_id)
    if flow and plan_id in flow.plans:
        return list(flow.plans[plan_id].tasks.values())
    return []

def get_current_flow(self) -> Optional[Flow]:
    """현재 선택된 Flow 반환"""
    if self._current_flow_id:
        return self.get_flow(self._current_flow_id)
    return None

def complete_task(self, flow_id: str, plan_id: str, task_id: str) -> bool:
    """Task를 완료 상태로 변경"""
    self.update_task_status(flow_id, plan_id, task_id, 'completed')

    # Plan의 모든 Task가 완료되었는지 확인
    tasks = self.get_tasks(flow_id, plan_id)
    if all(t.status.value == 'completed' for t in tasks):
        self.update_plan_status(flow_id, plan_id, 'completed')

    return True

def add_note(self, flow_id: str, note: str, plan_id: str = None, task_id: str = None):
    """Flow, Plan 또는 Task에 메모 추가"""
    flow = self.get_flow(flow_id)
    if not flow:
        return False

    timestamp = datetime.now().isoformat()
    note_entry = {'timestamp': timestamp, 'note': note}

    if task_id and plan_id:
        # Task에 메모 추가
        if plan_id in flow.plans and task_id in flow.plans[plan_id].tasks:
            task = flow.plans[plan_id].tasks[task_id]
            if not hasattr(task, 'notes'):
                task.notes = []
            task.notes.append(note_entry)
    elif plan_id:
        # Plan에 메모 추가
        if plan_id in flow.plans:
            plan = flow.plans[plan_id]
            if not hasattr(plan, 'notes'):
                plan.notes = []
            plan.notes.append(note_entry)
    else:
        # Flow에 메모 추가
        if not hasattr(flow, 'notes'):
            flow.notes = []
        flow.notes.append(note_entry)

    self._service.save_flow(flow)
    return True

def batch_update(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """여러 Task를 일괄 업데이트"""
    results = {'success': 0, 'failed': 0, 'errors': []}

    for update in updates:
        try:
            flow_id = update.get('flow_id')
            plan_id = update.get('plan_id')
            task_id = update.get('task_id')
            status = update.get('status')

            if flow_id and plan_id and task_id and status:
                self.update_task_status(flow_id, plan_id, task_id, status)
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append(f"Invalid update: {update}")
        except Exception as e:
            results['failed'] += 1
            results['errors'].append(str(e))

    return results
```

### Task 2: workflow_commands.py 수정 (15분)
- get_current_flow() 메서드 사용하도록 수정
- 에러 처리 개선

### Task 3: 통합 테스트 (30분)
- 전체 워크플로우 테스트
- wf 명령어 완전 검증
- Context 기록 확인

## 🚀 예상 결과
- 모든 wf 명령어 정상 작동
- Flow → Plan → Task 전체 워크플로우 완성
- 사용자 친화적인 인터페이스
