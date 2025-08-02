

## 1️⃣ Flow 시스템 자동화 업데이트

### 기존 내용 (수정 필요)
```
# Task 시작
h.flow("/task progress task_id")

# TaskLogger 생성 (필수!)
logger = h.create_task_logger(plan_id, task_num, "task_name")
```

### 새로운 내용 (자동화)
```
# Task 시작만 하면 됨!
h.flow("/task add Task 이름")  # ← 자동으로 JSONL 파일 생성됨
h.flow("/task progress task_id")  # ← 자동으로 상태 변경 기록됨

# TaskLogger는 필요한 경우에만 수동 생성
# (추가 이벤트를 기록하고 싶을 때)
logger = h.create_task_logger(plan_id, task_num, "task_name")
logger.analyze("file.py", "분석 내용")
```

## 2️⃣ 파일명 형식 업데이트

### 기존 내용
- 파일명은 항상 '{task_num}.task.jsonl' 형식

### 새로운 내용
- 파일명: '{task_num}.{sanitized_task_name}.jsonl'
- 예시: '1.에러_처리_개선.jsonl', '2.API_통합.jsonl'
- 특수문자는 언더스코어로 자동 변환

## 3️⃣ 작업 플로우 간소화

### 기존 플로우
1. Task 시작: h.flow("/task progress")
2. TaskLogger 생성: h.create_task_logger()  ← 필수!
3. 작업 기록: logger.xxx()

### 새로운 플로우 (자동화)
1. Task 추가: h.flow("/task add 작업명")  ← JSONL 자동 생성
2. 작업 진행
3. 상태 변경: h.flow("/task done")  ← 완료 자동 기록

## 4️⃣ TaskLogger 사용 시점 변경

### 자동으로 기록되는 것들
- Task 생성 시: TASK_INFO, DESIGN 이벤트
- 상태 변경 시: NOTE (시작/완료 메시지)

### 수동으로 기록해야 하는 것들
- 상세 분석: logger.analyze()
- 코드 수정: logger.code()
- TODO 관리: logger.todo(), logger.todo_update()
- 문제 발생: logger.blocker()
- 의사결정: logger.decision()

## 5️⃣ 예제 코드 업데이트

### 간단한 Task 작업 (자동화)
```python
# 1. Plan 생성
h.flow("/create 새 기능 개발")

# 2. Task 추가 (JSONL 자동 생성!)
h.flow("/task add 1. API 설계")
h.flow("/task add 2. 구현")
h.flow("/task add 3. 테스트")

# 3. Task 진행 (상태 변경 자동 기록!)
h.flow("/task progress task_xxx_xxx")
# ... 작업 수행 ...
h.flow("/task done task_xxx_xxx")
```

### 상세 기록이 필요한 경우
```python
# Task 시작
h.flow("/task progress task_id")

# 추가 기록을 위해 TaskLogger 가져오기
logger = h.create_task_logger(plan_id, task_num, "task_name")

# 상세 작업 기록
logger.todo(["TODO #1", "TODO #2", "TODO #3"])
logger.analyze("main.py", "코드 분석 결과")
logger.code("modify", "api.py", "엔드포인트 추가")
logger.complete("상세 완료 메시지")
```

## 6️⃣ 주의사항 추가

### ⚠️ 새로운 주의사항
1. **중복 생성 주의**: Task가 이미 JSONL을 가지고 있다면, create_task_logger()는 기존 파일에 이어서 기록
2. **파일명 제한**: Task 이름의 특수문자는 언더스코어로 변환, 최대 30자
3. **상태값**: TaskStatus는 소문자 사용 (todo, in_progress, done)
4. **성능**: 매우 큰 JSONL 파일은 읽기 성능에 영향 가능

## 7️⃣ 핵심 변경 사항 요약

### 🎯 가장 중요한 변화
**"이제 TaskLogger를 수동으로 생성하지 않아도 됩니다!"**

- ✅ h.flow("/task add") → 자동 JSONL 생성
- ✅ h.flow("/task progress") → 자동 상태 기록
- ✅ h.flow("/task done") → 자동 완료 기록
- 📝 상세 기록이 필요할 때만 logger 사용

## 8️⃣ 마이그레이션 가이드

### 기존 코드를 새 방식으로 변경
```python
# 기존 (수동)
h.flow("/task progress task_id")
logger = h.create_task_logger(...)  # 필수였음
logger.task_info(...)

# 새로운 (자동)
h.flow("/task progress task_id")  # 이것만으로 충분!
# logger는 추가 기록이 필요할 때만 생성
```
