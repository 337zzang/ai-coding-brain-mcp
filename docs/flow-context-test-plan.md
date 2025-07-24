# Flow-Context 연동 테스트 플랜

## 🎯 목표
Flow 시스템에서 Context 관리 기능이 자동으로 연동되는지 검증

## 📋 테스트 항목

### 1. Context 시스템 활성화 확인
- **목적**: Context 시스템이 올바르게 활성화되는지 확인
- **테스트 방법**:
  ```python
  import os
  os.environ['CONTEXT_SYSTEM'] = 'on'
  # ContextIntegration 초기화 확인
  ```
- **예상 결과**: Context 시스템 활성화 성공

### 2. Flow 작업 시 Context 자동 기록 테스트
- **목적**: Flow 생성, 전환, 삭제 시 Context 자동 기록 확인
- **테스트 시나리오**:
  1. 새 Flow 생성 → `flow_created` 이벤트 기록
  2. Flow 전환 → `flow_switched` 이벤트 기록
  3. Flow 삭제 → `flow_deleted` 이벤트 기록
- **확인 방법**:
  ```python
  # .ai-brain/contexts/flow_[id]/context.json 파일 확인
  ```

### 3. Plan 작업 시 Context 자동 기록 테스트
- **목적**: Plan CRUD 작업 시 Context 자동 기록 확인
- **테스트 시나리오**:
  1. Plan 생성 → `plan_created` 이벤트
  2. Plan 수정 → `plan_updated` 이벤트
  3. Plan 완료 → `plan_completed` 이벤트
- **검증 포인트**:
  - 타임스탬프 정확성
  - 메타데이터 완성도

### 4. Task 작업 시 Context 자동 기록 테스트
- **목적**: Task 상태 변경 시 Context 자동 기록 확인
- **테스트 시나리오**:
  1. Task 생성 → `task_created`
  2. Task 시작 (todo → in_progress) → `task_started`
  3. Task 완료 → `task_completed`
  4. Task 에러 → `error_occurred`
- **특별 확인사항**:
  - 상태 전환 시 자동 Context 기록
  - 에러 발생 시 상세 정보 포함

### 5. Context 조회 및 분석 기능 테스트
- **목적**: 기록된 Context 데이터 조회 및 분석 기능 검증
- **테스트 항목**:
  ```python
  # Context 요약 조회
  context.get_context_summary()
  
  # 관련 문서 조회
  get_related_docs(current_task)
  
  # Flow별 Context 조회
  get_flow_context_summary(flow_id)
  ```

### 6. Context 기반 작업 추천 기능 테스트
- **목적**: Context를 활용한 지능적 작업 추천 검증
- **테스트 시나리오**:
  1. 유사 작업 패턴 식별
  2. 다음 작업 추천
  3. 관련 문서 제안
- **평가 기준**:
  - 추천의 정확성
  - 응답 속도

## 🧪 테스트 환경 설정

```python
# 필수 환경변수
os.environ['CONTEXT_SYSTEM'] = 'on'

# 테스트용 Flow 생성
test_flow = fm.create_flow("context-test-flow")

# Context 디렉토리 확인
.ai-brain/contexts/
├── docs_context.json
└── flow_[id]/
    └── context.json
```

## ✅ 성공 기준

1. 모든 Flow/Plan/Task 작업이 Context에 자동 기록됨
2. Context 데이터가 올바른 형식으로 저장됨
3. 조회 API가 정확한 데이터를 반환함
4. Context 기반 추천이 유용한 결과를 제공함

## 📝 예상 결과

- **Context 파일 생성**: 각 Flow별로 독립적인 context.json
- **이벤트 기록**: 모든 작업이 타임스탬프와 함께 기록
- **데이터 무결성**: JSON 형식 유지, 에러 없음
- **성능**: Context 기록이 주 작업에 영향 없음