# 프로젝트 단위 Flow 관리 시스템 설계

## 📋 작업 제목: 프로젝트 기반 Flow 관리 시스템 구현

### 🏗️ 전체 설계 (Architecture Design)
- **목표**: 각 프로젝트가 독립적인 Flow를 가지도록 시스템 재설계
- **범위**: FlowManager, Repository, 파일 구조 변경
- **접근 방법**: 기존 중앙 관리에서 분산 관리로 전환
- **예상 소요 시간**: 
  - 설계 및 검토: 30분
  - 구현: 2시간
  - 테스트: 1시간

### 🔍 현재 상태 분석
- **기존 구조**:
  ```
  프로젝트 루트/
  └── .ai-brain/          # 모든 프로젝트의 Flow 중앙 저장
      └── flows.json      # 모든 Flow 데이터
  ```

- **문제점**:
  1. 여러 프로젝트의 Flow가 하나의 파일에 혼재
  2. 프로젝트 이동 시 Flow 데이터 접근 불가
  3. 메모리와 파일 간 동기화 문제

### 📐 상세 설계 (Detailed Design)

#### 1. 새로운 디렉토리 구조
```
각 프로젝트/
└── .ai-brain/                    # 프로젝트별 독립 디렉토리
    ├── flow.json                 # 단일 Flow 데이터
    ├── context/                  # Context 데이터
    │   └── events.json
    └── metadata.json             # 프로젝트 메타데이터
```

#### 2. 핵심 변경사항

##### 2.1 FlowManager 개선
```python
class ProjectBasedFlowManager:
    def __init__(self, project_path: str = None):
        self.project_path = project_path or os.getcwd()
        self.ai_brain_path = os.path.join(self.project_path, '.ai-brain')
        self._ensure_ai_brain_exists()
        self._load_or_create_flow()

    def _ensure_ai_brain_exists(self):
        '''프로젝트에 .ai-brain 디렉토리가 없으면 생성'''
        os.makedirs(self.ai_brain_path, exist_ok=True)
        os.makedirs(os.path.join(self.ai_brain_path, 'context'), exist_ok=True)

    def _load_or_create_flow(self):
        '''기존 Flow 로드 또는 새로 생성'''
        flow_path = os.path.join(self.ai_brain_path, 'flow.json')
        if os.path.exists(flow_path):
            self.flow = self._load_flow(flow_path)
        else:
            self.flow = self._create_project_flow()
```

##### 2.2 Repository 패턴 개선
```python
class ProjectFlowRepository:
    def __init__(self, ai_brain_path: str):
        self.flow_path = os.path.join(ai_brain_path, 'flow.json')
        self.metadata_path = os.path.join(ai_brain_path, 'metadata.json')

    def save_flow(self, flow: Flow):
        '''Flow를 프로젝트별 파일에 저장'''
        with open(self.flow_path, 'w') as f:
            json.dump(flow.to_dict(), f, indent=2)

    def load_flow(self) -> Optional[Flow]:
        '''프로젝트별 Flow 로드'''
        if os.path.exists(self.flow_path):
            with open(self.flow_path, 'r') as f:
                return Flow.from_dict(json.load(f))
        return None
```

#### 3. 주요 기능 구현

##### 3.1 프로젝트 전환
```python
def switch_project(self, project_path: str):
    '''다른 프로젝트로 전환'''
    # 현재 Flow 저장
    self._save_current_flow()

    # 새 프로젝트로 전환
    self.project_path = project_path
    self.ai_brain_path = os.path.join(project_path, '.ai-brain')

    # 새 프로젝트의 Flow 로드 또는 생성
    self._ensure_ai_brain_exists()
    self._load_or_create_flow()
```

##### 3.2 자동 저장
```python
@auto_save
def update_flow(self, updates: dict):
    '''Flow 업데이트 시 자동 저장'''
    self.flow.metadata.update(updates)
    self.flow.updated_at = datetime.utcnow()
```

### 🛠️ Task별 실행 계획

#### Task 1: FlowManager 리팩토링
- **목표**: 프로젝트 기반 Flow 관리 로직 구현
- **파일**: `flow_manager.py` → `project_flow_manager.py`
- **주요 변경**:
  - 프로젝트 경로 기반 초기화
  - .ai-brain 자동 생성
  - 단일 Flow 관리

#### Task 2: Repository 재구현
- **목표**: 프로젝트별 독립적인 저장소 구현
- **파일**: 새로운 `project_flow_repository.py`
- **주요 기능**:
  - flow.json 읽기/쓰기
  - 메타데이터 관리
  - 자동 백업

#### Task 3: 마이그레이션 도구
- **목표**: 기존 중앙 Flow를 프로젝트별로 분리
- **파일**: `migrate_to_project_flows.py`
- **기능**:
  - 기존 flows.json 파싱
  - 프로젝트별 .ai-brain 생성
  - Flow 데이터 이전

#### Task 4: 헬퍼 함수 업데이트
- **목표**: ai_helpers_new 통합
- **변경사항**:
  - `get_flow_manager()` → 현재 프로젝트 기반
  - 자동 프로젝트 감지

### ⚠️ 위험 요소 및 대응 계획
| 위험 요소 | 발생 가능성 | 영향도 | 대응 방안 |
|----------|------------|-------|-----------|
| 기존 데이터 손실 | 중 | 높음 | 마이그레이션 전 백업 |
| 호환성 문제 | 낮음 | 중간 | 레거시 모드 지원 |
| 성능 저하 | 낮음 | 낮음 | 파일 I/O 최적화 |

### ❓ 확인 필요 사항
1. 이 설계가 요구사항을 충족하나요?
2. 기존 시스템과의 호환성을 유지해야 하나요?
3. Context 시스템도 프로젝트별로 분리해야 하나요?

**✅ 이 계획대로 진행해도 될까요?**
