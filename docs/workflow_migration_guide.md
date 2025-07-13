# 워크플로우 시스템 마이그레이션 가이드

> 기존 WorkflowEngine 시스템에서 ImprovedWorkflowManager로 전환하는 가이드
> 작성일: 2025-07-13

## 📋 목차
1. [개요](#개요)
2. [주요 변경사항](#주요-변경사항)
3. [마이그레이션 단계](#마이그레이션-단계)
4. [코드 변경 예시](#코드-변경-예시)
5. [테스트 및 검증](#테스트-및-검증)
6. [롤백 계획](#롤백-계획)

## 개요

### 현재 시스템의 문제점
- **이중 저장 구조**: workflow.json과 개별 파일 시스템이 동시에 존재
- **복잡한 아키텍처**: WorkflowEngine, StateManager, Storage 등 여러 컴포넌트
- **동기화 문제**: helpers.workflow()와 WorkflowManager 인스턴스 불일치
- **상태 관리 복잡성**: 여러 곳에서 상태를 관리

### 새로운 시스템의 장점
- **단일 파일 저장**: workflow.json 하나로 모든 데이터 관리
- **간단한 구조**: ImprovedWorkflowManager 하나로 통합
- **빠른 성능**: 메모리 기반으로 파일 I/O 최소화
- **일관성**: 단일 소스로 데이터 일관성 보장

## 주요 변경사항

### 1. 파일 구조 변경
```
기존:
memory/
├── workflow.json (메타데이터)
└── projects/
    └── {project_name}/
        └── workflow_data/
            ├── workflow_{id}.json
            └── task_{id}.json

새로운 구조:
memory/
└── workflow.json (모든 데이터)
```

### 2. API 변경사항
| 기존 API | 새로운 API | 변경 내용 |
|---------|-----------|----------|
| `WorkflowEngine.create_workflow()` | `ImprovedWorkflowManager.create_plan()` | 메서드명 변경 |
| `WorkflowEngine.add_task()` | `ImprovedWorkflowManager.add_task()` | 동일 |
| `StateManager.set_workflow_state()` | 내부 처리 | 자동 상태 관리 |
| `Storage.save_workflow()` | 내부 처리 | 자동 저장 |

### 3. 데이터 모델 변경
- WorkflowPlan과 Task 모델은 그대로 사용
- 저장 시 to_dict() 메서드로 직렬화
- 로드 시 from_dict() 메서드로 역직렬화

## 마이그레이션 단계

### 1단계: 백업
```bash
# 기존 데이터 백업
cp memory/workflow.json memory/workflow_backup_$(date +%Y%m%d_%H%M%S).json
```

### 2단계: ImprovedWorkflowManager 설치
```bash
# 새 파일 복사
cp python/workflow/improved_manager.py python/workflow/
```

### 3단계: helpers 모듈 업데이트
```python
# helpers.py 수정
class HelpersWrapper:
    def __init__(self):
        self._workflow_manager = None
        # ... 기존 코드
    
    def workflow(self, command: str) -> Any:
        """워크플로우 명령 처리"""
        if not self._workflow_manager:
            from python.workflow.improved_manager import ImprovedWorkflowManager
            self._workflow_manager = ImprovedWorkflowManager(self.project_name)
        
        result = self._workflow_manager.process_command(command)
        
        # 워크플로우 메시지 발행 (기존 시스템과 호환)
        if result.get("success"):
            self._emit_workflow_message(result)
        
        return result
```

### 4단계: 기존 데이터 마이그레이션
```python
# 마이그레이션 스크립트
import json
import os
from datetime import datetime

def migrate_workflow_data():
    """기존 데이터를 새 형식으로 마이그레이션"""
    
    # 1. 기존 workflow.json 로드
    with open("memory/workflow.json", "r") as f:
        old_data = json.load(f)
    
    # 2. 개별 워크플로우 파일 로드
    workflow_dir = "memory/projects/{project}/workflow_data"
    if os.path.exists(workflow_dir):
        for filename in os.listdir(workflow_dir):
            if filename.startswith("workflow_"):
                # 워크플로우 데이터 로드 및 병합
                pass
    
    # 3. 새 형식으로 저장
    new_data = {
        "plans": old_data.get("plans", []),
        "active_plan_id": old_data.get("active_plan_id"),
        "events": old_data.get("events", []),
        "version": "3.1.0",
        "last_saved": datetime.now().isoformat(),
        "project_name": project_name
    }
    
    with open("memory/workflow.json", "w") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
```

### 5단계: 테스트
```bash
# 단위 테스트 실행
python -m pytest python/workflow/tests/test_improved_manager.py

# 통합 테스트
python -m pytest tests/integration/test_workflow_system.py
```

## 코드 변경 예시

### 기존 코드
```python
from python.workflow.manager import WorkflowManager
from python.workflow.engine import WorkflowEngine

# 복잡한 초기화
wm = WorkflowManager.get_instance("project")
engine = WorkflowEngine("project")

# 워크플로우 생성
workflow_id = engine.create_workflow("새 워크플로우")
engine.start_workflow(workflow_id)

# 태스크 추가
task_id = engine.add_task("태스크 1")
```

### 새로운 코드
```python
from python.workflow.improved_manager import ImprovedWorkflowManager

# 간단한 초기화
wm = ImprovedWorkflowManager("project")

# 플랜 생성 (자동 시작)
plan_id = wm.create_plan("새 워크플로우")

# 태스크 추가
task_id = wm.add_task("태스크 1")
```

## 테스트 및 검증

### 1. 기능 테스트 체크리스트
- [ ] 플랜 생성
- [ ] 태스크 추가
- [ ] 태스크 시작/완료
- [ ] 상태 조회
- [ ] 진행률 계산
- [ ] 이벤트 로깅
- [ ] 데이터 영속성

### 2. 성능 테스트
```python
# 성능 비교 스크립트
import time

def benchmark_operations():
    start_time = time.time()
    
    # 100개 태스크 생성/완료 테스트
    wm = ImprovedWorkflowManager("benchmark")
    plan_id = wm.create_plan("벤치마크")
    
    for i in range(100):
        task_id = wm.add_task(f"태스크 {i}")
        wm.complete_task(task_id)
    
    end_time = time.time()
    print(f"소요 시간: {end_time - start_time:.2f}초")
```

### 3. 호환성 테스트
- helpers.workflow() 명령 테스트
- 기존 API 호출 코드 테스트
- 워크플로우 메시지 발행 확인

## 롤백 계획

문제 발생 시 롤백 절차:

### 1. 즉시 롤백
```bash
# 백업 파일 복원
cp memory/workflow_backup_*.json memory/workflow.json

# 코드 원복
git checkout -- python/workflow/manager.py
git checkout -- helpers.py
```

### 2. 부분 롤백
- ImprovedWorkflowManager와 기존 시스템 병행 운영
- 점진적 전환 전략 적용

### 3. 데이터 복구
```python
# 데이터 복구 스크립트
def recover_workflow_data(backup_file):
    """백업에서 데이터 복구"""
    with open(backup_file, "r") as f:
        backup_data = json.load(f)
    
    # 현재 파일에 복원
    with open("memory/workflow.json", "w") as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)
```

## 모니터링 및 로깅

### 1. 로그 추가
```python
# ImprovedWorkflowManager에 로깅 추가
import logging

logger = logging.getLogger(__name__)

class ImprovedWorkflowManager:
    def create_plan(self, name: str, description: str = "") -> str:
        logger.info(f"플랜 생성: {name}")
        # ... 기존 코드
```

### 2. 메트릭 수집
- 응답 시간
- 파일 크기
- 메모리 사용량
- 오류 발생률

## 결론

ImprovedWorkflowManager로의 마이그레이션은 시스템을 단순화하고 성능을 향상시킵니다. 
단계별로 신중하게 진행하고, 각 단계마다 테스트를 수행하여 안정성을 보장하세요.

### 지원 및 문의
- 문제 발생 시 이슈 등록
- 개선 제안 환영

---
*이 가이드는 지속적으로 업데이트됩니다.*