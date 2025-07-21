# Flow Project 최종 설계 - Plan → Task 계층 구조

## 1. 개요

Flow Project는 AI 코딩 어시스턴트가 프로젝트 작업을 체계적으로 관리하고, 
대화가 중단되었다가 재개되어도 완전한 컨텍스트를 복원할 수 있는 워크플로우 시스템입니다.

### 핵심 특징
- **Plan → Task 계층 구조**: 큰 목표를 작은 단위로 분해
- **완전한 컨텍스트 복원**: 이전 대화의 모든 맥락 유지
- **문서 통합**: 관련 문서와 분석 결과 연결
- **/flow 명령어**: 통합된 인터페이스


=== 📊 새로운 데이터 구조 설계 ===

1. **계층 구조**
```
Project
├── Plans (계획들)
│   ├── Plan 1
│   │   ├── 목표
│   │   ├── 컨텍스트
│   │   ├── 관련 문서
│   │   └── Tasks
│   │       ├── Task 1.1
│   │       ├── Task 1.2
│   │       └── Task 1.3
│   └── Plan 2
│       └── Tasks
└── Metadata
    ├── 현재 활성 Plan
    ├── 마지막 작업 시간
    └── AI 세션 컨텍스트
```

2. **파일 구조**
```
.ai-brain/
├── workflow.json          # 메인 워크플로우 (Plans 포함)
├── context.json          # AI 세션 컨텍스트
├── documents/            # 관련 문서
│   └── {plan_id}/
│       ├── summary.md
│       └── references/
├── snapshots/           # 작업 스냅샷
│   └── {timestamp}.json
└── cache/
    └── llm/             # o3 분석 결과
```

3. **workflow.json 스키마**
```json
{
  "version": "2.0",
  "project_name": "project-name",
  "current_plan_id": "plan_001",
  "last_activity": "ISO 8601 datetime",
  "metadata": {
    "created_at": "ISO 8601",
    "updated_at": "ISO 8601",
    "ai_session": {
      "last_context": "작업 중이던 내용 요약",
      "active_files": ["file1.py", "file2.py"],
      "key_decisions": ["결정1", "결정2"]
    }
  },
  "plans": [
    {
      "id": "plan_001",
      "title": "WorkflowManager 리팩토링",
      "objective": "명령어 시스템 개선 및 새 기능 추가",
      "status": "in_progress",
      "context": {
        "background": "o3 분석 결과를 바탕으로...",
        "constraints": ["기존 API 호환성 유지"],
        "references": ["llm/o3_task_0006.md"]
      },
      "created_at": "ISO 8601",
      "updated_at": "ISO 8601",
      "tasks": [
        {
          "id": "task_001",
          "title": "명령어 매핑 수정",
          "description": "/start, /complete 최상위 추가",
          "status": "completed",
          "plan_id": "plan_001",
          "dependencies": [],
          "outputs": ["파일 수정 내역", "테스트 결과"],
          "created_at": "ISO 8601",
          "completed_at": "ISO 8601"
        }
      ]
    }
  ]
}
```



=== 🎮 /flow 명령어 체계 설계 ===

**기본 명령어**
/flow                    # 현재 상태 및 컨텍스트 표시
/flow status            # 전체 프로젝트 상태
/flow context           # AI 세션 컨텍스트 복원

**Plan 관리**
/flow plan              # 현재 Plan 정보
/flow plan list         # 모든 Plan 목록
/flow plan add [title]  # 새 Plan 생성
/flow plan start [id]   # Plan 시작/전환
/flow plan complete     # 현재 Plan 완료

**Task 관리**
/flow task              # 현재 Task 정보
/flow task list         # 현재 Plan의 Task 목록
/flow task add [title]  # 현재 Plan에 Task 추가
/flow task start [id]   # Task 시작
/flow task complete     # 현재 Task 완료
/flow task next         # 다음 Task로 이동

**문서 관리**
/flow doc add [path]    # 관련 문서 추가
/flow doc list          # 관련 문서 목록
/flow doc show [id]     # 문서 내용 표시

**스냅샷 및 복원**
/flow snapshot          # 현재 상태 스냅샷
/flow restore [time]    # 특정 시점으로 복원
/flow history           # 작업 히스토리



=== 🔄 컨텍스트 복원 메커니즘 ===

1. **세션 재개 시 자동 실행**
```python
def restore_context():
    # 1. 마지막 활성 Plan 로드
    current_plan = load_current_plan()

    # 2. AI 세션 컨텍스트 복원
    ai_context = load_ai_context()

    # 3. 관련 파일 상태 확인
    check_file_changes(ai_context['active_files'])

    # 4. 진행 상황 요약 생성
    summary = generate_progress_summary(current_plan)

    # 5. 다음 작업 제안
    next_steps = suggest_next_steps(current_plan)

    return {
        'plan': current_plan,
        'context': ai_context,
        'summary': summary,
        'next_steps': next_steps
    }
```

2. **컨텍스트 자동 저장**
- 각 명령어 실행 후 자동 저장
- 중요 결정사항 기록
- 활성 파일 목록 업데이트

3. **스마트 요약**
- Plan의 목표와 현재 진행률
- 완료된 Task와 남은 Task
- 주요 결정사항과 변경내역
- 관련 문서 링크


## 5. 구현 계획

### Phase 1: 데이터 구조 마이그레이션 (1일)
1. 새로운 스키마 정의
2. 기존 데이터 마이그레이션 스크립트
3. 백업 및 롤백 메커니즘

### Phase 2: 핵심 기능 구현 (2-3일)
1. Plan 관리 기능
2. 개선된 Task 관리
3. 컨텍스트 저장/복원
4. 문서 연결 시스템

### Phase 3: 명령어 시스템 (1일)
1. /flow 명령어 파서
2. 각 하위 명령어 구현
3. 상태 표시 및 요약

### Phase 4: 스마트 기능 (2일)
1. 자동 컨텍스트 요약
2. 다음 작업 제안
3. 진행률 추적
4. 의존성 관리

## 6. 예시 시나리오

```bash
# 프로젝트 시작
> /flow plan add "WorkflowManager 리팩토링"
✅ Plan 생성: plan_001

> /flow task add "명령어 매핑 개선"
> /flow task add "응답 형식 통일"
> /flow task add "새 기능 추가"
✅ 3개 태스크 추가됨

> /flow task start 1
🚀 Task 시작: 명령어 매핑 개선

# ... 작업 진행 ...

> /flow task complete
✅ Task 완료: 명령어 매핑 개선

# === 대화 종료 후 재개 ===

> /flow
📊 프로젝트: ai-coding-brain-mcp
📋 활성 Plan: WorkflowManager 리팩토링 (33% 완료)

✅ 완료된 작업:
- 명령어 매핑 개선

🔄 진행 중:
- 응답 형식 통일

📌 다음 작업:
- 새 기능 추가

💡 제안: 응답 형식 통일 작업을 계속하시겠습니까?
```

## 7. 기대 효과

1. **생산성 향상**: 작업 중단/재개가 자유로움
2. **체계적 관리**: Plan 단위로 큰 그림 관리
3. **투명성**: 모든 결정과사항과 진행 상황 추적
4. **협업 가능**: 명확한 상태 공유

이 설계를 통해 AI 어시스턴트는 단순한 도구를 넘어 
진정한 프로젝트 파트너로 진화합니다.
