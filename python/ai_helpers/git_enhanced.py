"""
Git 관련 기능 통합 모듈
ai-coding-brain-mcp v47용으로 재작성
"""

import subprocess
import os
from pathlib import Path
from .helper_result import HelperResult

# Git 사용 가능 여부 확인
GIT_EXECUTABLE = None

# Windows에서 Git 경로 찾기
if os.name == 'nt':  # Windows
    possible_paths = [
        r"C:\Program Files\Git\bin\git.exe",
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files (x86)\Git\bin\git.exe",
        r"C:\Program Files (x86)\Git\cmd\git.exe",
    ]
    for path in possible_paths:
        if os.path.exists(path):
            GIT_EXECUTABLE = path
            break
    
    # PATH에서 찾기
    if not GIT_EXECUTABLE:
        try:
            result = subprocess.run(['where', 'git'], capture_output=True, text=True, shell=True)
            if result.returncode == 0 and result.stdout.strip():
                GIT_EXECUTABLE = result.stdout.strip().split('\n')[0]
        except:
            pass

# Git 사용 가능 여부 확인
try:
    cmd = [GIT_EXECUTABLE or 'git', '--version']
    subprocess.run(cmd, capture_output=True, timeout=5)
    GIT_AVAILABLE = True
except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
    GIT_AVAILABLE = False



class GitEnhancer:
    """Git 명령어 실행을 위한 헬퍼 클래스"""

    def __init__(self):
        self.timeout = 30

    def _run_git_command(self, cmd, cwd=None):
        """Git 명령어 실행"""
        try:
            git_cmd = GIT_EXECUTABLE or 'git'
            full_cmd = [git_cmd] + cmd
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=cwd
            )

            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': '',
                'error': f'Git 명령 시간 초과 ({self.timeout}초)',
                'returncode': -1
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'returncode': -1
            }


# GitEnhancer 인스턴스 생성
_git_enhancer = GitEnhancer()


def git_status():
    """Git 상태 조회"""
    result = _git_enhancer._run_git_command(['status', '--porcelain'])

    if result['success']:
        lines = result['output'].strip().split('\n') if result['output'].strip() else []
        modified = [line[3:] for line in lines if line.startswith(' M')]
        added = [line[3:] for line in lines if line.startswith('A ')]
        untracked = [line[3:] for line in lines if line.startswith('??')]

        return HelperResult(True, {
            'branch': git_get_current_branch().data if git_get_current_branch().ok else 'unknown',
            'modified': modified,
            'added': added,
            'untracked': untracked,
            'untracked_count': len(untracked),
            'clean': len(lines) == 0
        })
    else:
        return HelperResult(False, f"Git status 실패: {result['error']}")


def git_add(files='.'):
    """Git add 실행"""
    files_list = [files] if isinstance(files, str) else files
    result = _git_enhancer._run_git_command(['add'] + files_list)

    if result['success']:
        return HelperResult(True, {
            'files': files_list,
            'output': result['output']
        })
    else:
        return HelperResult(False, f"Git add 실패: {result['error']}")


def git_commit(message, files=None):
    """Git commit 실행"""
    cmd = ['commit', '-m', message]
    if files:
        files_list = [files] if isinstance(files, str) else files
        cmd.extend(files_list)

    result = _git_enhancer._run_git_command(cmd)

    if result['success']:
        return HelperResult(True, {
            'message': message,
            'files': files,
            'output': result['output']
        })
    else:
        return HelperResult(False, f"Git commit 실패: {result['error']}")


def git_push(remote='origin', branch=None):
    """Git push 실행"""
    cmd = ['push']

    if branch:
        cmd.extend([remote, branch])
    else:
        # 현재 브랜치 push
        current_branch = git_get_current_branch()
        if current_branch.ok:
            cmd.extend([remote, current_branch.data])
        else:
            cmd.append(remote)

    result = _git_enhancer._run_git_command(cmd)

    if result['success']:
        return HelperResult(True, {
            'remote': remote,
            'branch': branch,
            'output': result['output']
        })
    else:
        return HelperResult(False, f"Git push 실패: {result['error']}")


def git_pull(remote='origin', branch=None):
    """Git pull 실행"""
    cmd = ['pull', remote]
    if branch:
        cmd.append(branch)

    result = _git_enhancer._run_git_command(cmd)

    if result['success']:
        return HelperResult(True, {
            'remote': remote,
            'branch': branch,
            'output': result['output']
        })
    else:
        return HelperResult(False, f"Git pull 실패: {result['error']}")


def git_branch(branch_name=None, action='list'):
    """Git branch 관리"""
    if action == 'list':
        result = _git_enhancer._run_git_command(['branch', '-a'])
        if result['success']:
            branches = [line.strip().replace('* ', '') for line in result['output'].split('\n') if line.strip()]
            current = next((b.replace('* ', '') for b in result['output'].split('\n') if b.startswith('*')), None)
            return HelperResult(True, {
                'branches': branches,
                'current': current,
                'action': action
            })
    elif action == 'create' and branch_name:
        result = _git_enhancer._run_git_command(['checkout', '-b', branch_name])
        if result['success']:
            return HelperResult(True, {
                'branch_name': branch_name,
                'action': action,
                'output': result['output']
            })

    return HelperResult(False, f"Git branch {action} 실패")


def git_log(count=10):
    """Git log 조회"""
    result = _git_enhancer._run_git_command(['log', f'--max-count={count}', '--oneline'])

    if result['success']:
        commits = []
        for line in result['output'].strip().split('\n'):
            if line.strip():
                parts = line.split(' ', 1)
                if len(parts) >= 2:
                    commits.append({
                        'hash': parts[0],
                        'message': parts[1]
                    })

        return HelperResult(True, {
            'commits': commits,
            'count': len(commits)
        })
    else:
        return HelperResult(False, f"Git log 실패: {result['error']}")


def git_diff(file_path=None, staged=False):
    """Git diff 조회"""
    cmd = ['diff']
    if staged:
        cmd.append('--cached')
    if file_path:
        cmd.append(file_path)

    result = _git_enhancer._run_git_command(cmd)

    if result['success']:
        return HelperResult(True, {
            'diff': result['output'],
            'has_changes': bool(result['output'].strip()),
            'staged': staged,
            'file_path': file_path
        })
    else:
        return HelperResult(False, f"Git diff 실패: {result['error']}")


def git_stash(message=None):
    """Git stash 생성"""
    cmd = ['stash', 'push']
    if message:
        cmd.extend(['-m', message])

    result = _git_enhancer._run_git_command(cmd)

    if result['success']:
        return HelperResult(True, {
            'message': message,
            'output': result['output']
        })
    else:
        return HelperResult(False, f"Git stash 실패: {result['error']}")


def git_stash_pop(index=0):
    """Git stash pop 실행"""
    cmd = ['stash', 'pop']
    if index > 0:
        cmd.append(f'stash@{{{index}}}')

    result = _git_enhancer._run_git_command(cmd)

    if result['success']:
        return HelperResult(True, {
            'index': index,
            'output': result['output']
        })
    else:
        return HelperResult(False, f"Git stash pop 실패: {result['error']}")


def git_commit_smart():
    """스마트 커밋 (자동 메시지 생성)"""
    # 변경사항 확인
    status = git_status()
    if not status.ok:
        return HelperResult(False, "Git status 확인 실패")

    # 자동 메시지 생성
    data = status.data
    if data['modified']:
        message = f"Update: {', '.join(data['modified'][:3])}"
        if len(data['modified']) > 3:
            message += f" and {len(data['modified']) - 3} more files"
    elif data['added']:
        message = f"Add: {', '.join(data['added'][:3])}"
    elif data['untracked']:
        message = f"Add new files: {len(data['untracked'])} files"
    else:
        return HelperResult(False, "변경사항이 없습니다")

    return git_commit(message)


def git_branch_smart(branch_name):
    """스마트 브랜치 생성 및 체크아웃"""
    return git_branch(branch_name, 'create')


def is_git_repository():
    """Git 저장소 여부 확인"""
    result = _git_enhancer._run_git_command(['rev-parse', '--git-dir'])
    return HelperResult(True, result['success'])


def git_init(directory=None):
    """Git 저장소 초기화"""
    cmd = ['init']
    if directory:
        cmd.append(directory)

    result = _git_enhancer._run_git_command(cmd)

    if result['success']:
        return HelperResult(True, {
            'directory': directory or os.getcwd(),
            'output': result['output']
        })
    else:
        return HelperResult(False, f"Git init 실패: {result['error']}")


def git_checkout(branch_or_file):
    """Git checkout 실행"""
    result = _git_enhancer._run_git_command(['checkout', branch_or_file])

    if result['success']:
        return HelperResult(True, {
            'target': branch_or_file,
            'output': result['output']
        })
    else:
        return HelperResult(False, f"Git checkout 실패: {result['error']}")


def git_get_current_branch():
    """현재 브랜치 이름 조회"""
    result = _git_enhancer._run_git_command(['branch', '--show-current'])

    if result['success']:
        branch = result['output'].strip()
        return HelperResult(True, branch)
    else:
        return HelperResult(False, f"브랜치 조회 실패: {result['error']}")


def git_get_remote_url(remote='origin'):
    """리모트 URL 조회"""
    result = _git_enhancer._run_git_command(['remote', 'get-url', remote])

    if result['success']:
        url = result['output'].strip()
        return HelperResult(True, url)
    else:
        return HelperResult(False, f"리모트 URL 조회 실패: {result['error']}")


# 레거시 호환성을 위한 추가 함수들
def get_git_operations():
    """사용 가능한 Git 작업 목록 반환"""
    operations = [
        'git_status', 'git_add', 'git_commit', 'git_push', 'git_pull',
        'git_branch', 'git_log', 'git_diff', 'git_stash', 'git_stash_pop',
        'git_commit_smart', 'git_branch_smart', 'is_git_repository', 'git_init',
        'git_checkout', 'git_get_current_branch', 'git_get_remote_url'
    ]

    return HelperResult(True, operations)


def get_git_metrics():
    """Git 저장소 메트릭 조회"""
    if not is_git_repository().data:
        return HelperResult(False, "Git 저장소가 아닙니다")

    status = git_status()
    log = git_log(1)

    metrics = {
        'is_repo': True,
        'branch': git_get_current_branch().data if git_get_current_branch().ok else 'unknown',
        'modified_files': len(status.data.get('modified', [])) if status.ok else 0,
        'untracked_files': len(status.data.get('untracked', [])) if status.ok else 0,
        'last_commit': log.data['commits'][0] if log.ok and log.data['commits'] else None
    }

    return HelperResult(True, metrics)
