# 극단순 Flow 시스템

## 구조
```
프로젝트/
└── .ai-brain/
    └── flow/
        ├── plan_20250724_001.json
        ├── plan_20250724_002.json
        └── plan_20250724_003.json
```

## 특징
- **Flow 개념 없음**: 프로젝트가 곧 컨테이너
- **flow.json 없음**: 메타데이터 관리 부담 제거
- **plans 폴더 없음**: 한 단계 덜 깊은 구조
- **극도로 단순**: Plan 파일들만 존재

## API
```python
manager = UltraSimpleFlowManager()

# Plan 생성
plan = manager.create_plan("기능 개발")

# Task 추가
task = manager.create_task(plan.id, "설계")

# 상태 업데이트
manager.update_task_status(plan.id, task.id, "done")

# 통계
stats = manager.get_stats()
```

## 장점
1. 더 이상 단순해질 수 없음
2. 파일 탐색기에서 바로 확인
3. Git diff가 매우 깔끔
4. 이해하기 쉬움
