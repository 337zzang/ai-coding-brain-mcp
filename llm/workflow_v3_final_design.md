
## 워크플로우 시스템 V3 최종 설계

### 1. 폴더 구조
```
프로젝트/
  └── .ai-brain/
      ├── workflow.json          # 메인 워크플로우 파일
      ├── workflow_history.json  # 히스토리 (append-only)
      ├── cache/                 # 캐시 데이터
      │   └── llm_responses/
      └── checkpoints/           # 상태 체크포인트
```

### 2. 삭제할 파일들
- python/workflow_wrapper.py (중복)
- python/session_workflow.py (중복)
- python/workflow_migration.py (불필요)
- python/workflow/ 디렉토리 전체 (재구현)

### 3. 새로 생성할 파일
- python/ai_helpers_new/workflow_manager.py (핵심 구현)

### 4. workflow.json 스키마
```json
{
  "version": "3.0",
  "project_name": "프로젝트명",
  "created_at": "ISO날짜",
  "updated_at": "ISO날짜",
  "tasks": [
    {
      "id": "task_001",
      "name": "작업명",
      "status": "todo|in_progress|done|skipped",
      "created_at": "ISO날짜",
      "updated_at": "ISO날짜"
    }
  ],
  "current_task": "task_001",
  "context": {
    "last_files": [],
    "last_command": ""
  }
}
```

### 5. 구현 순서
1. WorkflowManager 클래스 작성
2. fp 함수에 .ai-brain 생성 로직 추가
3. wf 함수를 WorkflowManager 사용하도록 수정
4. 기존 파일들 삭제
5. 테스트 및 검증
