# Flow 경로 관리 시스템 개선 설계 문서

## 1. 개요

### 1.1 배경
- **문제**: Flow 시스템이 프로젝트별로 독립적으로 관리되지 않음
- **원인**: 경로가 초기화 시점에 고정되어 프로젝트 전환 시 반영 안 됨
- **영향**: 여러 프로젝트를 다룰 때 flows.json이 섞이는 문제 발생

### 1.2 목표
- 프로젝트별 독립적인 Flow 관리
- 동적 프로젝트 전환 지원
- Repository 패턴 유지하면서 유연성 확보

## 2. 현재 시스템 분석

### 2.1 주요 문제점

#### 2.1.1 JsonFlowRepository의 정적 경로
```python
# 현재 코드
def __init__(self, storage_path: str = None):
    if storage_path is None:
        storage_path = os.path.join(os.getcwd(), ".ai-brain", "flows.json")
    self.storage_path = Path(storage_path)  # 고정됨!
```

**문제**: 
- `os.getcwd()`가 초기화 시점에만 호출됨
- 이후 디렉토리 변경 시 반영 안 됨
- 싱글톤 패턴으로 인해 같은 인스턴스 계속 사용

#### 2.1.2 FlowService의 전역 파일 사용
```python
# 현재 코드
current_file = os.path.join(os.path.expanduser("~"), ".ai-flow", "current_flow.txt")
```

**문제**:
- 사용자 홈 디렉토리에 전역 파일 생성
- 프로젝트 간 current_flow 정보 공유됨
- 프로젝트별 격리 불가능

#### 2.1.3 캐시 동기화 문제
- FlowManagerUnified의 `_flows` 캐시
- 파일 시스템과 메모리 상태 불일치
- 수동 동기화 필요

### 2.2 아키텍처 다이어그램
```
현재 구조:
┌─────────────────────┐
│  FlowManagerUnified │
├─────────────────────┤
│ - _flows (cache)    │
│ - repository ────────────┐
│ - flow_service ──────┐   │
└─────────────────────┘    │   │
                          │   │
┌─────────────────────┐    │   │
│    FlowService      │←───┘   │
├─────────────────────┤        │
│ - repository ────────────────┤
│ - ~/.ai-flow/      │        │
└─────────────────────┘        │
                              │
┌─────────────────────┐        │
│ JsonFlowRepository  │←───────┘
├─────────────────────┤
│ - storage_path      │ (고정!)
│   (초기화 시 결정)    │
└─────────────────────┘
```

## 3. 개선 설계

### 3.1 핵심 개념: ProjectContext

```python
from pathlib import Path
from typing import Optional

class ProjectContext:
    """프로젝트 컨텍스트 관리 클래스"""

    def __init__(self, root: Path):
        self.root = Path(root).resolve()

    @property
    def flow_file(self) -> Path:
        """프로젝트별 flows.json 경로"""
        return self.root / ".ai-brain" / "flows.json"

    @property
    def meta_dir(self) -> Path:
        """프로젝트별 메타데이터 디렉토리"""
        return self.root / ".ai-brain"

    @property
    def current_flow_file(self) -> Path:
        """프로젝트별 current_flow.txt"""
        return self.meta_dir / "current_flow.txt"

    def ensure_directories(self):
        """필요한 디렉토리 생성"""
        self.meta_dir.mkdir(parents=True, exist_ok=True)
```

### 3.2 Repository 개선

```python
class JsonFlowRepository(FlowRepository):
    """동적 경로 지원 Repository"""

    def __init__(self, context: ProjectContext):
        self._context = context
        self._ensure_file()

    @property
    def storage_path(self) -> Path:
        """컨텍스트 기반 동적 경로"""
        return self._context.flow_file

    def set_context(self, context: ProjectContext):
        """컨텍스트 변경 지원"""
        self._context = context
        self._ensure_file()
```

### 3.3 FlowService 개선

```python
class FlowService:
    """프로젝트별 격리된 FlowService"""

    def __init__(self, repository: FlowRepository, context: ProjectContext):
        self.repository = repository
        self.context = context
        self._flows: Dict[str, Flow] = {}
        self._current_flow_id: Optional[str] = None
        self._load_current_flow()

    def _get_current_flow_file(self) -> Path:
        """프로젝트별 current_flow 파일"""
        return self.context.current_flow_file

    def _load_current_flow(self):
        """프로젝트별 current_flow 로드"""
        current_file = self._get_current_flow_file()
        if current_file.exists():
            self._current_flow_id = current_file.read_text().strip()
```

### 3.4 FlowManagerUnified 개선

```python
class FlowManagerUnified:
    """프로젝트 전환 가능한 FlowManager"""

    @classmethod
    def for_project(cls, project_root: str) -> 'FlowManagerUnified':
        """프로젝트별 인스턴스 생성"""
        context = ProjectContext(project_root)
        repository = JsonFlowRepository(context)
        flow_service = FlowService(repository, context)
        plan_service = PlanService(flow_service)
        task_service = TaskService(plan_service)

        return cls(
            context=context,
            repository=repository,
            flow_service=flow_service,
            plan_service=plan_service,
            task_service=task_service
        )

    def switch_project(self, new_root: str):
        """프로젝트 전환"""
        # 새 컨텍스트 생성
        self.context = ProjectContext(new_root)

        # 모든 서비스에 새 컨텍스트 전파
        self.repository.set_context(self.context)
        self.flow_service.context = self.context

        # 캐시 무효화 및 재로드
        self._sync_flows_from_service()
```

## 4. 구현 계획

### 4.1 단계별 구현

#### Phase 1: ProjectContext 구현 (Plan 2)
1. `infrastructure/project_context.py` 생성
2. 단위 테스트 작성
3. 기존 코드와 호환성 유지

#### Phase 2: Repository 개선 (Plan 3)
1. JsonFlowRepository에 동적 경로 지원 추가
2. set_context 메서드 구현
3. 기존 API 호환성 유지

#### Phase 3: FlowService 개선 (Plan 4)
1. 전역 파일 제거
2. 프로젝트별 current_flow 관리
3. context 기반 동작

#### Phase 4: FlowManagerUnified 개선 (Plan 5)
1. for_project 팩토리 메서드 추가
2. switch_project 메서드 구현
3. 레거시 API 래핑

#### Phase 5: 테스트 및 검증 (Plan 6)
1. 통합 테스트 작성
2. 프로젝트 전환 시나리오 테스트
3. 성능 테스트

### 4.2 호환성 전략

```python
# 레거시 코드 지원
def __init__(self, storage_path: str = None, context_manager=None):
    if storage_path:
        # 레거시 모드
        context = ProjectContext(Path(storage_path).parent.parent)
    else:
        # 새 모드
        context = ProjectContext(Path.cwd())

    # 나머지 초기화...
```

## 5. 예상 사용 시나리오

### 5.1 프로젝트 전환
```python
# 방법 1: 새 인스턴스 생성
fmu_proj_a = FlowManagerUnified.for_project("/path/to/project-a")
fmu_proj_b = FlowManagerUnified.for_project("/path/to/project-b")

# 방법 2: 기존 인스턴스에서 전환
fmu.switch_project("/path/to/project-b")
```

### 5.2 CLI 통합
```python
def change_project(project_path: str):
    """프로젝트 전환 헬퍼"""
    global fmu

    # 디렉토리 변경 (선택적)
    os.chdir(project_path)

    # FlowManager 전환
    fmu = FlowManagerUnified.for_project(project_path)

    print(f"Switched to project: {project_path}")
```

## 6. 위험 요소 및 대응

### 6.1 위험 요소
1. **레거시 코드 호환성**: 기존 API 변경 시 문제
2. **캐시 일관성**: 여러 인스턴스 간 동기화
3. **파일 시스템 권한**: 디렉토리 생성 실패
4. **동시성 문제**: 여러 프로세스가 같은 파일 접근

### 6.2 대응 방안
1. **점진적 마이그레이션**: 레거시 API 유지하며 새 API 추가
2. **명시적 동기화**: sync 메서드 제공
3. **에러 핸들링**: 권한 문제 시 graceful degradation
4. **파일 잠금**: 필요시 lock 메커니즘 도입

## 7. 결론

이 설계를 통해 Flow 시스템은:
- ✅ 프로젝트별 독립적 관리 가능
- ✅ 동적 프로젝트 전환 지원
- ✅ Repository 패턴 유지
- ✅ 레거시 호환성 보장
- ✅ 확장 가능한 구조

다음 단계는 ProjectContext 클래스 구현부터 시작합니다.
