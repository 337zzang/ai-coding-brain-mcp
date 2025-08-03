# AI Coding Brain MCP v66.0 실제 사용 예시

## 프로젝트 전환
```python
# 프로젝트 전환
h.flow_project_with_workflow("my-project")
# 또는
h.flow("/flow my-project")

# 현재 프로젝트 확인
current = h.get_current_project()
project_path = current['data']['path']
```

## Flow Manager 사용
```python
# Manager 인스턴스 가져오기
manager = h.get_flow_manager()

# Plan 생성
plan = manager.create_plan("새로운 기능 구현")

# Task 생성
task1 = manager.create_task(plan.id, "1. 설계 및 분석")
task2 = manager.create_task(plan.id, "2. 구현")
task3 = manager.create_task(plan.id, "3. 테스트")

# Plan 선택
h.flow(f"/select {plan.id}")

# Task 상태 업데이트
manager.update_task_status(plan.id, task1.id, "in_progress")
# ... 작업 수행 ...
manager.update_task_status(plan.id, task1.id, "done")

# Plan 정보 조회
plan_data = manager.get_plan(plan.id)
print(f"Plan: {plan_data.name}")
print(f"Tasks: {len(plan_data.tasks)}")
```

## TaskLogger 사용
```python
# TaskLogger 생성
logger = h.create_task_logger(plan.id, 1, "api_integration")

# 작업 정보 설정
logger.task_info("API 통합 구현", priority="high", estimate="3h")

# TODO 목록 설정
logger.todo([
    "TODO #1: API 클라이언트 생성",
    "TODO #2: 인증 처리",
    "TODO #3: 테스트 작성"
])

# 진행 상황 기록
logger.analyze("api_client.py", "현재 구조 분석 완료")
logger.code("create", "api_client.py", "APIClient 클래스 생성")

# 완료
logger.complete("API 통합 완료 - 3개 엔드포인트 연동")
```

## 파일 작업
```python
# 절대 경로 해석
file_path = h.resolve_project_path("src/main.py")

# 파일 읽기/쓰기
content = h.read(file_path)['data']
h.write(file_path, modified_content)

# 검색
python_files = h.search_files("*.py", ".")['data']
todos = h.search_code("TODO", ".")['data']
```

## Git 작업
```python
# 브랜치 생성
h.git_checkout_b("feature/api-integration")

# 변경사항 확인
status = h.git_status()

# 커밋
h.git_add(["."])
h.git_commit("feat: API 통합 구현")

# 병합
h.git_checkout("main")
h.git_merge("feature/api-integration")
```

## 주의사항
1. `update_task_status`는 반드시 `plan_id`와 `task_id` 모두 필요
2. Plan 선택은 `h.flow("/select plan_id")` 사용
3. 프로젝트 전환은 `flow_project_with_workflow()` 사용
4. Desktop Commander는 항상 절대경로 사용
