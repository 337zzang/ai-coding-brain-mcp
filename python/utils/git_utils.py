"""
Git 작업을 위한 유틸리티 함수들
"""
import subprocess
from typing import Dict, Any, Optional
import os
from datetime import datetime

def git_commit_with_id(message: str, project_path: str = ".") -> Dict[str, Any]:
    """Git 커밋을 수행하고 상세 정보 반환

    Args:
        message: 커밋 메시지
        project_path: 프로젝트 경로

    Returns:
        성공 시: {
            'success': True,
            'commit_id': 'abc123...',
            'author': 'name',
            'email': 'user@example.com',
            'timestamp': '1234567890',
            'message': 'commit message',
            'files_changed': 5,
            'branch': 'master'
        }
        실패 시: {'success': False, 'error': 'error message'}
    """
    try:
        # 1. 현재 브랜치 확인
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=project_path,
            capture_output=True,
            text=True
        )
        current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"

        # 2. 변경사항 확인
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

        # 3. 스테이징
        # korea 디렉토리 등 서브모듈 제외
        if os.path.exists(os.path.join(project_path, "korea/.git")) or os.path.exists(os.path.join(project_path, "mexico/.git")):
            # 서브모듈 제외하고 추가
            exclude_patterns = []
            if os.path.exists(os.path.join(project_path, "korea/.git")):
                exclude_patterns.append(":(exclude)korea")
            if os.path.exists(os.path.join(project_path, "mexico/.git")):
                exclude_patterns.append(":(exclude)mexico")
            
            add_result = subprocess.run(
                ["git", "add", "--all"] + exclude_patterns,
                cwd=project_path,
                capture_output=True,
                text=True
            )
        else:
            add_result = subprocess.run(
                ["git", "add", "."],
                cwd=project_path,
                capture_output=True,
                text=True
            )

        if add_result.returncode != 0:
            return {
                'success': False,
                'error': f'Failed to stage changes: {add_result.stderr}'
            }

        # 4. 커밋
        commit_result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=project_path,
            capture_output=True,
            text=True
        )

        if commit_result.returncode == 0:
            # 5. 커밋 ID 획득
            commit_id = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=project_path
            ).strip().decode('utf-8')

            # 6. 커밋 정보 획득
            commit_info = subprocess.check_output(
                ["git", "log", "-1", "--pretty=format:%H|%an|%ae|%at|%s", commit_id],
                cwd=project_path
            ).decode('utf-8')

            # 7. 변경된 파일 수 확인
            files_changed_output = subprocess.check_output(
                ["git", "show", "--stat", "--format=", commit_id],
                cwd=project_path
            ).decode('utf-8')

            # 파일 수 파싱 (예: "5 files changed")
            files_changed = 0
            for line in files_changed_output.split('\n'):
                if 'files changed' in line or 'file changed' in line:
                    parts = line.strip().split()
                    if parts and parts[0].isdigit():
                        files_changed = int(parts[0])
                    break

            # 파싱
            header = commit_info.split('|')

            return {
                'success': True,
                'commit_id': commit_id,
                'commit_id_short': commit_id[:8],
                'author': header[1] if len(header) > 1 else 'unknown',
                'email': header[2] if len(header) > 2 else 'unknown',
                'timestamp': header[3] if len(header) > 3 else str(int(datetime.now().timestamp())),
                'message': message,
                'files_changed': files_changed,
                'branch': current_branch
            }
        else:
            return {
                'success': False,
                'error': commit_result.stderr
            }
    except Exception as e:
        return {
            'success': False,
            'error': f'Exception during git operation: {str(e)}'
        }

def git_push(branch: Optional[str] = None, project_path: str = ".") -> Dict[str, Any]:
    """Git push 수행

    Args:
        branch: 푸시할 브랜치 (None이면 현재 브랜치)
        project_path: 프로젝트 경로

    Returns:
        {'success': bool, 'message': str, 'error': str (if failed)}
    """
    try:
        cmd = ["git", "push"]
        if branch:
            cmd.extend(["origin", branch])

        result = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return {
                'success': True,
                'message': 'Push successful'
            }
        else:
            return {
                'success': False,
                'error': result.stderr
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_git_status_info(project_path: str = ".") -> Dict[str, Any]:
    """Git 상태 정보 수집

    Returns:
        {
            'branch': 'master',
            'modified': ['file1.py', 'file2.py'],
            'untracked': ['new_file.txt'],
            'staged': ['staged_file.py'],
            'last_commit': 'abc1234 커밋 메시지',
            'clean': False,
            'ahead': 0,  # 원격보다 앞선 커밋 수
            'behind': 0  # 원격보다 뒤쳐진 커밋 수
        }
    """
    try:
        # 1. 브랜치 정보
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=project_path,
            capture_output=True,
            text=True
        )
        branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"

        # 2. 변경 사항 분석
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_path,
            capture_output=True,
            text=True
        )

        modified = []
        untracked = []
        staged = []

        if status_result.returncode == 0:
            for line in status_result.stdout.splitlines():
                if not line.strip():
                    continue
                status_code = line[:2]
                filename = line[3:]

                # 서브모듈 제외
                if filename.startswith('korea/') or filename.startswith('mexico/'):
                    continue

                if status_code == " M":  # Modified
                    modified.append(filename)
                elif status_code == "??":  # Untracked
                    untracked.append(filename)
                elif status_code[0] in "MADRC":  # Staged
                    staged.append(filename)
                elif status_code == "MM":  # Staged and modified
                    staged.append(filename)
                    modified.append(filename)

        # 3. 마지막 커밋 정보
        last_commit = ""
        commit_result = subprocess.run(
            ["git", "log", "-1", "--format=%h %s"],
            cwd=project_path,
            capture_output=True,
            text=True
        )
        if commit_result.returncode == 0:
            last_commit = commit_result.stdout.strip()

        # 4. 원격 저장소와의 차이 확인
        ahead = behind = 0
        tracking_result = subprocess.run(
            ["git", "rev-list", "--left-right", "--count", f"{branch}...origin/{branch}"],
            cwd=project_path,
            capture_output=True,
            text=True
        )
        if tracking_result.returncode == 0 and tracking_result.stdout.strip():
            parts = tracking_result.stdout.strip().split()
            if len(parts) >= 2:
                ahead = int(parts[0])
                behind = int(parts[1])

        return {
            'success': True,
            'branch': branch,
            'modified': modified,
            'untracked': untracked,
            'staged': staged,
            'last_commit': last_commit,
            'clean': len(modified) == 0 and len(untracked) == 0 and len(staged) == 0,
            'ahead': ahead,
            'behind': behind
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'branch': 'unknown',
            'modified': [],
            'untracked': [],
            'staged': [],
            'clean': True
        }
