# Task 상태 관리 강화 기능 사용 예시

## 1. Task 상태 이력 추적
```python
# Task가 여러 상태를 거치면서 이력이 기록됨
task = Task(id="1-1", title="로그인 기능 구현")

# pending → ready
task.transition_to("ready")

# ready → in_progress
task.transition_to("in_progress")

# 작업이 막힌 경우
task.set_blocking_reason("API 엔드포인트 미구현")
task.transition_to("blocked")

# 이력 확인
for history in task.state_history:
    print(f"{history['from']} → {history['to']} at {history['timestamp']}")
```

## 2. 시간 추적 및 진행률
```python
# 예상 시간 설정
task.estimated_hours = 8.0

# 작업 시작
task.transition_to("in_progress")

# 진행률 확인 (시간 경과에 따라 자동 계산)
progress = task.get_progress_percentage()
print(f"진행률: {progress:.1f}%")

# 특정 상태에 머문 시간
time_in_progress = task.get_time_in_state("in_progress")
print(f"작업 시간: {time_in_progress:.2f} 시간")
```

## 3. Phase 레벨 관리
```python
phase = Phase(id="phase-1", name="백엔드 개발")

# 상세 진행 상황
details = phase.get_progress_details()
print(f"전체: {details['total_tasks']}개")
print(f"진행 중: {details['active_tasks']}개")
print(f"완료율: {details['completion_rate']:.1f}%")
print(f"차단율: {details['blocked_rate']:.1f}%")

# 남은 시간 추정
remaining = phase.estimate_remaining_time()
print(f"예상 남은 시간: {remaining:.1f} 시간")

# Phase 완료 가능 여부
if phase.can_complete():
    print("✅ Phase 완료 가능")
else:
    print("❌ 아직 완료할 수 없음")
```

## 4. Plan과 통합 사용
```python
# Plan의 get_next_task()는 이제 더 스마트하게 작동
plan = Plan(name="프로젝트 알파")

# 차단된 작업 확인
blocked_tasks = plan.get_blocked_tasks()
for task in blocked_tasks:
    print(f"차단됨: {task.title} - 이유: {task.blocking_reason}")

# 다음 작업 선택 (의존성과 우선순위 고려)
next_task = plan.get_next_task()
if next_task:
    print(f"다음 작업: {next_task.title}")
    next_task.transition_to("in_progress")
```
