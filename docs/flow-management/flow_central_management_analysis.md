# Flow 중앙 관리 시스템 분석

## 개요
AI Coding Brain MCP의 Flow 시스템은 중앙 집중식으로 관리되며, FlowManager를 통해 모든 작업이 수행됩니다.

## 아키텍처

```
사용자 코드
    ↓
FlowManager (중앙 인터페이스)
    ↓
CachedFlowService (비즈니스 로직 + 캐싱)
    ↓
JsonRepository (영속성 계층)
    ↓
.ai-brain/flows.json (저장 파일)
```

## 핵심 컴포넌트

### 1. FlowManager
- **위치**: `python/ai_helpers_new/flow_manager.py`
- **역할**: 사용자가 직접 사용하는 중앙 인터페이스
- **주요 메서드**:
  - `create_flow()`: Flow 생성
  - `select_flow()`: Flow 선택
  - `list_flows()`: Flow 목록 조회
  - `current_flow`: 현재 활성 Flow 속성

### 2. CachedFlowService
- **위치**: `python/ai_helpers_new/service/cached_flow_service.py`
- **역할**: Flow 데이터의 캐싱 및 비즈니스 로직 처리
- **특징**: 메모리 캐시로 성능 최적화

### 3. JsonRepository
- **위치**: `python/ai_helpers_new/repository/json_repository.py`
- **역할**: JSON 파일로 데이터 영속화
- **저장 위치**: `.ai-brain/flows.json`

## 사용 방법

```python
# FlowManager 인스턴스 생성
from ai_helpers_new.flow_manager import FlowManager
manager = FlowManager()

# 또는 전역 인스턴스 사용
from ai_helpers_new import get_flow_manager
manager = get_flow_manager()

# Flow 작업
flow = manager.create_flow('project_name')
manager.select_flow(flow.id)
current = manager.current_flow
```

## 현재 상태 및 문제점

### 작동하는 기능
- Flow 생성, 선택, 삭제, 목록 조회
- Context 시스템과의 자동 통합
- 메모리 내 캐싱

### 문제점
1. **영속성 문제**: 메모리의 Flow가 파일로 제대로 저장되지 않음
2. **Plan/Task 미완성**: Plan, Task 생성 시 에러 발생
3. **동기화 실패**: 메모리와 파일 간 데이터 불일치

## 권장사항
1. Flow를 임시 작업 세션으로만 사용
2. 중요 데이터는 별도 파일로 수동 저장
3. Git 커밋으로 작업 이력 관리
4. Context Reporter로 작업 내역 추적

## 관련 파일
- `flow_manager.py`: 메인 인터페이스
- `cached_flow_service.py`: 비즈니스 로직
- `json_repository.py`: 데이터 저장
- `workflow_commands.py`: CLI 명령어
- `flow_context_wrapper.py`: Context 통합

---
작성일: 2025-07-24
