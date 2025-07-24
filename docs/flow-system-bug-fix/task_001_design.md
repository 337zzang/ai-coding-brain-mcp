# 📋 작업 제목: Flow 시스템 버그 수정

## 🏗️ 전체 설계 (Architecture Design)

### 목표
- Flow 시스템의 AttributeError 문제 해결
- 안정적이고 확장 가능한 아키텍처로 개선
- 테스트 가능한 구조로 리팩토링

### 범위
- flow_repository.py 수정
- FlowManagerUnified 초기화 로직 개선
- 에러 처리 강화
- 단위 테스트 추가

### 접근 방법
1. 즉각적인 버그 수정 (Quick Fix)
2. 아키텍처 개선 (Long-term Solution)
3. 테스트 및 검증

### 예상 소요 시간
- 분석 및 설계: 30분 ✅ (완료)
- 버그 수정: 1시간
- 테스트 작성: 30분
- 문서화: 30분
- 총 예상 시간: 2시간 30분

## 🔍 현재 상태 분석

### 환경 확인
```python
# 프로젝트: ai-coding-brain-mcp
# Git 브랜치: (확인 필요)
# 환경변수: CONTEXT_SYSTEM=on
```

### 문제의 핵심
1. **FlowManagerUnified.__init__** (line 48)
   ```python
   self.repository = JsonFlowRepository(storage_path)  # storage_path는 string
   ```

2. **JsonFlowRepository.__init__** (line 49)
   - 첫 번째 파라미터가 `context`로 정의됨
   - string을 받으면 self._context = string이 됨

3. **storage_path 속성** (line 119)
   ```python
   return self._context.flow_file  # string에는 flow_file 속성이 없음!
   ```

### 영향받는 파일
- `flow_repository.py` - 직접적인 오류 발생
- `flow_manager_unified.py` - 잘못된 초기화
- `workflow_commands.py` - wf() 함수 (간접 영향)

### 위험도: 🔴 높음
- 모든 Flow 관련 명령이 작동하지 않음
- 새 프로젝트 생성 불가
- 기존 프로젝트 관리 불가

## 📐 상세 설계 (Detailed Design)

### 1. 아키텍처 결정사항

#### Option 1: Quick Fix (즉시 적용 가능) ✅ 권장
```python
# FlowManagerUnified.__init__ 수정
self.repository = JsonFlowRepository(storage_path=storage_path)  # 명시적 키워드 인자
```

#### Option 2: 근본적 해결
```python
# FlowManagerUnified에 ProjectContext 도입
from .infrastructure.project_context import ProjectContext

def __init__(self, storage_path: str = None, context_manager=None):
    # ...
    if storage_path:
        context = ProjectContext(Path(storage_path).parent.parent)
    else:
        context = ProjectContext(Path.cwd())

    self.repository = JsonFlowRepository(context=context)
```

### 2. 구현 상세

#### Step 1: JsonFlowRepository 시그니처 확인 및 문서화
```python
def __init__(self, context: Optional[ProjectContext] = None, storage_path: Optional[str] = None):
    """
    Initialize repository

    Args:
        context: ProjectContext for dynamic path management (preferred)
        storage_path: Legacy storage path (deprecated) - USE KEYWORD ARGUMENT
    """
```

#### Step 2: FlowManagerUnified 수정
```python
# BEFORE (버그)
self.repository = JsonFlowRepository(storage_path)

# AFTER (수정)
self.repository = JsonFlowRepository(storage_path=storage_path)
```

#### Step 3: 에러 처리 강화
```python
# JsonFlowRepository.__init__에 타입 체크 추가
if context is not None and not isinstance(context, ProjectContext):
    raise TypeError(f"context must be ProjectContext, not {type(context).__name__}")
```

### 3. 데이터 흐름
```
FlowManagerUnified.__init__
    ↓ storage_path (string)
    ↓ 
JsonFlowRepository(storage_path=storage_path)  # 키워드 인자 사용
    ↓
    ↓ storage_path parameter로 전달
    ↓
_create_context_from_path(storage_path)
    ↓
    ↓ ProjectContext 객체 생성
    ↓
self._context = ProjectContext 객체
    ↓
self._context.flow_file  # ✅ 정상 작동
```

## 🛠️ Task별 실행 계획

### Task 1: 즉시 버그 수정
- **목표**: FlowManagerUnified의 JsonFlowRepository 초기화 수정
- **상세 설계**:
  ```python
  # flow_manager_unified.py line 48 수정
  self.repository = JsonFlowRepository(storage_path=storage_path)
  ```
- **테스트 계획**: 
  - wf("/flow create test") 실행
  - 에러 없이 flow 생성 확인
- **예상 결과**: 
  - 성공 시: Flow 명령어 정상 작동
  - 실패 시: 다른 위치에도 동일한 문제 있음

### Task 2: 타입 안전성 강화
- **목표**: 향후 동일한 실수 방지
- **상세 설계**:
  ```python
  # JsonFlowRepository.__init__에 추가
  if context is not None:
      if not isinstance(context, ProjectContext):
          raise TypeError(f"context must be ProjectContext instance, got {type(context)}")
  ```

### Task 3: 테스트 작성
- **목표**: 회귀 방지
- **테스트 케이스**:
  1. JsonFlowRepository 올바른 초기화
  2. FlowManagerUnified flow 생성
  3. 잘못된 타입 전달 시 에러

### Task 4: 다른 위치 점검
- **목표**: 동일한 패턴의 버그 찾기
- **검색 대상**:
  - JsonFlowRepository( 패턴
  - 위치 인자로 string 전달하는 곳

## ⚠️ 위험 요소 및 대응 계획

| 위험 요소 | 발생 가능성 | 영향도 | 대응 방안 |
|----------|------------|-------|-----------|
| 다른 곳에도 동일 버그 | 높음 | 높음 | 전체 코드베이스 검색 |
| 기존 데이터 호환성 | 낮음 | 중간 | 마이그레이션 스크립트 |
| 테스트 부족 | 중간 | 높음 | 단위 테스트 필수 작성 |

## ❓ 확인 필요 사항
1. 이 수정이 기존 프로젝트들에 영향을 주나요?
2. JsonFlowRepository를 사용하는 다른 곳은 없나요?
3. storage_path 대신 ProjectContext를 사용하도록 전면 개편할까요?

**✅ 이 계획대로 진행해도 될까요?**