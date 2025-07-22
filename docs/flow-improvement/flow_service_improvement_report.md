# FlowService 개선 보고서

## 개요
FlowService를 ProjectContext와 통합하여 프로젝트별 격리된 current_flow 관리를 구현했습니다.

## 주요 개선사항

### 1. ProjectContext 통합
- FlowService 생성자에 `context` 매개변수 추가
- Repository의 context를 자동으로 사용하는 옵션
- 프로젝트별 경로 관리

### 2. 전역 파일 제거
- **이전**: `~/.ai-flow/current_flow.txt` (모든 프로젝트 공유)
- **이후**: `{project}/.ai-brain/current_flow.txt` (프로젝트별 격리)

### 3. 동적 Context 변경
```python
# Context 변경 시 Repository와 Service 모두 업데이트 필요
repository.set_context(new_context)
service.set_context(new_context)
```

### 4. 레거시 마이그레이션
- 전역 current_flow.txt가 존재하면 자동으로 프로젝트로 마이그레이션
- 기존 사용자의 설정을 보존

### 5. 새로운 메서드
- `set_context(context)`: 프로젝트 context 변경
- `get_project_info()`: 프로젝트별 서비스 정보
- `clear_current_flow()`: current flow 선택 해제

## 테스트 결과
- ✅ ProjectContext 통합 테스트 통과
- ✅ 프로젝트 전환 테스트 통과
- ✅ Current flow 파일 관리 테스트 통과
- ✅ 레거시 호환성 확인

## 사용 예시

### 기본 사용
```python
context = ProjectContext("/path/to/project")
repo = JsonFlowRepository(context=context)
service = FlowService(repo, context=context)

# Flow 생성
flow = service.create_flow("My Flow")
```

### 프로젝트 전환
```python
# 새 프로젝트로 전환
new_context = ProjectContext("/path/to/another/project")
repo.set_context(new_context)
service.set_context(new_context)

# 이제 새 프로젝트의 flows를 관리
flows = service.list_flows()  # 새 프로젝트의 flows
```

## 파일 구조
```
project/
├── .ai-brain/
│   ├── flows.json          # Flow 데이터
│   ├── current_flow.txt    # 현재 선택된 Flow ID
│   └── backups/            # 자동 백업
```

## 다음 단계
1. PlanService와 TaskService에도 ProjectContext 적용
2. FlowManagerUnified에 프로젝트 전환 API 추가
3. 전체 통합 테스트
