"""
Git 작업 - 프로토콜 추적 포함
"""
import subprocess
import os
from typing import List, Dict, Any, Optional
from .core import track_execution

def run_git_command(args: List[str], cwd: str = ".") -> Dict[str, Any]:
    """Git 명령 실행 헬퍼"""
    try:
        result = subprocess.run(
            ['git'] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        return {
            'success': result.returncode == 0,
            'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip(),
            'returncode': result.returncode
        }
    except Exception as e:
        return {
            'success': False,
            'stdout': '',
            'stderr': str(e),
            'returncode': -1
        }

@track_execution
def git_status(cwd: str = ".") -> Dict[str, Any]:
    """Git 상태 확인"""
    result = run_git_command(['status', '--porcelain'], cwd)

    if not result['success']:
        return result

    # 상태 파싱
    modified = []
    untracked = []
    staged = []

    for line in result['stdout'].split('\n'):
        if not line:
            continue

        status = line[:2]
        filepath = line[3:]

        if status == '??':
            untracked.append(filepath)
        elif status[0] in ['M', 'A', 'D', 'R']:
            staged.append(filepath)
        elif status[1] in ['M', 'D']:
            modified.append(filepath)

    return {
        'success': True,
        'modified': modified,
        'untracked': untracked,
        'staged': staged,
        'clean': not (modified or untracked or staged)
    }

@track_execution
def git_add(files: List[str] = None, all: bool = False, cwd: str = ".") -> Dict[str, Any]:
    """파일을 스테이징"""
    if all:
        args = ['add', '-A']
    elif files:
        args = ['add'] + files
    else:
        return {
            'success': False,
            'error': 'No files specified'
        }

    return run_git_command(args, cwd)

@track_execution
def git_commit(message: str, cwd: str = ".") -> Dict[str, Any]:
    """커밋 생성"""
    if not message:
        return {
            'success': False,
            'error': 'Commit message is required'
        }

    result = run_git_command(['commit', '-m', message], cwd)

    if result['success']:
        # 커밋 해시 추출
        commit_info = run_git_command(['rev-parse', 'HEAD'], cwd)
        if commit_info['success']:
            result['commit_hash'] = commit_info['stdout'][:7]

    return result

@track_execution
def git_push(remote: str = 'origin', branch: str = None, cwd: str = ".") -> Dict[str, Any]:
    """원격 저장소에 푸시"""
    if not branch:
        # 현재 브랜치 가져오기
        branch_result = run_git_command(['branch', '--show-current'], cwd)
        if not branch_result['success']:
            return branch_result
        branch = branch_result['stdout']

    return run_git_command(['push', remote, branch], cwd)

@track_execution
def git_pull(remote: str = 'origin', branch: str = None, cwd: str = ".") -> Dict[str, Any]:
    """원격 저장소에서 풀"""
    if not branch:
        # 현재 브랜치 가져오기
        branch_result = run_git_command(['branch', '--show-current'], cwd)
        if not branch_result['success']:
            return branch_result
        branch = branch_result['stdout']

    return run_git_command(['pull', remote, branch], cwd)

@track_execution
def git_branch(cwd: str = ".") -> Dict[str, Any]:
    """브랜치 목록 조회"""
    result = run_git_command(['branch', '-a'], cwd)

    if not result['success']:
        return result

    branches = []
    current_branch = None

    for line in result['stdout'].split('\n'):
        if not line:
            continue

        if line.startswith('*'):
            current_branch = line[2:].strip()
            branches.append(current_branch)
        else:
            branches.append(line.strip())

    return {
        'success': True,
        'branches': branches,
        'current': current_branch
    }

# 사용 가능한 함수 목록
__all__ = [
    'git_status', 'git_add', 'git_commit', 
    'git_push', 'git_pull', 'git_branch'
]
