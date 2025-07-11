# Workflow v1 → v2 마이그레이션 가이드

## 개요
이 가이드는 기존 Workflow v1 시스템에서 v2로 마이그레이션하는 방법을 설명합니다.

## 주요 변경사항

### 1. 네이밍 변경
- `Plan` → `WorkflowPlan`
- `workflow()` → `execute_workflow_command()`
- 명령어별 개별 함수 제공

### 2. 데이터 저장 위치
- v1: `memory/workflow.json`
- v2: `memory/workflow_v2/{project}_workflow.json`

### 3. API 변경
- 모든 함수가 `HelperResult` 반환
- 함수형 API 중심 설계
- 명령어 파싱과 비즈니스 로직 분리

## 마이그레이션 절차

### 1단계: 기존 데이터 백업
```python
import shutil
import os
from datetime import datetime

# 백업 생성
backup_name = f"workflow_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
shutil.copy('memory/workflow.json', f'memory/{backup_name}')
print(f"백업 완료: {backup_name}")
```

### 2단계: 데이터 읽기
```python
import json

with open('memory/workflow.json', 'r', encoding='utf-8') as f:
    v1_data = json.load(f)

current_plan = v1_data.get('current_plan', {})
tasks = current_plan.get('tasks', [])
```

### 3단계: v2로 데이터 이전
```python
from workflow.v2 import WorkflowV2Manager

# v2 매니저 생성
manager = WorkflowV2Manager("migrated_project")

# 플랜 생성
if current_plan:
    plan = manager.create_plan(
        name=current_plan.get('name', 'Migrated Plan'),
        description=current_plan.get('description', '')
    )

    # 태스크 이전
    for v1_task in tasks:
        task = manager.add_task(
            title=v1_task.get('title', ''),
            description=v1_task.get('description', '')
        )

        # 완료된 태스크 처리
        if v1_task.get('status') == 'completed':
            manager.complete_task(task.id, v1_task.get('summary', ''))
```

### 4단계: 코드 업데이트

#### Before (v1)
```python
# v1 코드
from workflow import workflow

result = workflow("/plan 새 프로젝트 | 설명")
result = workflow("/task 작업1 | 설명")
result = workflow("/done 완료")
```

#### After (v2)
```python
# v2 코드
from workflow.v2 import workflow_plan, workflow_task, workflow_done

result = workflow_plan("새 프로젝트", "설명")
result = workflow_task("작업1", "설명")
result = workflow_done("완료")
```

### 5단계: helpers_wrapper 사용
```python
# helpers를 통한 v2 접근
helpers.workflow_v2_plan("프로젝트", "설명")
helpers.workflow_v2_task("작업", "설명")
helpers.workflow_v2_status()
helpers.workflow_v2("/done 완료")
```

## 호환성 유지

### 임시 호환성 레이어
```python
# v1 스타일 명령을 v2로 변환
def workflow_compat(command: str):
    """v1 명령어를 v2로 변환"""
    from workflow.v2 import execute_workflow_command
    return execute_workflow_command(command)

# 사용 예
result = workflow_compat("/plan 프로젝트 | 설명")
```

## 주의사항

1. **데이터 백업**: 마이그레이션 전 반드시 백업
2. **점진적 전환**: 한 번에 모든 코드를 변경하지 말고 점진적으로
3. **테스트**: 마이그레이션 후 충분한 테스트 수행
4. **롤백 계획**: 문제 발생시 v1으로 롤백할 수 있도록 준비

## 문제 해결

### 데이터 손실
백업 파일에서 복원:
```python
shutil.copy('memory/workflow_backup_20250108.json', 'memory/workflow.json')
```

### 함수를 찾을 수 없음
```python
# sys.path 확인
import sys
sys.path.insert(0, 'python')
```

### 상태 불일치
v2 시스템은 독립적으로 작동하므로 v1과 상태가 다를 수 있습니다.
필요시 수동으로 동기화하세요.
