# Plan/Task 모델 분석 보고서

## 현재 상태

### Task 클래스
- 현재 메서드: validate_status, validate_priority, mark_completed, mark_started, get_priority_value
- 상태 관리: 기본적인 mark_completed(), mark_started()만 존재

### Plan 클래스  
- 현재 메서드: get_current_phase, get_all_tasks, get_task_by_id, overall_progress
- 작업 선택: 외부(cmd_next.py)에서 처리

### Phase 클래스
- 현재 메서드: get_task_by_id, add_task, progress
- 역할: 단순 컨테이너 역할

## 주요 문제점

1. **이원화된 작업 관리**
   - Plan.phases[].tasks: 작업 정의
   - context.tasks['next']: 실행 큐
   - 동기화 필요, 일관성 문제

2. **타입 안전성 부족**
   - dict 변환 후 조작
   - Pydantic 검증 우회

3. **분산된 비즈니스 로직**
   - 상태 전환: cmd_task.py
   - 우선순위 정렬: cmd_next.py
   - 의존성 체크: cmd_next.py

## 개선 방안

{'Plan': {'새로운 메서드': ['get_next_task() -> Optional[Task]: 우선순위와 의존성을 고려하여 다음 작업 반환', 'get_ready_tasks() -> List[Task]: 시작 가능한 모든 작업 목록', 'reorder_by_priority() -> None: 모든 작업을 우선순위로 재정렬', 'get_blocked_tasks() -> List[Task]: 의존성으로 막힌 작업 목록', 'update_task_status(task_id: str, status: str) -> bool: 작업 상태 업데이트']}, 'Task': {'새로운 메서드': ['transition_to(status: str) -> bool: 유효한 상태 전환 수행', 'can_start() -> bool: 시작 가능 여부 (의존성 체크)', 'check_dependencies() -> List[str]: 충족되지 않은 의존성 목록', 'add_dependency(task_id: str) -> None: 의존성 추가', 'remove_dependency(task_id: str) -> None: 의존성 제거']}, 'Phase': {'새로운 메서드': ['get_next_task() -> Optional[Task]: Phase 내 다음 작업', 'is_completed() -> bool: Phase 완료 여부', 'get_blocked_count() -> int: 막힌 작업 수', 'reorder_tasks() -> None: Phase 내 작업 재정렬']}}
