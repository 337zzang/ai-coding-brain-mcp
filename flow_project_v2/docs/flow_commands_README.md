# /flow 명령어 시스템

## 개요
Flow Project v2와 통합된 작업 전환 명령어 시스템입니다. 여러 프로젝트(flow) 간에 전환하며 작업할 수 있습니다.

## 주요 기능
- **다중 Flow 관리**: 여러 프로젝트를 생성하고 전환
- **Plan/Task 통합**: flow 내에서 직접 plan과 task 관리
- **Context 자동 추적**: 모든 작업이 자동으로 기록됨
- **세션 지속성**: flow 전환 시에도 상태 유지

## 명령어 목록

### Flow 관리
```
/flow                          # 현재 flow 상태 표시
/flow list                     # 모든 flow 목록
/flow create <n>            # 새 flow 생성
/flow switch <id/name>         # 다른 flow로 전환
/flow delete <id> [confirm]    # flow 삭제 (확인 필요)
/flow status                   # 현재 flow 상세 상태
```

### Plan/Task 관리
```
/flow plan add <title>         # 현재 flow에 plan 추가
/flow plan list                # 현재 flow의 plan 목록
/flow task add <plan_id> <title>  # plan에 task 추가
```

### 기타 기능
```
/flow summary [brief|detailed|ai]  # flow 요약
/flow export                   # JSON으로 내보내기
/flow import <file>            # JSON에서 가져오기 (개발중)
/flow help                     # flow 명령어 도움말
```

## 사용 예시

### 새 프로젝트 시작
```python
# Context 시스템 활성화 (선택사항)
os.environ['CONTEXT_SYSTEM'] = 'on'

from workflow_wrapper import wf

# 새 flow 생성
wf("/flow create AI Assistant Project")

# Plan 추가
wf("/flow plan add Phase 1: Research")
wf("/flow plan add Phase 2: Development")

# Task 추가
wf("/flow plan list")  # plan ID 확인
wf("/flow task add plan_20250721_123456 Literature Review")
```

### 프로젝트 전환
```python
# 현재 flow 확인
wf("/flow")

# 다른 flow로 전환
wf("/flow list")
wf("/flow switch flow_20250721_112437")

# 상태 확인
wf("/flow status")
```

### 작업 요약
```python
# 간단한 요약
wf("/flow summary")

# 상세 요약
wf("/flow summary detailed")

# AI 최적화 요약
wf("/flow summary ai")
```

## 데이터 저장 위치
- **Flow Registry**: `.ai-brain/flows_registry.json`
- **현재 Flow**: `.ai-brain/current_flow.json`
- **Flow 데이터**: `flow_project_v2/flows/<flow_id>/`

## 기술적 세부사항
- **FlowCommandHandler**: /flow 명령어 처리
- **FlowManagerWithContext**: Flow Project v2 통합
- **ContextWorkflowManager**: 명령어 라우팅

## 주의사항
- Flow 삭제는 되돌릴 수 없으므로 신중히 수행
- 현재 활성 flow는 삭제할 수 없음 (먼저 다른 flow로 전환 필요)
- Import 기능은 현재 개발 중

## Context 시스템과의 통합
`CONTEXT_SYSTEM=on` 환경 변수 설정 시:
- 모든 flow 작업이 자동으로 추적됨
- Task 완료 시 자동 저장
- AI 친화적 요약 생성
