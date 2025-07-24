# 폴더 기반 Flow 관리 시스템 설계

## 📋 작업 제목: Flow 시스템 폴더 구조 재설계

### 🏗️ 전체 설계 (Architecture Design)
- **목표**: Flow를 폴더 구조로 관리하여 확장성과 성능 향상
- **범위**: 전체 Flow 시스템 재구현
- **접근 방법**: 기존 메모리 기반에서 파일 시스템 기반으로 전환
- **예상 소요 시간**: 3-4시간

### 🔍 현재 상태 분석

#### 기존 구조의 문제점
1. **단일 파일 저장**: 모든 Flow/Plan/Task가 하나의 JSON에 저장
2. **메모리 부담**: 전체 데이터를 메모리에 로드
3. **동시성 문제**: 여러 작업 시 충돌 가능성
4. **Git 추적 어려움**: 작은 변경도 전체 파일 수정

#### 분석된 핵심 파일들
- `domain/models.py`: Flow, Plan, Task 모델 정의
- `flow_manager.py`: 메인 인터페이스 (17KB)
- `cached_flow_service.py`: 캐싱 로직 (13KB)
- `json_repository.py`: 파일 저장 (7KB)

### 📐 새로운 폴더 구조 설계

```
프로젝트/
└── .ai-brain/
    ├── flow.json                 # Flow 메타데이터만
    ├── plans/                    # Plan 폴더
    │   ├── plan_20250724_001.json
    │   ├── plan_20250724_002.json
    │   └── index.json           # Plan 인덱스
    ├── context/                  # Context 이벤트
    │   ├── events/
    │   └── snapshots/
    ├── backups/                  # 자동 백업
    └── config.json              # 설정 파일
```

### 📊 데이터 구조

#### flow.json (메타데이터만)
```json
{
  "id": "flow_projectname_20250724",
  "name": "project-name",
  "project": {
    "name": "project-name",
    "path": "/absolute/path",
    "type": "python"
  },
  "stats": {
    "total_plans": 15,
    "active_plans": 3,
    "completed_plans": 10,
    "total_tasks": 145
  },
  "created_at": "2025-07-24T10:00:00Z",
  "updated_at": "2025-07-24T10:54:00Z",
  "metadata": {}
}
```

#### plans/plan_YYYYMMDD_NNN.json
```json
{
  "id": "plan_20250724_001",
  "name": "implement_flow_system",
  "description": "Flow 시스템 구현",
  "status": "in_progress",
  "tasks": {
    "task_001": {
      "id": "task_001",
      "name": "design_architecture",
      "status": "completed",
      "created_at": "2025-07-24T10:00:00Z",
      "completed_at": "2025-07-24T10:30:00Z"
    },
    "task_002": {
      "id": "task_002",
      "name": "implement_core",
      "status": "in_progress",
      "created_at": "2025-07-24T10:30:00Z"
    }
  },
  "created_at": "2025-07-24T10:00:00Z",
  "updated_at": "2025-07-24T10:54:00Z",
  "metadata": {}
}
```

### 🛠️ 구현 계획

#### Phase 1: 새로운 Repository 구현
```python
class FolderBasedFlowRepository:
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.flow_path = os.path.join(base_path, 'flow.json')
        self.plans_dir = os.path.join(base_path, 'plans')
        self._ensure_structure()

    def save_plan(self, plan: Plan):
        '''개별 Plan 파일로 저장'''
        plan_file = os.path.join(self.plans_dir, f'{plan.id}.json')
        with open(plan_file, 'w') as f:
            json.dump(plan.to_dict(), f, indent=2)

    def load_plan(self, plan_id: str) -> Optional[Plan]:
        '''개별 Plan 파일에서 로드'''
        plan_file = os.path.join(self.plans_dir, f'{plan_id}.json')
        if os.path.exists(plan_file):
            with open(plan_file) as f:
                return Plan.from_dict(json.load(f))
        return None
```

#### Phase 2: FlowManager 개선
- Lazy Loading: Plan은 필요할 때만 로드
- 부분 업데이트: 전체 Flow 대신 개별 Plan만 저장
- 캐싱 전략: 최근 사용한 N개 Plan만 메모리에 유지

#### Phase 3: 마이그레이션 도구
- 기존 단일 파일을 폴더 구조로 변환
- 백업 생성 후 안전하게 이전

### ⚠️ 위험 요소 및 대응
| 위험 요소 | 영향도 | 대응 방안 |
|----------|--------|-----------|
| 파일 I/O 증가 | 중 | 효율적 캐싱으로 최소화 |
| 동시 접근 | 높음 | 파일 잠금 메커니즘 |
| 데이터 정합성 | 높음 | 트랜잭션 개념 도입 |

### ❓ 확인 사항
1. Plan ID 형식: YYYYMMDD_NNN vs UUID?
2. 인덱스 파일 필요성?
3. 압축 사용 여부?

**✅ 이 설계를 기반으로 구현을 시작해도 될까요?**
