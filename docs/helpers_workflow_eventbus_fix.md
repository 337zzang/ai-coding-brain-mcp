
# helpers.workflow EventBus 연동 수정 사항

## 문제점
1. EventBus.publish()가 엄격한 isinstance 체크를 사용
2. 모듈 리로드로 인해 Event 클래스가 다르게 인식됨
3. WorkflowEvent 서브클래스들이 타입 체크 실패

## 해결책
event_bus.py의 publish 메서드를 duck typing 방식으로 수정:
- isinstance(event, Event) 체크를 제거
- hasattr로 필수 속성만 확인 (type, id)

## 추가 필요 작업
1. dispatcher 모듈 리로드 시 자동으로 event_adapter 생성 확인
2. 세션 재시작 후에도 연동 유지되도록 초기화 로직 개선

## 테스트 결과
✅ helpers.workflow 명령으로 4개 이벤트 모두 발행/수신 확인
- PLAN_CREATED
- PLAN_STARTED  
- TASK_ADDED
- TASK_COMPLETED
