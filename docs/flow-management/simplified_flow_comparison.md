# Flow 시스템 구조 비교

## 기존 구조 (복잡)
```
프로젝트/
└── .ai-brain/
    └── flow/
        └── flow_projectname_20250724_xxxxx/  # Flow ID 디렉토리
            ├── flow.json
            └── plans/
                ├── plan_001.json
                └── plan_002.json
```

## 새로운 구조 (단순)
```
프로젝트/
└── .ai-brain/
    └── flow/                              # Flow ID 없음!
        ├── flow.json                      # 프로젝트 정보만
        └── plans/
            ├── plan_20250724_001.json
            └── plan_20250724_002.json
```

## API 비교

### 기존 API
```python
# Flow 생성/선택 필요
flow = manager.create_flow("my_flow")
manager.select_flow(flow.id)

# 모든 작업에 flow_id 필요
plan = manager.create_plan(flow.id, "plan_name")
task = manager.create_task(flow.id, plan.id, "task_name")
manager.update_task_status(flow.id, plan.id, task.id, "done")
```

### 새로운 API
```python
# 자동으로 프로젝트 Flow 사용
manager = SimpleFlowManager()

# flow_id 불필요
plan = manager.create_plan("plan_name")
task = manager.create_task(plan.id, "task_name")
manager.update_task_status(plan.id, task.id, "done")
```

## 장점
1. **단순함**: Flow ID 관리 불필요
2. **직관적**: 프로젝트 = Flow
3. **깔끔한 API**: 파라미터 감소
4. **명확한 구조**: 폴더 구조가 단순

## 마이그레이션
기존 시스템에서 새 시스템으로 전환 시:
- Flow ID 제거
- 프로젝트별로 .ai-brain/flow 생성
- plans/ 폴더로 Plan 파일 이동
