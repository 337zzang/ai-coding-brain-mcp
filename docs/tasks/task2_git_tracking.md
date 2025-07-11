# 🔧 Task 2: Git 커밋 ID 추적 시스템 구축

## 작업 개요
- **목표**: 작업 완료 시 Git 커밋 정보를 Task 메타데이터에 자동 저장
- **범위**: WorkflowCommands.complete_current_task 메서드 개선
- **우선순위**: HIGH
- **예상 시간**: 6시간

## 현재 문제점
1. `os.system()` 사용으로 커밋 ID 캡처 불가
2. 커밋 성공/실패만 확인 가능
3. Task와 Git 커밋 간 연결 정보 없음
4. 커밋 메시지에 Task ID 미포함

## 구현 계획

### 1. Git 헬퍼 함수 생성
```python
import subprocess
from typing import Dict, Optional

def git_commit_with_id(message: str, project_path: str = ".") -> Dict[str, Any]:
    '''Git 커밋을 수행하고 상세 정보 반환'''
    try:
        # 1. 변경사항 확인
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_path,
            capture_output=True,
            text=True
        )

        if not status_result.stdout.strip():
            return {
                'success': False,
                'error': 'No changes to commit'
            }

        # 2. 스테이징
        add_result = subprocess.run(
            ["git", "add", "."],
            cwd=project_path,
            capture_output=True,
            text=True
        )

        # 3. 커밋
        commit_result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=project_path,
            capture_output=True,
            text=True
        )

        if commit_result.returncode == 0:
            # 4. 커밋 ID 획득
            commit_id = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=project_path
            ).strip().decode('utf-8')

            # 5. 커밋 정보 획득
            commit_info = subprocess.check_output(
                ["git", "show", "--stat", "--format=%H|%an|%ae|%at|%s", commit_id],
                cwd=project_path
            ).decode('utf-8')

            # 파싱
            info_lines = commit_info.split('\n')
            header = info_lines[0].split('|')

            return {
                'success': True,
                'commit_id': commit_id,
                'author': header[1],
                'email': header[2],
                'timestamp': header[3],
                'message': message,
                'files_changed': len([l for l in info_lines if 'changed' in l])
            }
        else:
            return {
                'success': False,
                'error': commit_result.stderr
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
```

### 2. Task 메타데이터 구조 개선
```python
# Task.result에 Git 정보 추가
task.result = {
    'summary': summary,
    'details': details,
    'outputs': outputs,
    'git_info': {
        'commit_id': 'abc123...',
        'commit_url': 'https://github.com/.../commit/abc123',
        'author': 'user@example.com',
        'timestamp': '2025-01-07T12:00:00',
        'files_changed': 5,
        'branch': 'master'
    }
}
```

### 3. 커밋 메시지 형식 개선
```
task(task_id): 작업 제목

- 요약: 작업 요약 내용
- Phase: 1
- Priority: HIGH

자세한 내용...
```

## 구현 단계
1. Git 헬퍼 함수 작성 (git_utils.py)
2. complete_current_task 메서드 수정
3. Task 모델에 Git 정보 필드 추가
4. 테스트 코드 작성
5. 기존 작업 마이그레이션 고려

## 테스트 시나리오
1. 정상 커밋 및 ID 캡처
2. 변경사항 없을 때 처리
3. 커밋 실패 시 에러 처리
4. 메타데이터 저장 검증
