# Flow Project 워크플로우 시스템 상세 설계

## 1. 시스템 개요

### 1.1 목적
- 프로젝트별 독립적인 태스크 관리 시스템 제공
- 프로젝트 전환 시 워크플로우 자동 전환
- 간단한 명령어로 태스크 추적 및 관리

### 1.2 핵심 컴포넌트
1. **flow_project_wrapper.py**: 프로젝트 전환 인터페이스
2. **WorkflowManager**: 워크플로우 관리 핵심 클래스  
3. **workflow_wrapper.py**: 사용자 인터페이스 래퍼
4. **데이터 저장소**: .ai-brain/workflow.json

## 2. 아키텍처 상세

### 2.1 계층 구조
```
사용자
  ↓
[wf() 함수] - workflow_wrapper.py
  ↓
[WorkflowManager.wf_command()] - ai_helpers_new/workflow_manager.py
  ↓
[태스크 관리 메서드들]
  ↓
[파일 시스템] - .ai-brain/workflow.json
```

### 2.2 데이터 흐름
1. **프로젝트 전환 흐름**
   - fp("project-name") 호출
   - 바탕화면에서 프로젝트 디렉토리 검색
   - WorkflowManager 인스턴스 생성/전환
   - 기존 workflow.json 로드 또는 새로 생성

2. **태스크 관리 흐름**
   - wf("/task add 태스크명") 호출
   - WorkflowManager.add_task() 실행
   - 고유 ID 생성 (task_XXX 형식)
   - workflow.json에 저장
   - 히스토리 추가

### 2.3 주요 클래스 다이어그램

```
WorkflowManager
├─ 속성
│  ├─ project_path: Path
│  ├─ ai_brain_path: Path  
│  ├─ workflow_file: Path
│  ├─ history_file: Path
│  └─ workflow: dict
│
└─ 메서드
   ├─ 초기화
   │  ├─ __init__(project_path)
   │  ├─ _ensure_directories()
   │  └─ _load_workflow()
   │
   ├─ 태스크 관리
   │  ├─ add_task(name)
   │  ├─ update_task(id, status, summary)
   │  ├─ get_current_task()
   │  └─ list_tasks()
   │
   ├─ 명령어 처리
   │  ├─ wf_command(command)
   │  ├─ _handle_task_command(args)
   │  ├─ _show_status()
   │  └─ _show_help()
   │
   └─ 유틸리티
      ├─ save_workflow()
      └─ _add_history(entry)
```

## 3. 데이터 모델

### 3.1 workflow.json 스키마
```json
{
  "version": "1.0",
  "project_name": "string",
  "created_at": "ISO 8601 datetime",
  "updated_at": "ISO 8601 datetime", 
  "current_task_id": "string | null",
  "tasks": [
    {
      "id": "task_XXX",
      "name": "string",
      "description": "string",
      "status": "todo | in_progress | completed | done",
      "created_at": "ISO 8601 datetime",
      "updated_at": "ISO 8601 datetime",
      "summary": "string | null"
    }
  ]
}
```

### 3.2 workflow_history.json 스키마
```json
[
  {
    "timestamp": "ISO 8601 datetime",
    "action": "string",
    "task_id": "string",
    "details": {}
  }
]
```

## 4. API 명세

### 4.1 사용자 명령어
| 명령어 | 설명 | 반환값 |
|--------|------|---------|
| wf("/status") | 워크플로우 상태 | dict with stats |
| wf("/task add [name]") | 태스크 추가 | dict with task |
| wf("/task list") | 태스크 목록 | dict with tasks |
| wf("/task start [id]") | 태스크 시작 | dict with result |
| wf("/task complete [id] [summary]") | 태스크 완료 | dict with result |
| wf("/help") | 도움말 | dict with help |

### 4.2 내부 메서드
- get_workflow_manager(): 현재 프로젝트의 WorkflowManager 인스턴스 반환
- save_workflow(): 변경사항을 파일에 저장
- _add_history(entry): 히스토리 항목 추가

## 5. 보안 및 제약사항

### 5.1 보안
- 프로젝트 검색은 바탕화면으로 제한
- 파일 접근은 프로젝트 디렉토리 내부로 제한

### 5.2 제약사항  
- 단일 프로젝트당 하나의 워크플로우
- 동시성 처리 없음 (단일 사용자 가정)
- 태스크 ID는 순차적 증가

## 6. 확장 가능성

### 6.1 향후 개선사항
1. 태스크 우선순위 추가
2. 태스크 간 의존성 관리
3. 태스크 필터링 및 검색
4. 다중 사용자 지원
5. 웹 인터페이스 추가

### 6.2 플러그인 시스템
- 커스텀 명령어 추가 가능
- 태스크 상태 커스터마이징
- 외부 시스템 연동

## 7. 테스트 전략

### 7.1 단위 테스트
- 각 메서드별 독립적 테스트
- 파일 I/O 모킹
- 엣지 케이스 처리

### 7.2 통합 테스트
- 전체 워크플로우 시나리오
- 프로젝트 전환 테스트
- 데이터 마이그레이션 테스트
