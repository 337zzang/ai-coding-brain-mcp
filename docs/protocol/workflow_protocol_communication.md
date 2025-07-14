# 워크플로우 프로토콜 통신 가이드

## 📋 개요

워크플로우 프로토콜은 프로젝트 작업 관리를 위한 이벤트 기반 통신 시스템입니다.

## 🏗️ 아키텍처

### 1. 레이어 구조

```
┌──────────────────────────────────────────────┐
│              MCP Tool Layer                  │
│  Claude가 호출하는 도구들                      │
└────────────────────┬─────────────────────────┘
                     │
┌────────────────────▼─────────────────────────┐
│          Integration Layer                   │
│  WorkflowIntegration 클래스                  │
│  - 이벤트 발행                               │
│  - 상태 동기화                               │
└────────────────────┬─────────────────────────┘
                     │
┌────────────────────▼─────────────────────────┐
│            Storage Layer                     │
│  - workflow.json: 메인 상태                  │
│  - workflow_events.json: 이벤트 로그         │
│  - context.json: 프로젝트 컨텍스트           │
└──────────────────────────────────────────────┘
```

### 2. 데이터 구조

#### workflow.json
```json
{
  "plans": [
    {
      "id": "uuid",
      "name": "플랜 이름",
      "status": "draft|active|completed|archived",
      "tasks": [
        {
          "id": "uuid",
          "title": "태스크 제목",
          "status": "pending|in_progress|completed",
          "notes": ["진행 메모"],
          "outputs": {}
        }
      ]
    }
  ],
  "current_plan_id": "현재 활성 플랜 ID"
}
```

## 📨 통신 프로토콜

### 1. 기본 통신 흐름

```
Claude → MCP Tool → Integration Layer → Storage → Response
```

### 2. 주요 액션

#### CREATE_PLAN
- **요청**: 플랜 이름과 태스크 목록
- **처리**: 새 플랜 생성 및 저장
- **응답**: 생성된 플랜 ID와 상태

#### UPDATE_TASK
- **요청**: 태스크 ID와 업데이트 내용
- **처리**: 태스크 상태 변경 및 타임스탬프 업데이트
- **응답**: 업데이트된 태스크 정보

#### FLOW_PROJECT
- **요청**: 프로젝트 이름
- **처리**: 프로젝트 전환 및 워크플로우 상태 복구
- **응답**: 프로젝트 컨텍스트와 워크플로우 상태

### 3. 이벤트 시스템

모든 상태 변경은 이벤트로 기록됩니다:

- `project_switched`: 프로젝트 전환
- `workflow_created`: 새 워크플로우 생성
- `task_updated`: 태스크 업데이트
- `task_completed`: 태스크 완료

### 4. 에러 처리

```json
{
  "success": false,
  "error": {
    "type": "ErrorType",
    "message": "에러 설명",
    "context": {},
    "suggestion": "해결 방법"
  }
}
```

## 🔧 사용 예시

### Python에서 사용
```python
# 프로젝트 전환
result = flow_project("my-project")

# 플랜 생성
plan = create_workflow_plan("새 기능 개발", tasks=[...])

# 태스크 업데이트
update_workflow_task(task_id, {"status": "in_progress"})
```

### 이벤트 리스너 등록
```python
workflow_integration.on('task_completed', handle_task_completion)
```

## 📊 상태 관리

1. **Persistent State**: workflow.json에 영구 저장
2. **Event Log**: workflow_events.json에 모든 이벤트 기록
3. **Context Sync**: context.json과 자동 동기화

## 🚀 최적화 팁

1. 대량 업데이트 시 배치 처리 사용
2. 이벤트 리스너는 가벼운 작업만 수행
3. 주기적으로 오래된 이벤트 정리

생성일: 2025-07-14 23:53:10