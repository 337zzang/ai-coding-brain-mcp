# AI 양방향 통신 시스템 사용 가이드

## 개요
워크플로우 이벤트를 AI가 읽고 실행할 수 있는 지시서로 변환하는 시스템

## 주요 기능

### 1. **태스크 완료 → Git 커밋/푸시**
태스크가 완료되면 자동으로 Git에 커밋하고 푸시합니다.
- 자동 커밋 메시지 생성
- 진행 상황을 사용자에게 보고
- 다음 태스크 준비

### 2. **에러 발생 → 자동 해결 시도**
다양한 에러 타입에 대한 자동 해결 지시:
- `FileNotFoundError`: 파일 자동 생성
- `ImportError`: 모듈 자동 설치
- `SyntaxError`: 코드 분석 및 수정 제안
- `AttributeError`: 사용 가능한 속성 확인
- `PermissionError`: 권한 문제 해결 방안 제시

### 3. **플랜 완료 → 문서화 및 보고서**
플랜이 완료되면:
- 완료된 작업 요약
- Git 태그 생성
- 작업 결과물 보관
- 다음 플랜 제안

## 구현된 컴포넌트

### 1. AIInstructionListener (기본 클래스)
- AI 지시서 생성 및 저장
- 우선순위 관리
- 즉시 실행 알림

### 2. TaskCompletionInstructor
- 태스크 완료 이벤트 처리
- Git 자동화 지시
- 진행 상황 보고 지시

### 3. ErrorInstructor
- 에러 타입별 해결 방법 생성
- 자동 복구 지시
- 에러 로깅 지시

### 4. WorkflowInstructor
- 플랜 시작/완료 이벤트 처리
- 환경 설정 지시
- 문서화 및 보관 지시

### 5. AIInstructionExecutor
- 지시서 읽기 및 실행
- 우선순위 기반 실행
- 실행 결과 추적

## 사용 방법

### 1. 리스너 등록
```python
from python.workflow.v3.register_ai_listeners import register_ai_instructors

# AI 지시 리스너 등록
register_ai_instructors("프로젝트명")
```

### 2. 워크플로우 작업 수행
```python
# 태스크 완료 시 자동으로 AI 지시서 생성
helpers.workflow("/next")
```

### 3. AI 지시서 확인
```python
from python.workflow.v3.ai_instruction_executor import check_ai_instructions

# 대기 중인 지시서 확인
check_ai_instructions()
```

### 4. AI 지시 실행
```python
from python.workflow.v3.ai_instruction_executor import execute_ai_instruction

# 다음 지시 실행
execute_ai_instruction()

# 모든 지시 실행 (최대 5개)
execute_all_ai_instructions(5)
```

## AI 지시서 형식

```json
{
  "instruction_id": "INS_20250712_123456_abc123",
  "created_at": "2025-07-12T12:34:56",
  "event_type": "task_completed",
  "context": {
    "task_id": "task_123",
    "task_title": "API 구현",
    "plan_name": "백엔드 개발",
    "progress": 75
  },
  "ai_actions_required": [
    {
      "action": "git_commit_and_push",
      "description": "변경사항을 Git에 커밋하고 푸시",
      "params": {
        "message": "feat: API 구현 완료"
      },
      "mcp_commands": [
        "helpers.git_add('.')",
        "helpers.git_commit('feat: API 구현 완료')",
        "helpers.git_push()"
      ]
    }
  ],
  "priority": "immediate",
  "deadline": "immediate",
  "status": "pending"
}
```

## 우선순위 레벨
- `immediate`: 즉시 실행
- `high`: 높은 우선순위
- `normal`: 보통 우선순위
- `low`: 낮은 우선순위

## 실행 기한
- `immediate`: 즉시
- `today`: 오늘 중
- `this_week`: 이번 주 중

## 양방향 통신 흐름

```
1. 워크플로우 이벤트 발생
   ↓
2. 리스너가 이벤트 감지
   ↓
3. AI 지시서 생성 (JSON)
   ↓
4. AI가 지시서 읽기
   ↓
5. MCP 도구로 작업 수행
   ↓
6. 결과를 워크플로우에 반영
```

## 파일 구조

```
memory/
├── ai_instructions.json               # 기본 지시서
├── task_completion_instructions.json  # 태스크 완료 지시
├── error_instructions.json           # 에러 해결 지시
└── workflow_instructions.json        # 워크플로우 지시

python/workflow/v3/
├── listeners/
│   ├── ai_instruction_base.py       # 기본 리스너
│   ├── task_completion_instructor.py # 태스크 완료
│   ├── error_instructor.py          # 에러 처리
│   └── workflow_instructor.py       # 워크플로우
├── ai_instruction_executor.py       # 실행자
└── register_ai_listeners.py         # 등록 헬퍼
```

## 확장 가능성

### 새로운 이벤트 타입 추가
1. 새 리스너 클래스 생성 (AIInstructionListener 상속)
2. 이벤트 처리 메서드 구현
3. AI 작업 목록 생성
4. 리스너 등록

### 커스텀 작업 추가
1. 새로운 action 타입 정의
2. MCP 명령어 목록 작성
3. 실행자에서 처리 로직 추가

## 문제 해결

### 리스너가 등록되지 않는 경우
- WorkflowManager에 listener_manager가 있는지 확인
- 프로젝트가 올바르게 로드되었는지 확인

### 지시서가 생성되지 않는 경우
- 이벤트가 실제로 발생했는지 확인
- 리스너가 올바르게 등록되었는지 확인
- memory 디렉토리 권한 확인

### 지시가 실행되지 않는 경우
- 지시서 파일이 존재하는지 확인
- JSON 형식이 올바른지 확인
- MCP 명령어가 유효한지 확인