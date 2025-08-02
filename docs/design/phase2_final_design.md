
# 🏗️ Phase 2 최종 설계 (Context 전파 전략 확정)

## 📋 개요
사용자 피드백과 O3의 심층 분석을 반영하여 Phase 2 설계를 확정합니다.

## 🎯 핵심 결정사항

### 1. Context 전파 전략: Hybrid 방식 채택

#### 선택된 방안: **중앙 Session + 선택적 명시적 주입**

```python
# 기본 사용 (Session 기반)
api = get_flow_api()  # 내부적으로 current session 사용
plan = api.create_plan("새 프로젝트")

# 테스트/멀티스레드 (명시적 주입)
test_session = Session()
api = get_flow_api(session=test_session)
plan = api.create_plan("테스트 프로젝트")
```

#### 구현 상세
```python
from typing import Optional
from contextvars import ContextVar

# Thread-safe한 현재 세션 저장
_current_session: ContextVar[Optional['Session']] = ContextVar('current_session', default=None)

class Session:
    """REPL 세션의 모든 상태를 관리하는 중앙 객체"""

    def __init__(self):
        self.project_context: Optional[ProjectContext] = None
        self.flow_manager: Optional[ContextualFlowManager] = None
        self.metadata: Dict[str, Any] = {}

    def set_project(self, project_name: str) -> ProjectContext:
        """프로젝트 설정 (os.chdir 없이)"""
        # ProjectContext 생성/로드
        self.project_context = ProjectContext(name=project_name)

        # 해당 프로젝트의 FlowContext 자동 로드
        flow_path = self.project_context.resolve_path(".ai-brain/flow")
        self.flow_manager = ContextualFlowManager(flow_path)

        return self.project_context

    @property
    def flow_context(self) -> FlowContext:
        """현재 Flow 컨텍스트 (프로젝트에 종속)"""
        if not self.flow_manager:
            raise ValueError("No project selected")
        return self.flow_manager.get_context()

def get_current_session() -> Session:
    """현재 세션 반환 (없으면 생성)"""
    session = _current_session.get()
    if session is None:
        session = Session()
        _current_session.set(session)
    return session

def get_flow_api(session: Optional[Session] = None) -> FlowAPI:
    """Flow API 인스턴스 반환"""
    if session is None:
        session = get_current_session()
    return FlowAPI(session.flow_manager, session)
```

### 2. ProjectContext와 FlowContext의 관계: 종속 관계

```
Session
  │
  ├─ ProjectContext (1)
  │     ├─ name: str
  │     ├─ base_path: Path
  │     └─ resolve_path(relative: str) -> Path
  │
  └─ FlowManager (1) ← ProjectContext의 .ai-brain/flow 관리
        └─ FlowContext (1) ← 현재 활성 플랜/태스크 상태
              ├─ current_plan_id: str
              └─ metadata: dict
```

**핵심 원칙**:
- 1 Project = 1 FlowManager = 1 active FlowContext
- 프로젝트 전환 시 FlowContext도 자동 전환
- FlowContext는 항상 ProjectContext에 종속

### 3. 의존성 정리 전략: 단계적 접근

#### Phase 2-1: Session 인프라 구축 (우선)
```python
# 새 파일들 (기존 코드 영향 최소화)
- session.py          # Session 클래스
- flow_context.py     # FlowContext, ProjectContext
- contextual_flow_manager.py  # 새로운 매니저
```

#### Phase 2-2: 기존 코드 점진적 마이그레이션
```python
# simple_flow_commands.py 수정
def get_manager():
    """기존 호환성 유지"""
    # return _manager  # 기존
    return get_current_session().flow_manager  # 새로운 방식

# 전역 변수는 deprecation warning과 함께 유지
_manager = None  # @deprecated - use get_current_session()
```

#### Phase 2-3: 'h' 미정의 오류 수정
```python
# task_logger.py 수정
class TaskLogger:
    def __init__(self, ..., file_ops=None):
        # 의존성 주입
        self.file_ops = file_ops or self._get_default_file_ops()

    def _get_default_file_ops(self):
        # 런타임에 import (순환 참조 방지)
        from .file import write, append
        return {'write': write, 'append': append}
```

## 📐 구현 로드맵

### 🚀 Phase 2-1: Session 인프라 (1시간)
1. TODO #1: session.py 생성 - Session 클래스 구현
2. TODO #2: flow_context.py 생성 - Context 클래스들
3. TODO #3: contextual_flow_manager.py - 새 매니저
4. TODO #4: 기본 테스트 작성
5. TODO #5: get_current_session() 통합

### 🔧 Phase 2-2: API 마이그레이션 (1시간)
1. TODO #1: flow_api.py 생성 - Pythonic API
2. TODO #2: get_manager() 수정 - Session 사용
3. TODO #3: flow() 함수 내부 수정
4. TODO #4: 호환성 테스트
5. TODO #5: deprecation 경고 추가

### 📁 Phase 2-3: Project 관리 개선 (1시간)
1. TODO #1: ProjectContext 구현
2. TODO #2: flow_project_with_workflow 수정
3. TODO #3: os.chdir 제거
4. TODO #4: 파일 함수들 수정
5. TODO #5: 통합 테스트

### 🔗 Phase 2-4: 의존성 정리 (30분)
1. TODO #1: task_logger.py - 의존성 주입
2. TODO #2: simple_flow_commands.py - 'h' 제거
3. TODO #3: 순환 참조 검증
4. TODO #4: import 정리
5. TODO #5: 최종 테스트

## ⚠️ 중요 고려사항

### 1. 백업 및 브랜치 전략
```bash
git checkout -b feature/phase2-context-refactoring
git commit -am "backup: before phase 2 context refactoring"
```

### 2. 테스트 전략
- 각 Phase 완료 후 기존 기능 테스트
- Session 격리 테스트 추가
- 멀티스레드 시나리오 테스트

### 3. 마이그레이션 가이드
```python
# 기존 코드 (계속 작동)
flow("/create 프로젝트")
flow("/task add 작업")

# 새 코드 (권장)
api = get_flow_api()
plan = api.create_plan("프로젝트")
task = api.add_task("작업")

# 테스트 코드
with isolated_session() as session:
    api = get_flow_api(session)
    # 격리된 테스트
```

## ✅ 승인 요청

이 최종 설계는:
1. **Context 전파**: Hybrid 방식 (중앙 Session + 선택적 명시적 주입)
2. **관계 정의**: ProjectContext가 FlowContext를 소유하는 종속 관계
3. **의존성 정리**: 단계적 접근으로 위험 최소화

**이 설계안으로 Phase 2 구현을 시작하시겠습니까? (Y/N)**
