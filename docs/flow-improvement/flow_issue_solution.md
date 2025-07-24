# Flow 시스템 문제 해결 가이드

## 문제 요약
- Flow 생성 시 project 필드가 설정되지 않아 `/flow [프로젝트명]` 명령이 작동하지 않음
- FlowManagerUnified와 wf 함수 간의 인터페이스 불일치

## 임시 해결 방법

### 1. 수동으로 현재 Flow 설정
```bash
# current_flow.txt 파일 직접 수정
echo "flow_20250723_093507_d41323" > .ai-brain/current_flow.txt
```

### 2. Flow 명령어 대신 직접 메서드 호출
```python
from ai_helpers_new.flow_manager_unified import FlowManagerUnified
fmu = FlowManagerUnified()

# Flow 목록 보기
flows = fmu.list_flows()

# 특정 Flow 선택
fmu._current_flow_id = 'flow_id'

# Plan 추가
fmu.add_plan('plan_name')

# Task 추가
fmu.add_task('plan_id', 'task_name')
```

### 3. 현재 활성 Flow 정보
- Flow ID: flow_20250723_093507_d41323
- Flow Name: ai-coding-brain-mcp
- Plans: 12개 (v31.0 Context 시스템 강화 등)
- Tasks: 여러 개

## 영구 해결 방안 (코드 수정 필요)

### 1. FlowManagerUnified.create_flow 수정
```python
def create_flow(self, name: str) -> Dict[str, Any]:
    # 현재 프로젝트 정보 가져오기
    from .project import get_current_project
    current_proj = get_current_project()
    project_name = current_proj.get('name') if current_proj else None

    # FlowManager.create_flow 호출 시 project 전달
    return super().create_flow(name, project=project_name)
```

### 2. wf 함수와의 인터페이스 수정
- process_command 메서드 구현 또는
- workflow_wrapper.py에서 직접 메서드 호출하도록 수정

## 현재 사용 가능한 작업

1. 기존 Flow(flow_20250723_093507_d41323) 사용
2. Plan과 Task 직접 관리
3. Context 시스템은 정상 작동
