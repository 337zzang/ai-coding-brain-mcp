# Flow-Context 자동 연동 구현 계획

## 🎯 목표
Flow 시스템의 모든 작업이 자동으로 Context에 기록되도록 통합 구현

## 🔍 현재 문제점
- "Context 기록 실패: 'actions'" 오류 발생
- FlowManager에서 Context 기록 함수를 호출하지만 실패
- 이벤트가 JSON 파일에 저장되지 않음

## 📋 구현 Task 목록

### 1. ContextIntegration 파일 저장 로직 수정
**목적**: 이벤트가 실제로 JSON 파일에 저장되도록 수정

**작업 내용**:
- `record_flow_action` 함수의 'actions' 키 오류 수정
- JSON 파일 저장 로직 검증 및 수정
- 파일 I/O 예외 처리 강화

**예상 코드 수정**:
```python
def record_flow_action(self, flow_id, action_type, data):
    # 'actions' 대신 'events' 사용
    context['events'].append({
        'type': action_type,
        'timestamp': datetime.now().isoformat(),
        'data': data
    })
    self._save_context(flow_id, context)
```

### 2. FlowManager에 Context 자동 기록 통합
**목적**: Flow 생성/수정/삭제 시 자동 Context 기록

**수정 대상 메서드**:
- `create_flow()` - flow_created 이벤트
- `delete_flow()` - flow_deleted 이벤트
- `switch_flow()` - flow_switched 이벤트

**통합 방법**:
```python
def create_flow(self, name, project=None, force=False):
    flow = # ... 기존 로직
    
    # Context 기록 추가
    if self._context_enabled:
        try:
            record_flow_action(flow.id, 'flow_created', {
                'name': name,
                'project': project,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.warning(f"Context 기록 실패: {e}")
    
    return flow
```

### 3. PlanManager Context 통합
**목적**: Plan CRUD 작업 자동 기록

**수정 대상**:
- `create_plan()` - plan_created
- `update_plan()` - plan_updated
- `complete_plan()` - plan_completed
- `delete_plan()` - plan_deleted

### 4. TaskManager Context 통합
**목적**: Task 상태 변경 자동 추적

**수정 대상**:
- `create_task()` - task_created
- `update_task_status()` - 상태별 이벤트
  - todo → in_progress: task_started
  - in_progress → completed: task_completed
  - any → error: error_occurred

### 5. 이벤트 리스너 패턴 구현
**목적**: 느슨한 결합으로 Context 시스템 통합

**구현 내용**:
```python
class FlowEventEmitter:
    def __init__(self):
        self._listeners = []
    
    def register_listener(self, listener):
        self._listeners.append(listener)
    
    def emit_event(self, event_type, data):
        for listener in self._listeners:
            listener.on_event(event_type, data)

class ContextListener:
    def on_event(self, event_type, data):
        # Context에 기록
        pass
```

### 6. Context 실시간 업데이트 메커니즘
**목적**: 변경사항 즉시 반영

**구현 방법**:
- 버퍼링 없이 즉시 저장
- 또는 짧은 주기(1초)로 배치 저장
- 파일 락 메커니즘으로 동시성 처리

### 7. 통합 테스트 작성
**목적**: 자동 연동 검증

**테스트 시나리오**:
```python
def test_flow_context_integration():
    # Flow 생성
    flow = fm.create_flow("test-flow")
    
    # Context 파일 확인
    assert context_file_exists(flow.id)
    assert has_event(flow.id, 'flow_created')
    
    # Plan 추가
    plan = fm.create_plan(flow.id, "test-plan")
    assert has_event(flow.id, 'plan_created')
```

### 8. 성능 최적화
**목적**: 빈번한 파일 I/O 최적화

**최적화 방법**:
- 비동기 파일 쓰기
- 이벤트 배치 처리 (N개 또는 N초마다)
- 메모리 캐싱 + 주기적 플러시

### 9. 문서화 및 가이드 작성
**목적**: 개발자 가이드 제공

**문서 내용**:
- Context 시스템 아키텍처
- API 레퍼런스
- 사용 예제
- 트러블슈팅 가이드

## 🚀 구현 순서

1. **긴급**: Task 1 - ContextIntegration 수정 (actions → events)
2. **중요**: Task 2-4 - Flow/Plan/Task에 Context 통합
3. **개선**: Task 5-6 - 이벤트 패턴 및 실시간 업데이트
4. **품질**: Task 7 - 통합 테스트
5. **최적화**: Task 8 - 성능 개선
6. **문서화**: Task 9 - 가이드 작성

## 📊 예상 결과

### Before
- Context 기록 시도하지만 실패
- 수동으로 record_*_action 호출 필요
- 이벤트가 파일에 저장되지 않음

### After
- 모든 Flow/Plan/Task 작업 자동 기록
- Context 파일에 이벤트 누적
- 실시간 조회 및 분석 가능

## ⏱️ 예상 소요 시간
- 전체: 4-6시간
- Task 1-2: 2시간 (핵심 수정)
- Task 3-4: 1시간
- Task 5-9: 2-3시간

## 🎯 성공 기준
1. Flow/Plan/Task 작업 시 자동으로 Context 기록
2. Context 파일에 이벤트가 올바르게 저장
3. 기존 기능에 영향 없음
4. 성능 저하 없음