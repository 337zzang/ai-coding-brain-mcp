# Flow 시스템 사용 가이드

## 🎯 단순 모드 (권장)

### 특징
- Flow ID 없음
- 프로젝트당 하나의 Flow
- 단순한 폴더 구조
- 깔끔한 API

### 사용법
```python
# 환경변수 설정 (선택사항, 기본값이 simple)
os.environ['FLOW_MODE'] = 'simple'

# Flow Manager 초기화
from ai_helpers_new import get_flow_manager
manager = get_flow_manager()

# Plan 생성 - flow_id 불필요!
plan = manager.create_plan("기능 구현", "새로운 기능 개발")

# Task 생성
task = manager.create_task(plan.id, "설계 문서 작성")

# 상태 업데이트
manager.update_task_status(plan.id, task.id, "in_progress")

# 통계 확인
stats = manager.get_stats()
print(f"프로젝트: {stats['project']}")
print(f"Plan 수: {stats['plan_count']}")
```

### 폴더 구조
```
프로젝트/
└── .ai-brain/
    └── flow/
        ├── flow.json      # 프로젝트 메타데이터
        └── plans/         # Plan 파일들
            ├── plan_20250724_001.json
            └── plan_20250724_002.json
```

## 🔄 기존 모드 (호환성)

### 사용법
```python
# 환경변수로 기존 모드 선택
os.environ['FLOW_MODE'] = 'legacy'

# 나머지는 기존과 동일
manager = get_flow_manager()
flow = manager.create_flow("my_flow")
plan = manager.create_plan(flow.id, "plan_name")
```

## 📊 모드 비교

| 특징 | 단순 모드 | 기존 모드 |
|------|----------|----------|
| Flow ID | 없음 | 있음 |
| API 복잡도 | 낮음 | 높음 |
| 폴더 구조 | 단순 | 복잡 |
| 프로젝트당 Flow | 1개 | 여러 개 가능 |

## 🚀 권장사항

1. **새 프로젝트**: 단순 모드 사용
2. **기존 프로젝트**: 마이그레이션 후 단순 모드로 전환
3. **팀 프로젝트**: 단순 모드 (더 직관적)

## 🔧 마이그레이션

기존 시스템에서 단순 모드로 전환:

```python
# 1. 백업
cp -r .ai-brain .ai-brain.backup

# 2. 마이그레이션 스크립트 실행
python -m ai_helpers_new.migrate_to_simple

# 3. 환경변수 설정
export FLOW_MODE=simple
```
