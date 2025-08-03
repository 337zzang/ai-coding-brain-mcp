# Flow API Migration Guide

## 기존 방식 (Deprecated)
```python
from ai_helpers_new import flow

# 명령어 기반 인터페이스
flow("/create My Plan")
flow("/task add My Task")
flow("/task done task_id")
```

## 새로운 방식 (권장)
```python
from ai_helpers_new import get_flow_api

# Pythonic API
api = get_flow_api()
plan = api.create_plan("My Plan")
task = api.add_task("My Task")
api.complete_task(task['id'])
```

## 주요 변경사항

### 1. Session 기반 아키텍처
- Thread-safe한 전역 상태 관리
- 테스트를 위한 격리된 세션 지원

### 2. 객체 지향 API
- 메서드 체이닝 가능
- 타입 힌트 지원
- IDE 자동완성 지원

### 3. 하위 호환성
- 기존 flow() 명령어는 계속 작동
- get_manager()도 계속 사용 가능
- 점진적 마이그레이션 가능

## 마이그레이션 예시

### Plan 관리
```python
# 기존
flow("/create Project Plan")
flow("/list")
flow("/select plan_id")

# 새로운 방식
api = get_flow_api()
plan = api.create_plan("Project Plan")
plans = api.list_plans()
api.select_plan(plan['id'])
```

### Task 관리
```python
# 기존
flow("/task add Implement feature")
flow("/task start task_id")
flow("/task done task_id")

# 새로운 방식
task = api.add_task("Implement feature")
api.start_task(task['id'])
api.complete_task(task['id'])
```

### 상태 확인
```python
# 기존
flow("/status")

# 새로운 방식
status = api.get_status()
print(f"Plans: {status['plan_count']}")
print(f"Tasks: {status['task_summary']}")
```
