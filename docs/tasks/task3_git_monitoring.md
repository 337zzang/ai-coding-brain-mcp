# 🔧 Task 3: Git 상태 모니터링 통합

## 작업 개요
- **목표**: /status 명령어에 Git 상태 정보 통합
- **범위**: WorkflowManager.get_status() 및 상태 표시 개선
- **우선순위**: MEDIUM
- **예상 시간**: 3시간

## 현재 문제점
1. /status에 Git 정보가 전혀 표시되지 않음
2. 변경된 파일, untracked 파일 정보 없음
3. 현재 브랜치 정보 없음
4. 커밋되지 않은 작업 경고 없음

## 구현 계획

### 1. Git 상태 정보 수집 함수
```python
def get_git_status_info() -> Dict[str, Any]:
    '''Git 상태 정보 수집'''
    try:
        # 브랜치 정보
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            text=True
        ).strip()

        # 변경 사항
        status_output = subprocess.check_output(
            ["git", "status", "--porcelain"],
            text=True
        )

        modified = []
        untracked = []
        staged = []

        for line in status_output.splitlines():
            if line.startswith(" M"):
                modified.append(line[3:])
            elif line.startswith("??"):
                untracked.append(line[3:])
            elif line.startswith("M ") or line.startswith("A "):
                staged.append(line[3:])

        # 마지막 커밋 정보
        last_commit = subprocess.check_output(
            ["git", "log", "-1", "--format=%h %s"],
            text=True
        ).strip()

        return {
            'branch': branch,
            'modified': modified,
            'untracked': untracked,
            'staged': staged,
            'last_commit': last_commit,
            'clean': len(modified) == 0 and len(untracked) == 0
        }
    except Exception as e:
        return {'error': str(e)}
```

### 2. get_status 메서드 개선
- 기존 워크플로우 상태에 Git 정보 추가
- 포맷팅 개선으로 가독성 향상

### 3. 표시 형식 개선
```
📅 계획: 워크플로우 시스템 전면 개선 (20%)
📝 안정성, 추적성, 사용성 향상을 위한 장기 개선 프로젝트

🔄 Git 상태: master | 3 files modified, 2 untracked
   마지막 커밋: ef3e20a feat(workflow): Git 커밋 ID 추적

📊 작업 목록:
  ✅ 원자적 파일 저장 시스템 구현
  ✅ Git 커밋 ID 추적 시스템 구축  
  🔄 Git 상태 모니터링 통합
  ⬜ WorkflowManager 싱글톤 문제 해결
  ...
```

## 구현 단계
1. git_utils.py에 get_git_status_info() 추가
2. WorkflowManager.get_status() 수정
3. 상태 표시 포맷 개선
4. 테스트 및 검증

## 기대 효과
- Git 상태 한눈에 파악
- 커밋 누락 방지
- 작업 흐름 개선
