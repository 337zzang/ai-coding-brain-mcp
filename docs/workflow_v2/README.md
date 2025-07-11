# Workflow v2 시스템

## 개요
Workflow v2는 프로젝트 작업을 체계적으로 관리하기 위한 차세대 워크플로우 시스템입니다.
기존 v1 시스템의 한계를 극복하고 execute_code와의 완벽한 통합을 제공합니다.

## 주요 특징

### 1. 함수형 API
- 모든 기능을 함수로 직접 호출 가능
- execute_code 환경에서 원활한 실행
- 명확한 입력/출력 인터페이스

### 2. 독립적인 구조
- v1 시스템과 완전히 분리된 구현
- 깔끔한 모듈 구조
- 확장 가능한 아키텍처

### 3. 강력한 데이터 관리
- 프로젝트별 독립적인 워크플로우 파일
- 안정적인 데이터 영속성
- JSON 기반 저장 구조

## 시작하기

### 설치
```python
# 이미 프로젝트에 포함되어 있음
from workflow.v2 import WorkflowV2Manager
```

### 기본 사용법

#### 1. 매니저 생성
```python
manager = WorkflowV2Manager("my_project")
```

#### 2. 플랜 생성
```python
plan = manager.create_plan("프로젝트 계획", "설명")
```

#### 3. 태스크 추가
```python
task = manager.add_task("할 일", "상세 설명")
```

#### 4. 상태 확인
```python
status = manager.get_status()
print(f"진행률: {status['progress_percent']}%")
```

## 고급 기능

### 명령어 디스패처
```python
from workflow.v2 import execute_workflow_command

result = execute_workflow_command("/status")
result = execute_workflow_command("/plan 새 계획 | 설명")
result = execute_workflow_command("/task 새 작업 | 설명")
```

### 핸들러 함수
```python
from workflow.v2 import workflow_status, workflow_plan, workflow_task

# 상태 조회
status = workflow_status()

# 플랜 생성
plan = workflow_plan("계획명", "설명")

# 태스크 추가
task = workflow_task("작업명", "설명")
```

## 데이터 구조

### WorkflowPlan
- `id`: 고유 식별자
- `name`: 플랜 이름
- `description`: 설명
- `status`: 상태 (draft/active/completed/archived)
- `tasks`: 태스크 목록
- `created_at`: 생성 시각
- `updated_at`: 수정 시각

### Task
- `id`: 고유 식별자
- `title`: 태스크 제목
- `description`: 설명
- `status`: 상태 (todo/in_progress/completed/cancelled)
- `created_at`: 생성 시각
- `completed_at`: 완료 시각
- `notes`: 메모 목록
- `outputs`: 결과물 딕셔너리

## 파일 구조
```
memory/workflow_v2/
└── {project_name}_workflow.json
```

## 마이그레이션 가이드

### v1에서 v2로
1. 기존 workflow.json 백업
2. WorkflowV2Manager로 새 플랜 생성
3. 기존 태스크 데이터 이전
4. 새 시스템으로 전환

## 문제 해결

### 모듈을 찾을 수 없음
```python
import sys
sys.path.insert(0, 'python')
```

### 데이터 로드 실패
워크플로우 파일이 손상되었을 수 있습니다.
`memory/workflow_v2/` 디렉토리를 확인하세요.

## 기여하기
이슈 리포트와 개선 제안을 환영합니다!
