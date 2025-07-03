
# 리팩토링된 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    EnhancedFlow                         │
│  (Central Orchestrator & Scenario Management)           │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                     EventBus                            │
│         (Publish-Subscribe Event System)                │
└──────┬──────────────────┬──────────────────┬───────────┘
       │                  │                  │
       ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ TaskManager  │  │ PlanManager  │  │ PhaseManager │
├──────────────┤  ├──────────────┤  ├──────────────┤
│ - create     │  │ - create     │  │ - define     │
│ - update     │  │ - evaluate   │  │ - start      │
│ - complete   │  │ - complete   │  │ - transition │
│ - delete     │  │ - progress   │  │ - complete   │
└──────────────┘  └──────────────┘  └──────────────┘
       │                  │                  │
       └──────────────────┴──────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│           ContextPersistenceService                     │
│         (State Persistence to JSON)                     │
└─────────────────────────────────────────────────────────┘
```

## 이벤트 플로우 예시:
1. TaskManager.complete_task() → TaskCompletedEvent 발행
2. EventBus가 구독자들에게 전달
3. PlanManager.on_task_completed() 실행 → Plan 진행률 업데이트
4. PhaseManager.on_task_completed() 실행 → Phase 완료 체크
5. 조건 충족 시 추가 이벤트 발행 (PlanCompleted, PhaseCompleted)
