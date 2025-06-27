# Plan-Task 큐 통합 설계 문서

## 개요
현재 이원화된 작업 관리 구조(Plan.phases[].tasks와 context.tasks['next'])를 
Plan 중심의 단일 구조로 통합합니다.

## 현재 문제점
- 동기화 필요: 두 구조 간 수동 동기화
- 일관성 문제: 데이터 불일치 가능성
- 중복 관리: 같은 정보를 두 곳에서 관리
- 복잡도: 개발자가 두 구조 모두 이해 필요

## 통합 설계

### 핵심 원칙
1. Single Source of Truth: Plan이 작업의 유일한 소스
2. 상태 기반 관리: 작업 상태로 실행 가능 여부 판단
3. 메서드 캡슐화: 모든 작업 조작은 모델 메서드로

### 주요 변경사항
{'목표': "context.tasks['next'] 큐를 제거하고 Plan 모델에서 직접 작업 관리", '핵심 변경사항': ['1. context.tasks 필드 제거', '2. Plan.get_next_task() 메서드로 다음 작업 결정', '3. Task에 실행 관련 필드 추가 (queued_at, started_at 등)', '4. Plan에서 작업 상태로 필터링 (pending → ready → in_progress)'], '새로운 작업 흐름': {'작업 추가': 'Plan.phases[phase_id].add_task(task)', '다음 작업 선택': 'Plan.get_next_task() # 우선순위, 의존성 고려', '작업 시작': 'task.mark_started()', '작업 완료': 'task.mark_completed()', '대기 작업 조회': 'Plan.get_ready_tasks()', '완료 작업 조회': "Plan.get_all_tasks(status='completed')"}, 'Task 상태 확장': {'pending': '생성됨, 아직 큐에 없음', 'ready': '실행 준비됨 (의존성 충족)', 'in_progress': '진행 중', 'completed': '완료됨', 'blocked': '의존성으로 차단됨', 'cancelled': '취소됨'}}

### 구현 예시

def get_next_task(self) -> Optional[Task]:
    """우선순위와 의존성을 고려하여 다음 실행할 작업 반환
    
    Returns:
        Optional[Task]: 다음 실행할 작업, 없으면 None
    """
    ready_tasks = []
    
    # 모든 Phase의 작업을 순회
    for phase in self.phases.values():
        for task in phase.tasks:
            # ready 상태이거나 pending이면서 시작 가능한 작업
            if task.status == "ready" or (task.status == "pending" and task.can_start()):
                ready_tasks.append(task)
    
    if not ready_tasks:
        return None
    
    # 우선순위로 정렬 (HIGH > MEDIUM > LOW)
    ready_tasks.sort(key=lambda t: t.get_priority_value(), reverse=True)
    
    # 가장 높은 우선순위 작업 반환
    selected_task = ready_tasks[0]
    
    # 상태를 ready로 변경 (pending인 경우)
    if selected_task.status == "pending":
        selected_task.status = "ready"
    
    return selected_task


## 마이그레이션 계획
[{'단계': '1. 모델 확장', '작업': ['Task 모델에 새 필드 추가 (queued_at, ready_at)', 'Task 상태 enum 확장 (ready, blocked, cancelled 추가)', 'Plan/Task에 새 메서드 구현']}, {'단계': '2. 병행 운영', '작업': ['기존 context.tasks 유지하면서 새 메서드 테스트', 'cmd_next.py에서 Plan.get_next_task() 호출 테스트', '결과 비교 및 검증']}, {'단계': '3. 전환', '작업': ['cmd_task.py를 새 메서드 사용으로 수정', 'cmd_next.py를 새 메서드 사용으로 수정', 'context.tasks 참조 제거']}, {'단계': '4. 정리', '작업': ['ProjectContext에서 tasks 필드 제거', '구 동기화 코드 제거', '테스트 및 문서 업데이트']}]

## 예상 효과
- 코드 복잡도 30% 감소
- 동기화 버그 완전 제거
- 유지보수성 대폭 개선
