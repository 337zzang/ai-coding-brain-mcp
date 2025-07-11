# 데이터 소유권 정책 (Data Ownership Policy)

## 🎯 단일 진실 원천(Single Source of Truth) 원칙

### 1. 데이터 소유권 명확화

#### WorkflowManager (소유자)
**위치**: `memory/workflow_v3/{project_name}_workflow.json`

**소유 데이터**:
- ✅ 모든 워크플로우 상태 (current_plan, archived_plans)
- ✅ 플랜 정보 (id, name, description, status, tasks)
- ✅ 태스크 정보 (id, title, status, notes, timestamps)
- ✅ 워크플로우 이벤트 히스토리
- ✅ 워크플로우 메타데이터

**책임**:
- 워크플로우 데이터의 생성, 수정, 삭제
- 데이터 무결성 보장
- 상태 변경 시 이벤트 발행

#### ContextManager (구독자)
**위치**: `memory/context.json`

**소유 데이터**:
- ✅ 프로젝트 메타데이터 (프로젝트 경로, 설정 등)
- ✅ 사용자 컨텍스트 (세션 정보, 환경 설정)
- ✅ 워크플로우 스냅샷 (읽기 전용, 캐시 목적)

**제거되는 데이터**:
- ❌ `memory/workflow.json` (더 이상 사용하지 않음)
- ❌ 워크플로우 전체 데이터 복사본
- ❌ 워크플로우 이벤트 히스토리

### 2. 데이터 흐름

```
WorkflowManager (진실의 원천)
    ↓ (이벤트 발행)
EventBus
    ↓ (이벤트 전달)
ContextManager (스냅샷 유지)
    ↓ (UI/API 제공)
사용자 인터페이스
```

### 3. 스냅샷 정책

ContextManager가 유지하는 워크플로우 스냅샷:
```json
{
  "workflow_snapshot": {
    "current_plan_id": "plan-123",
    "current_plan_name": "프로젝트 이름",
    "total_tasks": 10,
    "completed_tasks": 5,
    "progress_percent": 50,
    "last_updated": "2025-07-10T09:00:00Z",
    "status": "active"
  }
}
```

### 4. 이벤트 기반 동기화

**필수 동기화 이벤트**:
- PLAN_CREATED → 스냅샷 생성
- PLAN_UPDATED → 스냅샷 업데이트
- TASK_COMPLETED → 진행률 업데이트
- PLAN_COMPLETED → 상태 업데이트
- PLAN_ARCHIVED → 스냅샷 제거

### 5. 구현 가이드라인

1. **WorkflowManager는 절대 ContextManager의 데이터를 읽지 않음**
2. **ContextManager는 WorkflowManager의 데이터를 직접 수정하지 않음**
3. **모든 상태 변경은 이벤트를 통해서만 전파**
4. **스냅샷은 최소한의 정보만 포함**
5. **캐시는 TTL(Time To Live)을 가짐**

### 6. 마이그레이션 전략

1. 기존 `workflow.json` 데이터를 WorkflowManager로 이전
2. ContextManager의 워크플로우 저장 로직 제거
3. 스냅샷 메커니즘 구현
4. 이벤트 핸들러 업데이트
5. 레거시 파일 정리
