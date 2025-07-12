# EventBus 중심 재구성 문서

## 개선 전 구조
```
WorkflowManager._add_event()
    ├── EventStore.add(event)  # 직접 호출
    └── EventAdapter.publish_workflow_event(event)  # 별도 호출
```

## 개선 후 구조
```
WorkflowManager._add_event()
    └── UnifiedEventSystem.publish(event)  # 단일 진입점
            └── EventBus.publish(event)
                    ├── EventStoreListener.handle_event()  # 구독자
                    ├── ErrorCollectorListener.handle_event()  # 구독자
                    ├── DocsGeneratorListener.handle_event()  # 구독자
                    └── TaskContextListener.handle_event()  # 구독자
```

## 주요 개선사항

1. **단일 진입점**: 모든 이벤트가 UnifiedEventSystem을 통해 처리
2. **느슨한 결합**: EventStore도 구독자 중 하나로 변경
3. **확장성**: 새 리스너 추가가 용이
4. **일관성**: 모든 이벤트가 동일한 경로로 처리

## 마이그레이션 전략

1. UnifiedEventSystem 생성
2. 기존 리스너들을 새 시스템에 등록
3. WorkflowManager의 _add_event 메서드 수정
4. 기존 event_adapter 제거
5. 테스트 및 검증
