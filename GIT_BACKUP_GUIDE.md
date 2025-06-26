# 🔄 Git 기반 통합 백업 시스템 가이드

## 📋 목차
1. [개요](#개요)
2. [주요 기능](#주요-기능)
3. [사용 방법](#사용-방법)
4. [자동 백업](#자동-백업)
5. [워크플로우](#워크플로우)
6. [문제 해결](#문제-해결)

## 개요

AI Coding Brain MCP의 Git 기반 통합 백업 시스템은 모든 코드 변경사항을 Git으로 관리하여 안정성과 효율성을 극대화합니다.

### 핵심 구성요소

- **GitVersionManager** (`python/git_version_manager.py`): Git 작업 중앙 관리
- **MCP Git Tools** (`python/mcp_git_tools.py`): MCP 인터페이스
- **Auto Tracking Wrapper** (`python/auto_tracking_wrapper.py`): 자동 백업 트리거

## 주요 기능

### 1. Git 상태 확인
```python
git_status()
```
- 현재 브랜치 확인
- 변경된 파일 목록
- 스테이징 상태

### 2. 스마트 커밋 (백업)
```python
git_commit_smart()  # 자동 메시지 생성
git_commit_smart("커스텀 메시지")
```
- 작업 컨텍스트 기반 자동 메시지
- Wisdom 시스템 통합
- 자동 스테이징 옵션

### 3. 스마트 브랜치
```python
git_branch_smart()  # 자동 이름 생성
git_branch_smart("feature/login")
```
- Task 기반 브랜치명 자동 생성
- 현재 상태 자동 백업

### 4. 안전한 롤백
```python
git_rollback_smart()  # 이전 커밋으로
git_rollback_smart("abc1234")  # 특정 커밋으로
```
- 롤백 전 백업 브랜치 생성
- Wisdom 기반 안정 커밋 선택

### 5. 원격 푸시
```python
git_push()  # origin으로 현재 브랜치
git_push("origin", "main")
```

## 자동 백업

### 자동 백업 트리거

파일 작업 시 자동으로 Git 커밋이 실행됩니다:

1. **파일 작업** (`create_file`, `write_file`, `modify`)
2. **코드 블록 수정** (`replace_block`, `insert_block`)
3. **5회 작업마다 자동 커밋**

### 자동 백업 설정

환경 변수로 제어:
```bash
# Git 자동 백업 디버그 활성화
export DEBUG_GIT=true

# 자동 백업 비활성화 (수동 모드)
export AUTO_GIT_COMMIT=false
```

## 워크플로우

### 1. 일반 작업 플로우
```python
# 1. 프로젝트 시작
flow_project("my-project")

# 2. 작업 브랜치 생성
git_branch_smart()

# 3. 코드 작업 (자동 백업됨)
create_file("feature.py", code)
replace_block("main.py", "function", new_code)

# 4. 수동 백업 (필요시)
git_commit_smart("중요 기능 완성")

# 5. 원격 백업
git_push()
```

### 2. Task 기반 플로우
```python
# 1. 새 작업 시작
next_task()  # 자동으로 브랜치 생성 검토

# 2. 작업 진행 (자동 백업)
# ... 코드 작업 ...

# 3. 작업 완료
task_manage("done", ["1-1"])  # 자동 커밋 및 병합 검토
```

### 3. 복원 플로우
```python
# 1. 현재 상태 확인
git_status()

# 2. 커밋 히스토리 확인
execute_code: 
    git_manager = get_git_manager()
    # 최근 5개 커밋 확인

# 3. 안전한 롤백
git_rollback_smart()  # 백업 브랜치 자동 생성
```

## 문제 해결

### Git 초기화 문제
```python
# Git 저장소 수동 초기화
execute_code:
    import subprocess
    subprocess.run(["git", "init"], cwd=".")
```

### 자동 백업 중지
```python
# 임시 중지
execute_code:
    import os
    os.environ['AUTO_GIT_COMMIT'] = 'false'
```

### 수동 백업 강제 실행
```python
# 즉시 백업
git_commit_smart("긴급 백업")
```

### 충돌 해결
```python
# 1. 상태 확인
git_status()

# 2. 충돌 파일 수정
edit_block(...)

# 3. 해결 후 커밋
git_commit_smart("충돌 해결")
```

## 모범 사례

### 1. 의미 있는 커밋
- 작업 단위로 커밋
- 명확한 메시지 작성
- Task ID 포함

### 2. 브랜치 전략
- `main`: 안정 버전
- `task/*`: 작업별 브랜치
- `backup/*`: 자동 백업 브랜치

### 3. 정기적 푸시
- 하루 최소 1회 원격 푸시
- 중요 작업 완료 시 즉시 푸시

### 4. Wisdom 활용
- 롤백 패턴 학습
- 안정 커밋 추적
- 실수 방지

## 고급 기능

### 커스텀 훅
```python
# 커밋 전 테스트 실행
execute_code:
    git_manager = get_git_manager()
    # 커스텀 검증 로직
```

### 통계 및 분석
```python
# Git 활동 통계
wisdom_stats()  # Git 커밋/롤백 포함
```

---

*최종 업데이트: 2025-06-26*
