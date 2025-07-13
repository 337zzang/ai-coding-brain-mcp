# Workflow System v4

## 개요
효율적인 상태 기반 워크플로우 시스템

## 주요 개선사항
- **파일 수 감소**: 37개 → 10개 (73% 감소)
- **리스너 제거**: 14개 리스너 → 0개 (MessageController로 통합)
- **단순한 구조**: 상태 기반 엔진 + 메시지 컨트롤러

## 디렉토리 구조
```
workflow/
├── core/                    # 핵심 엔진
│   ├── state_manager.py     # 상태 관리
│   ├── workflow_engine.py   # 워크플로우 엔진
│   └── storage.py          # 데이터 저장
├── messaging/              # 메시지 시스템
│   └── message_controller.py # 통합 메시지 컨트롤러
├── manager.py              # API 호환성 어댑터
├── models.py               # 데이터 모델
└── errors.py               # 에러 정의
```

## 사용법

### 기본 사용 (새 API)
```python
from workflow import WorkflowEngine

# 엔진 생성
engine = WorkflowEngine("my-project")

# 워크플로우 생성 및 시작
workflow_id = engine.create_workflow("새 기능 개발")
engine.start_workflow(workflow_id)

# 태스크 추가 및 실행
task_id = engine.add_task("구현하기")
engine.start_task(task_id)
# ... 작업 수행 ...
engine.complete_task(task_id, "완료!")
```

### 기존 API 호환
```python
from workflow import WorkflowManager

manager = WorkflowManager.get_instance("my-project")
manager.start_plan("새 기능 개발")
manager.add_task("구현하기")
```

## 메시지 시스템
모든 상태 변화는 stdout으로 출력:
- `st:state_changed:entity_id:{...}` - 상태 전이
- `st:task_summary:entity_id:{...}` - 작업 요약
- `st:error_occurred:entity_id:{...}` - 에러 발생

## 설정
```python
config = {
    'messaging': {
        'logging': True,        # 로깅 활성화
        'error_handling': True, # 에러 처리 활성화
        'auto_commit': False    # Git 자동 커밋 (기본값: False)
    }
}
engine = WorkflowEngine("project", config)
```
