# 워크플로우-컨텍스트 통합 시스템

## 개요
WorkflowManager에 Flow Project v2의 Context System을 통합하여 모든 워크플로우 작업을 자동으로 추적하고 AI 친화적인 컨텍스트를 생성합니다.

## 주요 특징
- **비침습적 통합**: Decorator 패턴으로 기존 코드 변경 최소화
- **선택적 활성화**: 환경 변수로 Context 기능 on/off
- **이벤트 기반 저장**: task 완료 시점에만 저장 (MCP 환경 최적화)
- **100% 하위 호환**: 기존 WorkflowManager 사용자는 변화 없음

## 사용법

### Context 시스템 활성화
```bash
# Windows
set CONTEXT_SYSTEM=on

# Linux/Mac
export CONTEXT_SYSTEM=on
```

### 새로운 명령어 (Context 활성화 시)
```
/context                    # 현재 컨텍스트 요약 (brief)
/context show detailed      # 상세 요약
/context show ai           # AI 최적화 요약

/session save [name]       # 현재 세션 저장
/session list             # 저장된 세션 목록
/session restore <file>   # 세션 복원

/history [n]              # 최근 n개 히스토리
/stats                    # 통계 정보
```

### 기존 명령어 (항상 사용 가능)
```
/help                     # 도움말
/status                   # 상태 확인
/task add <이름>          # 태스크 추가
/task list               # 태스크 목록
/start <id>              # 태스크 시작
/complete <id> [요약]    # 태스크 완료
```

## 아키텍처

### Decorator 패턴
```python
# 기본 사용 (Context 비활성화)
WorkflowManager
    └─> 기존 기능만

# Context 활성화 시
ContextWorkflowManager
    └─> WorkflowManager (래핑)
        └─> 기존 기능 + Context 추적
```

### 파일 구조
```
python/
├── ai_helpers_new/
│   ├── workflow_manager.py          # 기존 WorkflowManager
│   ├── context_workflow_manager.py  # Context 통합 래퍼
│   └── __init__.py                 # exports
├── workflow_wrapper.py             # 통합 인터페이스
└── ...

flow_project_v2/
├── context/                        # Context 시스템
│   ├── context_manager.py
│   ├── session.py
│   └── summarizer.py
└── ...
```

## 저장 전략
- **자동 저장 제거**: 5분 타이머 방식 제거
- **이벤트 기반 저장**: task 완료/실패 시점에만 저장
- **수동 저장**: `/session save` 명령어로 언제든 저장

## 성능 고려사항
- MCP 환경에 최적화 (불필요한 주기적 I/O 제거)
- Context 비활성화 시 오버헤드 없음
- 선택적 기능 로딩으로 메모리 효율성

## 예제

### 기본 사용 (Context 비활성화)
```python
from workflow_wrapper import wf

# 기존과 동일하게 사용
wf("/task add 새로운 작업")
wf("/complete task_001 작업 완료")
```

### Context 활성화 사용
```python
import os
os.environ['CONTEXT_SYSTEM'] = 'on'

from workflow_wrapper import wf

# 작업 수행
wf("/task add AI 모델 학습")
wf("/start task_001")
wf("/complete task_001 학습 완료")

# Context 조회
wf("/context show detailed")
wf("/stats")
wf("/history 10")

# 세션 저장
wf("/session save milestone_1")
```

## 테스트
```bash
python flow_project_v2/tests/test_workflow_context_integration.py
```

## 기여
o3 AI 분석을 통해 MCP 환경에 최적화된 설계로 구현되었습니다.
