# Flow 폴더 구조 시스템 - 최종 설계

## 🎯 설계 목표
1. **프로젝트별 독립성**: 각 프로젝트가 독립적인 .ai-brain/flow 폴더 보유
2. **확장성**: Plan/Task가 많아져도 성능 저하 없음
3. **Git 친화성**: 개별 Plan 파일로 변경사항 추적 용이
4. **API 호환성**: 기존 인터페이스 유지

## 📁 최종 디렉토리 구조
```
프로젝트/
└── .ai-brain/
    └── flow/
        ├── flow.json             # Flow 메타데이터
        ├── plans/                # Plan 파일들
        │   ├── plan_20250724_001.json
        │   ├── plan_20250724_002.json
        │   └── ...
        ├── context/              # Context 이벤트
        │   ├── events.json
        │   └── snapshots/
        └── backups/              # 자동 백업
            └── YYYYMMDD/
```

## 🏗️ 아키텍처 (o3 제안 기반)
```
사용자 코드
    ↓
FlowManager (인터페이스)
    ↓
CachedFlowService (캐싱 계층)
    ↓
Repository (파일 I/O)
    ↓
파일 시스템
```

## 💾 데이터 구조

### flow.json
```json
{
  "id": "flow_projectname_20250724",
  "name": "project-name",
  "plan_ids": ["plan_20250724_001", "plan_20250724_002"],
  "project": "project-name",
  "created_at": "2025-07-24T10:00:00Z",
  "updated_at": "2025-07-24T10:55:00Z",
  "metadata": {}
}
```

### plans/plan_YYYYMMDD_NNN.json
```json
{
  "id": "plan_20250724_001",
  "name": "implement_feature",
  "flow_id": "flow_projectname_20250724",
  "tasks": {
    "task_001": {
      "id": "task_001",
      "name": "design",
      "status": "completed"
    }
  },
  "created_at": "2025-07-24T10:00:00Z",
  "updated_at": "2025-07-24T10:55:00Z"
}
```

## 🔧 핵심 구현 (o3 기반)

### 1. Repository 계층
```python
class JsonFileMixin:
    @staticmethod
    def _atomic_write(path: Path, data: dict):
        '''원자적 쓰기로 데이터 무결성 보장'''
        tmp = path.with_suffix('.tmp')
        with tmp.open('w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(path)

class FileFlowRepository(JsonFileMixin, FlowRepository):
    '''Flow 메타데이터 관리'''

class FilePlanRepository(JsonFileMixin, PlanRepository):
    '''개별 Plan 파일 관리'''
```

### 2. 캐싱 계층 (LRU)
```python
class CachedFlowService:
    def __init__(self, base_path=".ai-brain/flow"):
        self._flow_repo = FileFlowRepository(base_path)
        self._plan_repo = FilePlanRepository(base_path)
        self._flow_cache = LRUCache(64, ttl=30)
        self._plan_cache = LRUCache(256, ttl=30)
```

### 3. API 호환성
```python
class Flow:
    @property
    def plans(self) -> dict[str, Plan]:
        '''기존 API 호환을 위한 프로퍼티'''
        # Lazy loading
        return {pid: self._load_plan(pid) for pid in self.plan_ids}
```

## 🚀 구현 단계

### Phase 1: Repository 구현 (1시간)
- FileFlowRepository 구현
- FilePlanRepository 구현
- 원자적 쓰기 메커니즘

### Phase 2: 캐싱 계층 (30분)
- LRU 캐시 구현
- CachedFlowService 구현

### Phase 3: FlowManager 수정 (1시간)
- 새로운 Repository 사용
- API 호환성 유지
- Context 통합

### Phase 4: 마이그레이션 (30분)
- 기존 flows.json → 폴더 구조 변환
- 백업 생성
- 검증

## ✅ 장점
1. **성능**: 필요한 Plan만 로드
2. **확장성**: Plan 수 제한 없음
3. **안정성**: 원자적 쓰기로 데이터 보호
4. **협업**: Git에서 깔끔한 diff
5. **디버깅**: 파일 직접 확인 가능

## ⚠️ 주의사항
1. 파일 잠금 필요 (filelock 사용)
2. 백업 정책 수립
3. 인덱스 파일 고려

**이 설계대로 구현을 진행하시겠습니까?**
