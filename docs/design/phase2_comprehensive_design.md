
# 🏗️ Phase 2: AI Coding Brain MCP 구조 개선 상세 설계


# 🏗️ Phase 2: AI Coding Brain MCP 구조 개선 상세 설계

## 📋 개요
Phase 1에서 치명적 오류를 수정한 후, 이제 시스템의 구조적 문제를 개선하여 확장성, 유지보수성, 사용성을 향상시킵니다.

## 🎯 목표
1. **전역 상태 제거**: 동시성과 확장성을 위한 상태 관리 개선
2. **Pythonic API 제공**: 직관적이고 AI 친화적인 인터페이스
3. **부작용 제거**: os.chdir 등 예측 불가능한 동작 제거
4. **의존성 정리**: 순환 참조 해결 및 모듈 구조 개선

## 🔍 현재 문제점 상세 분석

### 1. 전역 상태 의존 문제
```python
# 현재 코드 (simple_flow_commands.py)
_manager = None  # 전역 매니저 인스턴스
_current_plan_id = None  # 전역 선택 플랜

def flow(command: str):
    global _current_plan_id  # 5개 함수에서 사용
    # 문자열 파싱 기반 처리
```

**문제점**:
- 동시에 여러 작업 처리 불가
- 테스트 어려움 (상태 격리 불가)
- 예측 불가능한 동작 (다른 곳에서 상태 변경 시)

### 2. 문자열 파싱 API의 한계
```python
# 현재 사용법
flow("/create 새 프로젝트")  # 공백 처리 문제
flow("/task add 작업 이름")  # 파싱 오류 가능성
```

**문제점**:
- AI가 문자열 규칙을 학습해야 함
- 타입 체크 불가
- IDE 자동완성 지원 없음
- 오류 발생 가능성 높음

### 3. os.chdir 부작용
```python
# 현재 코드 (project.py)
os.chdir(str(project_path))  # 전역 작업 디렉토리 변경
```

**문제점**:
- 모든 상대 경로 해석 기준 변경
- 다른 모듈에 예측 불가능한 영향
- 병렬 작업 시 충돌 가능

### 4. 'h' 미정의 오류
```python
# task_logger.py, simple_flow_commands.py
import ai_helpers_new as h  # 순환 참조 위험
```

## 📐 설계 솔루션

### 1. Context 기반 상태 관리

#### 1.1 FlowContext 클래스 설계
```python
from dataclasses import dataclass
from typing import Optional, Dict, Any
import uuid

@dataclass
class FlowContext:
    """Flow 작업의 컨텍스트를 캡슐화"""
    context_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    current_plan_id: Optional[str] = None
    current_project: Optional[str] = None
    project_path: Optional[Path] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def select_plan(self, plan_id: str) -> None:
        """플랜 선택 (상태 변경을 메서드로 캡슐화)"""
        self.current_plan_id = plan_id
        self.metadata['plan_selected_at'] = datetime.now()

    def clear(self) -> None:
        """컨텍스트 초기화"""
        self.current_plan_id = None
        self.metadata.clear()
```

#### 1.2 ContextualFlowManager 설계
```python
class ContextualFlowManager:
    """컨텍스트 기반 Flow 매니저"""

    def __init__(self, repository: FlowRepository):
        self.repository = repository
        self._contexts: Dict[str, FlowContext] = {}

    def create_context(self) -> FlowContext:
        """새 컨텍스트 생성"""
        context = FlowContext()
        self._contexts[context.context_id] = context
        return context

    def get_context(self, context_id: str) -> Optional[FlowContext]:
        """컨텍스트 조회"""
        return self._contexts.get(context_id)

    # Plan 관련 메서드들
    def create_plan(self, name: str, context: FlowContext) -> Plan:
        """컨텍스트를 사용한 플랜 생성"""
        plan = Plan(name=name)
        self.repository.save_plan(plan)
        context.select_plan(plan.id)
        return plan

    def add_task(self, plan_id: str, title: str, context: FlowContext) -> Task:
        """컨텍스트를 사용한 태스크 추가"""
        # plan_id가 없으면 context의 current_plan_id 사용
        target_plan_id = plan_id or context.current_plan_id
        if not target_plan_id:
            raise ValueError("No plan selected in context")

        plan = self.repository.get_plan(target_plan_id)
        task = Task(title=title)
        plan.tasks[task.id] = task
        self.repository.save_plan(plan)
        return task
```

### 2. Pythonic API 설계

#### 2.1 고수준 API 래퍼
```python
class FlowAPI:
    """사용하기 쉬운 Pythonic API"""

    def __init__(self, manager: ContextualFlowManager):
        self.manager = manager
        self.context = manager.create_context()

    # 직관적인 메서드명과 명확한 인자
    def create_plan(self, name: str, description: str = "") -> Plan:
        """새 플랜 생성

        Args:
            name: 플랜 이름
            description: 플랜 설명 (선택)

        Returns:
            생성된 Plan 객체
        """
        plan = self.manager.create_plan(name, self.context)
        if description:
            plan.metadata['description'] = description
        return plan

    def select_plan(self, plan_id: str) -> bool:
        """플랜 선택

        Args:
            plan_id: 선택할 플랜 ID

        Returns:
            성공 여부
        """
        try:
            plan = self.manager.repository.get_plan(plan_id)
            self.context.select_plan(plan_id)
            return True
        except Exception:
            return False

    def add_task(self, title: str, plan_id: Optional[str] = None) -> Task:
        """현재 또는 지정된 플랜에 태스크 추가"""
        return self.manager.add_task(plan_id, title, self.context)

    def list_plans(self) -> List[Plan]:
        """모든 플랜 목록 조회"""
        return self.manager.repository.list_plans()

    def get_current_plan(self) -> Optional[Plan]:
        """현재 선택된 플랜 조회"""
        if self.context.current_plan_id:
            return self.manager.repository.get_plan(self.context.current_plan_id)
        return None

    # 편의 메서드들
    def complete_task(self, task_id: str) -> bool:
        """태스크 완료 처리"""
        plan = self.get_current_plan()
        if plan and task_id in plan.tasks:
            plan.tasks[task_id].status = TaskStatus.DONE
            plan.tasks[task_id].completed_at = datetime.now()
            self.manager.repository.save_plan(plan)
            return True
        return False

    # 체이닝을 위한 fluent 인터페이스
    def with_plan(self, plan_id: str) -> 'FlowAPI':
        """특정 플랜 컨텍스트에서 작업"""
        new_api = FlowAPI(self.manager)
        new_api.context.select_plan(plan_id)
        return new_api
```

#### 2.2 기존 flow() 함수와의 호환성 유지
```python
# 전역 인스턴스 (기존 코드 호환용)
_default_api: Optional[FlowAPI] = None

def get_flow_api() -> FlowAPI:
    """기본 Flow API 인스턴스 반환"""
    global _default_api
    if _default_api is None:
        manager = ContextualFlowManager(get_repository())
        _default_api = FlowAPI(manager)
    return _default_api

def flow(command: str = "") -> Dict[str, Any]:
    """기존 문자열 기반 API (호환성 유지)

    내부적으로 새로운 API를 사용하도록 리팩토링
    """
    api = get_flow_api()

    if not command or command == "/status":
        return _show_status_new(api)

    parts = command.strip().split(maxsplit=2)
    cmd = parts[0].lower()

    # 명령어 매핑
    if cmd == "/create" and len(parts) > 1:
        plan = api.create_plan(parts[1])
        return ok({"plan": plan.to_dict(), "msg": f"Plan 생성됨: {plan.id}"})

    elif cmd == "/select" and len(parts) > 1:
        if api.select_plan(parts[1]):
            return ok({"msg": f"Plan 선택됨: {parts[1]}"})
        return err("Plan을 찾을 수 없습니다")

    # ... 다른 명령어들도 동일하게 매핑

    return err(f"알 수 없는 명령어: {cmd}")

# 새로운 사용법 예시
def example_new_usage():
    # 방법 1: 직접 API 사용
    api = get_flow_api()
    plan = api.create_plan("새 프로젝트", "프로젝트 설명")
    task1 = api.add_task("첫 번째 작업")
    task2 = api.add_task("두 번째 작업")
    api.complete_task(task1.id)

    # 방법 2: 체이닝
    api.with_plan(plan.id).add_task("세 번째 작업").complete_task(task.id)

    # 방법 3: 기존 호환 (점진적 마이그레이션)
    flow("/create 또 다른 프로젝트")
```

### 3. ProjectContext로 os.chdir 제거

#### 3.1 ProjectContext 클래스
```python
@dataclass
class ProjectContext:
    """프로젝트 작업 컨텍스트"""
    name: str
    base_path: Path
    metadata: Dict[str, Any] = field(default_factory=dict)

    def resolve_path(self, relative_path: str) -> Path:
        """상대 경로를 프로젝트 기준으로 해석"""
        return self.base_path / relative_path

    def exists(self) -> bool:
        """프로젝트 존재 여부"""
        return self.base_path.exists()
```

#### 3.2 ProjectManager 설계
```python
class ProjectManager:
    """os.chdir 없이 프로젝트 관리"""

    def __init__(self):
        self.projects: Dict[str, ProjectContext] = {}
        self.current_project: Optional[ProjectContext] = None

    def register_project(self, name: str, path: Union[str, Path]) -> ProjectContext:
        """프로젝트 등록"""
        project = ProjectContext(name=name, base_path=Path(path))
        self.projects[name] = project
        return project

    def switch_project(self, name: str) -> ProjectContext:
        """프로젝트 전환 (os.chdir 없이)"""
        if name not in self.projects:
            # 자동 탐색
            project_path = self._find_project(name)
            if project_path:
                self.register_project(name, project_path)
            else:
                raise ValueError(f"Project not found: {name}")

        self.current_project = self.projects[name]
        return self.current_project

    def get_current_project(self) -> Optional[ProjectContext]:
        """현재 프로젝트 반환"""
        return self.current_project

    def resolve_path(self, path: str) -> Path:
        """현재 프로젝트 기준으로 경로 해석"""
        if self.current_project:
            return self.current_project.resolve_path(path)
        return Path(path)  # 프로젝트 없으면 그대로 사용
```

#### 3.3 파일 작업 함수 수정
```python
# file.py 수정
def read(path: str, project_context: Optional[ProjectContext] = None, **kwargs) -> Dict[str, Any]:
    """프로젝트 컨텍스트를 고려한 파일 읽기"""
    # 절대 경로가 아니면 프로젝트 기준으로 해석
    file_path = Path(path)
    if not file_path.is_absolute() and project_context:
        file_path = project_context.resolve_path(path)

    # 기존 읽기 로직...
    return _read_file_impl(file_path, **kwargs)

# 전역 프로젝트 매니저 (선택적 사용)
_project_manager = ProjectManager()

def get_project_manager() -> ProjectManager:
    return _project_manager

# 헬퍼 함수
def read_in_project(path: str, **kwargs) -> Dict[str, Any]:
    """현재 프로젝트 기준으로 파일 읽기"""
    pm = get_project_manager()
    return read(path, project_context=pm.current_project, **kwargs)
```

### 4. 의존성 정리

#### 4.1 순환 참조 해결
```python
# task_logger.py 수정
# import ai_helpers_new as h  # 제거

# 필요한 함수만 주입받도록 변경
class TaskLogger:
    def __init__(self, ..., file_writer=None):
        self.file_writer = file_writer or self._default_file_writer

    def _default_file_writer(self, path: str, content: str):
        # 기본 파일 쓰기 (표준 라이브러리만 사용)
        with open(path, 'a', encoding='utf-8') as f:
            f.write(content)
```

#### 4.2 의존성 주입 패턴
```python
# dependency_injection.py
class DIContainer:
    """간단한 의존성 주입 컨테이너"""

    def __init__(self):
        self._services = {}
        self._singletons = {}

    def register(self, name: str, factory, singleton: bool = False):
        """서비스 등록"""
        self._services[name] = (factory, singleton)

    def get(self, name: str):
        """서비스 조회"""
        if name not in self._services:
            raise ValueError(f"Service not found: {name}")

        factory, is_singleton = self._services[name]

        if is_singleton:
            if name not in self._singletons:
                self._singletons[name] = factory()
            return self._singletons[name]

        return factory()

# 전역 컨테이너
container = DIContainer()

# 서비스 등록
container.register('flow_manager', lambda: ContextualFlowManager(get_repository()), singleton=True)
container.register('project_manager', lambda: ProjectManager(), singleton=True)
container.register('file_writer', lambda: write_file, singleton=False)
```

## 🚀 구현 계획

### Task 1: FlowContext 및 ContextualFlowManager 구현
1. TODO #1: FlowContext 데이터 클래스 생성
2. TODO #2: ContextualFlowManager 클래스 구현
3. TODO #3: 기존 UltraSimpleFlowManager 마이그레이션
4. TODO #4: 컨텍스트 기반 명령어 처리
5. TODO #5: 단위 테스트 작성

### Task 2: Pythonic API 구현
1. TODO #1: FlowAPI 클래스 구현
2. TODO #2: 직관적 메서드명 정의
3. TODO #3: 타입 힌트 및 문서화
4. TODO #4: flow() 함수 호환성 래퍼
5. TODO #5: 사용 예제 및 테스트

### Task 3: ProjectContext로 os.chdir 제거
1. TODO #1: ProjectContext 클래스 구현
2. TODO #2: ProjectManager 구현
3. TODO #3: 파일 작업 함수 수정
4. TODO #4: flow_project_with_workflow 리팩토링
5. TODO #5: 마이그레이션 테스트

### Task 4: 의존성 정리 및 'h' 오류 수정
1. TODO #1: 순환 참조 분석
2. TODO #2: 의존성 주입 패턴 적용
3. TODO #3: task_logger.py 수정
4. TODO #4: simple_flow_commands.py 수정
5. TODO #5: 통합 테스트

## ⚠️ 위험 관리

### 호환성 유지 전략
1. **점진적 마이그레이션**: 기존 API 유지하면서 새 API 추가
2. **Deprecation 경고**: 기존 API 사용 시 경고 메시지
3. **마이그레이션 가이드**: 문서 제공

### 성능 고려사항
1. **컨텍스트 관리**: 메모리 누수 방지를 위한 수명 관리
2. **캐싱**: 자주 사용되는 프로젝트 정보 캐싱
3. **지연 로딩**: 필요할 때만 리소스 로드

## 📊 예상 효과

### 개발자 경험 향상
- IDE 자동완성 지원
- 타입 체크 가능
- 명확한 API 문서

### 시스템 품질 향상
- 테스트 용이성 증가
- 동시성 지원 가능
- 예측 가능한 동작

### AI 통합 개선
- 직관적인 함수명
- 명확한 인자와 반환값
- 오류 처리 개선

## 🔄 마이그레이션 예시

### 기존 코드
```python
flow("/create 새 프로젝트")
flow("/task add 첫 번째 작업")
flow("/task done task_123")
```

### 새로운 코드
```python
api = get_flow_api()
plan = api.create_plan("새 프로젝트")
task = api.add_task("첫 번째 작업")
api.complete_task(task.id)
```

### 호환성 모드
```python
# 둘 다 동작
flow("/create 새 프로젝트")  # 기존 방식
api.create_plan("새 프로젝트")  # 새 방식
```

## ✅ 승인 요청
Phase 2의 상세 설계를 검토하셨습니다.
이 설계안대로 구현을 진행하시겠습니까?

특히 다음 우선순위로 진행 예정입니다:
1. FlowContext (전역 상태 제거)
2. Pythonic API
3. ProjectContext (os.chdir 제거)
4. 의존성 정리

**설계안을 승인하시겠습니까? (Y/N)**



## 🔄 Phase 2 구조 개선 시각화

### 1️⃣ 전역 상태 제거 (Before → After)

**Before (현재)**
```
┌─────────────────────────┐
│   simple_flow_commands  │
├─────────────────────────┤
│ _manager (전역)         │ ← 동시성 문제
│ _current_plan_id (전역) │ ← 상태 오염 위험
└─────────────────────────┘
         ↓
    모든 함수가 공유
```

**After (개선)**
```
┌─────────────────────────┐
│   ContextualFlowManager │
├─────────────────────────┤
│ contexts: Dict[id, ctx] │ ← 격리된 상태
└─────────────────────────┘
         ↓
┌──────────────┐ ┌──────────────┐
│ FlowContext1 │ │ FlowContext2 │ ← 독립적 작업
├──────────────┤ ├──────────────┤
│ plan_id: A   │ │ plan_id: B   │
│ project: X   │ │ project: Y   │
└──────────────┘ └──────────────┘
```

### 2️⃣ API 진화 (문자열 → 객체)

**Before**
```python
# AI가 문자열 규칙을 학습해야 함
flow("/create 프로젝트 이름")  # 공백 처리?
flow("/task add 작업 제목")    # 파싱 오류?
```

**After**
```python
# 명확한 메서드와 타입
api = FlowAPI()
plan = api.create_plan(name="프로젝트 이름")
task = api.add_task(title="작업 제목", plan_id=plan.id)
```

### 3️⃣ 프로젝트 경로 관리

**Before (os.chdir 사용)**
```
프로세스 작업 디렉토리
    ↓ os.chdir
ProjectA/ ← 전역 변경!
    ↓
모든 상대 경로가 영향받음
```

**After (ProjectContext 사용)**
```
ProjectManager
├── ProjectContext("A") → /path/to/A/
├── ProjectContext("B") → /path/to/B/
└── current_project → 선택된 컨텍스트

상대 경로 → context.resolve_path() → 절대 경로
```

### 4️⃣ 의존성 구조 개선

**Before**
```
task_logger.py ─┐
                ├→ import ai_helpers_new as h ← 순환 참조!
flow_commands ──┘
```

**After**
```
DIContainer
├── register('file_writer', write_func)
├── register('flow_manager', manager)
└── register('logger', logger)

task_logger.py → container.get('file_writer')
```



## 📋 Phase 2 마이그레이션 가이드

### 🔧 단계별 구현 순서

#### Step 1: FlowContext 구현 (영향 최소화)
```python
# 1. 새 파일 생성: flow_context.py
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

@dataclass
class FlowContext:
    context_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    current_plan_id: Optional[str] = None
    # ... 설계대로 구현
```

#### Step 2: ContextualFlowManager 구현
```python
# 2. 새 파일: contextual_flow_manager.py
# 기존 UltraSimpleFlowManager를 상속하여 점진적 마이그레이션
class ContextualFlowManager(UltraSimpleFlowManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._contexts: Dict[str, FlowContext] = {}

    # 새 메서드 추가...
```

#### Step 3: FlowAPI 구현 및 flow() 함수 수정
```python
# 3. simple_flow_commands.py 수정
# 기존 전역 변수는 deprecated 표시
_manager = None  # @deprecated - use get_flow_api()
_current_plan_id = None  # @deprecated

# 새로운 API
def get_flow_api() -> FlowAPI:
    # 싱글톤 패턴으로 구현
    pass

# 기존 flow() 함수 수정 - 내부에서 새 API 사용
def flow(command: str = "") -> Dict[str, Any]:
    # 호환성 유지하면서 새 API로 위임
    api = get_flow_api()
    # ... 명령어 파싱 후 api 메서드 호출
```

### 🔄 점진적 마이그레이션 전략

#### Phase 2-A: 핵심 구조 변경 (1-2시간)
1. FlowContext 클래스 생성
2. ContextualFlowManager 구현
3. 기존 테스트 통과 확인

#### Phase 2-B: API 개선 (1시간)
1. FlowAPI 클래스 구현
2. flow() 함수 래핑
3. 사용 예제 작성

#### Phase 2-C: 프로젝트 관리 (1시간)
1. ProjectContext 구현
2. os.chdir 제거
3. 파일 함수 수정

#### Phase 2-D: 의존성 정리 (30분)
1. 순환 참조 해결
2. 'h' 오류 수정

### ⚠️ 주의사항

1. **백업 필수**
   ```bash
   git checkout -b feature/phase2-structural-improvements
   git commit -am "backup: before phase 2"
   ```

2. **테스트 우선**
   - 각 단계마다 기존 기능 테스트
   - 새 기능에 대한 단위 테스트 추가

3. **문서화**
   - 각 새로운 클래스/함수에 docstring
   - 타입 힌트 필수

### 📝 체크리스트

- [ ] Git 브랜치 생성
- [ ] Phase 2-A 구현
  - [ ] FlowContext.py 생성
  - [ ] ContextualFlowManager 구현
  - [ ] 기존 테스트 통과
- [ ] Phase 2-B 구현
  - [ ] FlowAPI 클래스
  - [ ] flow() 호환성 래퍼
  - [ ] 새 API 테스트
- [ ] Phase 2-C 구현
  - [ ] ProjectContext
  - [ ] os.chdir 제거
  - [ ] 파일 함수 수정
- [ ] Phase 2-D 구현
  - [ ] 순환 참조 해결
  - [ ] 통합 테스트
- [ ] 문서 업데이트
- [ ] PR 생성

