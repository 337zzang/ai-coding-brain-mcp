# FlowManagerUnified 통합 설계

## 1. 개선 목표
- 프로젝트별 인스턴스 관리
- 런타임 프로젝트 전환
- 레거시 API 호환성
- 명확한 의존성 주입

## 2. 개선된 설계

```python
# python/ai_helpers_new/flow_manager_unified.py

from typing import Optional, Dict, Any
from pathlib import Path

from .infrastructure.project_context import ProjectContext
from .infrastructure.flow_repository import JsonFlowRepository
from .service.flow_service import FlowService
from .service.plan_service import PlanService
from .service.task_service import TaskService

class FlowManagerUnified:
    """프로젝트 인식 통합 Flow Manager"""

    # 클래스 레벨 인스턴스 캐시 (프로젝트별)
    _instances: Dict[str, 'FlowManagerUnified'] = {}

    def __init__(
        self,
        context: ProjectContext,
        repository: JsonFlowRepository,
        flow_service: FlowService,
        plan_service: PlanService,
        task_service: TaskService,
        context_manager=None
    ):
        self.context = context
        self.repository = repository
        self.flow_service = flow_service
        self.plan_service = plan_service
        self.task_service = task_service
        self.context_manager = context_manager

        # 내부 캐시
        self._flows: Dict[str, Any] = {}
        self._current_flow = None

        # 초기 동기화
        self._sync_flows_from_service()

    @classmethod
    def for_project(cls, project_root: str, context_manager=None) -> 'FlowManagerUnified':
        """프로젝트별 인스턴스 생성/반환

        Args:
            project_root: 프로젝트 루트 디렉토리
            context_manager: 선택적 context manager

        Returns:
            FlowManagerUnified 인스턴스
        """
        project_root = str(Path(project_root).resolve())

        # 캐시 확인
        if project_root in cls._instances:
            instance = cls._instances[project_root]
            # Context manager 업데이트
            if context_manager:
                instance.context_manager = context_manager
            return instance

        # 새 인스턴스 생성
        context = ProjectContext(project_root)
        repository = JsonFlowRepository(context)
        flow_service = FlowService(repository, context)
        plan_service = PlanService(flow_service)
        task_service = TaskService(plan_service)

        instance = cls(
            context=context,
            repository=repository,
            flow_service=flow_service,
            plan_service=plan_service,
            task_service=task_service,
            context_manager=context_manager
        )

        # 캐시에 저장
        cls._instances[project_root] = instance

        return instance

    @classmethod
    def get_current_project_instance(cls, context_manager=None) -> 'FlowManagerUnified':
        """현재 작업 디렉토리 기준 인스턴스 반환"""
        return cls.for_project(Path.cwd(), context_manager)

    def switch_project(self, new_root: str) -> 'FlowManagerUnified':
        """다른 프로젝트로 전환

        Args:
            new_root: 새 프로젝트 루트

        Returns:
            새 프로젝트의 FlowManagerUnified 인스턴스
        """
        # 새 인스턴스 반환 (캐시 활용)
        return self.__class__.for_project(new_root, self.context_manager)

    def reload(self):
        """현재 프로젝트 다시 로드"""
        # 모든 서비스 동기화
        self.flow_service.sync()
        self._sync_flows_from_service()

    def get_project_info(self) -> Dict[str, Any]:
        """현재 프로젝트 정보"""
        info = self.context.get_project_info()
        info.update({
            'repository_info': self.repository.get_project_info(),
            'service_info': self.flow_service.get_project_info(),
            'cached_flows': len(self._flows)
        })
        return info

    # === 레거시 호환성 메서드 ===

    def __init_legacy__(self, storage_path: str = None, context_manager=None):
        """레거시 생성자 (deprecated)"""
        import warnings
        warnings.warn(
            "Direct initialization is deprecated. Use FlowManagerUnified.for_project() instead.",
            DeprecationWarning
        )

        if storage_path:
            # storage_path에서 프로젝트 루트 추론
            path = Path(storage_path)
            if path.name == "flows.json" and path.parent.name == ".ai-brain":
                project_root = path.parent.parent
            else:
                project_root = Path.cwd()
        else:
            project_root = Path.cwd()

        # for_project 사용
        instance = self.__class__.for_project(str(project_root), context_manager)

        # 속성 복사
        self.__dict__.update(instance.__dict__)
```

## 3. 사용 패턴

### 3.1 단일 프로젝트
```python
# 현재 디렉토리 프로젝트
fmu = FlowManagerUnified.get_current_project_instance()

# 특정 프로젝트
fmu = FlowManagerUnified.for_project("/path/to/project")
```

### 3.2 멀티 프로젝트
```python
# 여러 프로젝트 동시 작업
fmu_a = FlowManagerUnified.for_project("/projects/proj-a")
fmu_b = FlowManagerUnified.for_project("/projects/proj-b")

# 프로젝트 전환
fmu = fmu.switch_project("/projects/proj-c")
```

### 3.3 CLI 통합
```python
# 전역 인스턴스 관리
current_fmu = None

def change_project(path: str):
    global current_fmu
    current_fmu = FlowManagerUnified.for_project(path)
    print(f"Switched to: {path}")

def get_fmu():
    global current_fmu
    if current_fmu is None:
        current_fmu = FlowManagerUnified.get_current_project_instance()
    return current_fmu
```

## 4. 마이그레이션 전략

1. **Phase 1**: 새 API 추가, 레거시 유지
2. **Phase 2**: 경고 메시지 추가
3. **Phase 3**: 내부 구현 새 API로 전환
4. **Phase 4**: 레거시 API 제거 (major version)

## 5. 성능 최적화

- 프로젝트별 인스턴스 캐싱
- 불필요한 파일 I/O 최소화
- 지연 로딩 적용
- 메모리 사용량 모니터링
