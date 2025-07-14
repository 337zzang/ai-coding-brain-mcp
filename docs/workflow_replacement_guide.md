# 워크플로우 시스템 대체 가이드

## 🔄 기존 시스템 → 통합 시스템 마이그레이션 완료

### 1. 사용 가능한 메서드

#### 방법 1: helpers.workflow 객체 사용 (기존 호환)
```python
# 프로젝트 전환
helpers.workflow.flow_project("my_project")

# 워크플로우 생성
plan = helpers.workflow.create_plan("작업 계획", tasks)

# 작업 실행
result = helpers.workflow.execute_task(task)

# 상태 확인
status = helpers.workflow.get_status()

# 체크포인트
checkpoint = helpers.workflow.checkpoint("name", data)

# 다음 작업
helpers.workflow.next_action("action", params)
```

#### 방법 2: helpers 직접 메서드 사용 (새로운 방식)
```python
# 프로젝트 전환
helpers.workflow_flow_project("my_project")

# 워크플로우 생성
plan = helpers.workflow_create_plan("작업 계획", tasks)

# 작업 실행
result = helpers.workflow_execute_task(task)

# 상태 확인
status = helpers.workflow_get_status()

# 체크포인트
checkpoint = helpers.workflow_checkpoint("name", data)

# 다음 작업
helpers.workflow_next_action("action", params)
```

### 2. 통합의 이점

1. **자동 프로토콜 추적**
   - 모든 실행이 고유 ID로 추적됨
   - 표준화된 출력 형식

2. **체크포인트 시스템**
   - 작업 중단/재시작 지원
   - 상태 자동 저장

3. **성능 분석**
   - 실행 시간 자동 측정
   - 병목 현상 식별 가능

4. **기존 코드 호환성**
   - 기존 helpers.workflow 코드 그대로 작동
   - 점진적 마이그레이션 가능

### 3. 마이그레이션 예시

#### 기존 코드:
```python
# 기존 방식 (가정)
workflow = create_workflow("My Plan")
workflow.add_task(task1)
workflow.execute()
```

#### 새로운 코드:
```python
# 통합 시스템
plan = helpers.workflow.create_plan("My Plan", [task1])
result = helpers.workflow.execute_task(task1)
```

### 4. 프로토콜 출력 예시

실행 시 다음과 같은 표준화된 출력이 생성됩니다:

```
[SECTION:SEC_xxx:WORKFLOW:My Plan]
[DATA:DATA_xxx:workflow_id:WF_xxx]
[EXEC:EXEC_xxx:task_xxx:timestamp]
[PROGRESS:PROG_xxx:1/3:33%]
[/EXEC:EXEC_xxx:success:0.123s]
[CHECKPOINT:CKPT_xxx:checkpoint_name:size]
[/SECTION:SEC_xxx]
```

### 5. 문제 해결

#### Q: 기존 코드가 작동하지 않아요
A: helpers.workflow 객체가 제대로 생성되었는지 확인하세요.

#### Q: 프로토콜 출력이 너무 많아요
A: 필요시 로그 레벨을 조정할 수 있습니다.

#### Q: 체크포인트는 어디에 저장되나요?
A: 메모리와 ./memory/workflows 디렉토리에 저장됩니다.

---

✅ 통합 완료: 기존 시스템이 새로운 워크플로우-프로토콜 통합 시스템으로 대체되었습니다.
