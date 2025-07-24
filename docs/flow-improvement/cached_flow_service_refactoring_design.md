# CachedFlowService 리팩토링 설계

## 🎯 핵심 원칙
- **1 프로젝트 = 1 Flow = 1 파일**
- 파일명 = 프로젝트명.json
- 파일 패턴 의존성 완전 제거

## 📁 새로운 파일 구조

```
.ai-brain/
├── projects/                      # 프로젝트별 Flow 데이터
│   ├── ai-coding-brain-mcp.json  # 각 프로젝트의 Flow 데이터
│   └── [project-name].json
├── project_index.json            # 프로젝트 메타데이터 인덱스
└── backups/                      # 자동 백업
```

## 🔧 주요 변경사항

### 1. CachedFlowService 리팩토링

```python
class CachedFlowService:
    def __init__(self, base_path: str = ".ai-brain"):
        self.base_path = Path(base_path)
        self.projects_dir = self.base_path / "projects"
        self.index_file = self.base_path / "project_index.json"
        self._ensure_directories()
        self._load_index()

    def _get_project_file(self, project_id: str) -> Path:
        """프로젝트 파일 경로 반환"""
        return self.projects_dir / f"{project_id}.json"

    def list_flows(self) -> List[Flow]:
        """인덱스 기반 Flow 목록 조회"""
        flows = []
        for project_id in self._index:
            flow = self.get_flow(project_id)
            if flow:
                flows.append(flow)
        return flows

    def get_flow(self, flow_id: str) -> Optional[Flow]:
        """프로젝트 파일에서 Flow 로드"""
        project_file = self._get_project_file(flow_id)
        if not project_file.exists():
            return None

        # 캐시 확인
        if self._cache.is_valid(flow_id):
            return self._cache.get(flow_id)

        # 파일에서 로드
        with open(project_file, 'r') as f:
            data = json.load(f)
            flow = Flow.from_dict(data)
            self._cache.put(flow_id, flow)
            return flow

    def save_flow(self, flow: Flow) -> None:
        """프로젝트 파일에 Flow 저장"""
        project_file = self._get_project_file(flow.id)

        # 원자적 쓰기
        self._save_atomic(project_file, flow.to_dict())

        # 인덱스 업데이트
        self._update_index(flow.id, {
            'name': flow.name,
            'updated_at': datetime.now().isoformat(),
            'plans_count': len(flow.plans),
            'tasks_count': sum(len(p.tasks) for p in flow.plans.values())
        })

        # 캐시 업데이트
        self._cache.put(flow.id, flow)
```

### 2. 인덱스 파일 구조 (project_index.json)

```json
{
  "ai-coding-brain-mcp": {
    "name": "AI Coding Brain MCP",
    "created_at": "2025-07-23T11:10:54",
    "updated_at": "2025-07-24T08:45:00",
    "plans_count": 2,
    "tasks_count": 4,
    "size_bytes": 2920
  },
  "another-project": {
    ...
  }
}
```

## 🚀 마이그레이션 전략

### Phase 1: 데이터 통합
1. 모든 flow_*.json 파일을 읽기
2. flows.json의 데이터와 병합
3. 프로젝트별 파일로 저장

### Phase 2: 레거시 정리
1. 기존 파일들을 backups/로 이동
2. 새 구조로 완전 전환

### Phase 3: 검증
1. 모든 Flow 접근 가능 확인
2. 성능 테스트
3. 레거시 코드 제거

## 📊 장점

1. **단순성**: 1 프로젝트 = 1 파일
2. **성능**: 불필요한 파일 스캔 제거
3. **확장성**: 프로젝트 수가 늘어도 관리 용이
4. **안정성**: 파일명 패턴 의존성 제거
5. **저장공간**: 중복 제거로 용량 절약

## ⚡ 성능 최적화

- 인덱스 파일로 빠른 목록 조회
- 프로젝트별 독립적인 캐싱
- 필요한 파일만 로드
