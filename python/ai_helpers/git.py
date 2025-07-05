"""
Git 헬퍼 함수들 - 크로스 플랫폼 지원
"""
import subprocess
import os
import sys
import json
from typing import Dict, Any, List, Optional, Union
from .helper_result import HelperResult

# Git 실행 파일 찾기 (Windows 호환)
def _find_git_executable() -> Optional[str]:
    """Git 실행 파일 경로 찾기"""
    # 1. 환경 변수에서 찾기
    if sys.platform == "win32":
        # Windows에서 일반적인 Git 설치 경로들
        possible_paths = [
            r"C:\Program Files\Git\bin\git.exe",
            r"C:\Program Files (x86)\Git\bin\git.exe",
            os.path.expandvars(r"%PROGRAMFILES%\Git\bin\git.exe"),
            os.path.expandvars(r"%PROGRAMFILES(X86)%\Git\bin\git.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Git\bin\git.exe"),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path

    # 2. PATH에서 찾기
    try:
        result = subprocess.run(["where" if sys.platform == "win32" else "which", "git"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip().split('\n')[0]
    except:
        pass

    return None

# Git 실행 가능 여부 확인
GIT_EXECUTABLE = _find_git_executable()
GIT_AVAILABLE = GIT_EXECUTABLE is not None

def _run_git_command(args: List[str], cwd: Optional[str] = None) -> HelperResult:
    """Git 명령 실행 헬퍼"""
    if not GIT_AVAILABLE:
        return HelperResult(
            ok=False, 
            data=None, 
            error="Git이 설치되지 않았거나 PATH에 없습니다"
        )

    try:
        cmd = [GIT_EXECUTABLE] + args
        result = subprocess.run(
            cmd,
            cwd=cwd or os.getcwd(),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'  # 인코딩 오류 방지
        )

        if result.returncode == 0:
            return HelperResult(
                ok=True,
                data={
                    'stdout': result.stdout.strip(),
                    'stderr': result.stderr.strip(),
                    'command': ' '.join(args)
                },
                error=None
            )
        else:
            return HelperResult(
                ok=False,
                data={
                    'stdout': result.stdout.strip(),
                    'stderr': result.stderr.strip(),
                    'command': ' '.join(args),
                    'returncode': result.returncode
                },
                error=result.stderr.strip() or f"Git command failed with code {result.returncode}"
            )
    except Exception as e:
        return HelperResult(
            ok=False,
            data=None,
            error=f"Git 명령 실행 중 오류: {str(e)}"
        )

def git_status() -> HelperResult:
    """Git 저장소 상태 확인"""
    result = _run_git_command(['status', '--porcelain', '-b'])

    if not result.ok:
        return result

    lines = result.data['stdout'].split('\n')
    branch_line = lines[0] if lines else ""

    # 브랜치 파싱
    branch = "unknown"
    if branch_line.startswith("## "):
        branch_info = branch_line[3:]
        if "..." in branch_info:
            branch = branch_info.split("...")[0]
        else:
            branch = branch_info

    # 변경된 파일 파싱
    modified = []
    untracked = []
    staged = []

    for line in lines[1:]:
        if not line:
            continue

        status = line[:2]
        filename = line[3:]

        if status == "??":
            untracked.append(filename)
        elif "M" in status:
            modified.append(filename)
        elif "A" in status[0]:  # 첫 번째 문자가 A면 staged
            staged.append(filename)

    return HelperResult(
        ok=True,
        data={
            'branch': branch,
            'modified': modified,
            'untracked': untracked,
            'staged': staged,
            'clean': len(modified) == 0 and len(untracked) == 0 and len(staged) == 0
        },
        error=None
    )

def git_add(files: Union[str, List[str]] = ".") -> HelperResult:
    """파일을 스테이징 영역에 추가"""
    if isinstance(files, str):
        files = [files]

    return _run_git_command(['add'] + files)

def git_commit(message: str, files: Optional[List[str]] = None) -> HelperResult:
    """커밋 생성"""
    if not message:
        return HelperResult(ok=False, data=None, error="커밋 메시지가 필요합니다")

    # 파일이 지정되면 먼저 add
    if files:
        add_result = git_add(files)
        if not add_result.ok:
            return add_result

    return _run_git_command(['commit', '-m', message])

def git_push(remote: str = "origin", branch: Optional[str] = None) -> HelperResult:
    """원격 저장소에 푸시"""
    args = ['push', remote]
    if branch:
        args.append(branch)

    return _run_git_command(args)

def git_pull(remote: str = "origin", branch: Optional[str] = None) -> HelperResult:
    """원격 저장소에서 풀"""
    args = ['pull', remote]
    if branch:
        args.append(branch)

    return _run_git_command(args)

def git_branch(name: Optional[str] = None, checkout: bool = False) -> HelperResult:
    """브랜치 생성 또는 목록 조회"""
    if name:
        if checkout:
            return _run_git_command(['checkout', '-b', name])
        else:
            return _run_git_command(['branch', name])
    else:
        # 브랜치 목록 조회
        result = _run_git_command(['branch', '-a'])
        if result.ok:
            branches = [b.strip() for b in result.data['stdout'].split('\n') if b.strip()]
            current = next((b[2:] for b in branches if b.startswith('* ')), None)
            result.data['branches'] = [b.lstrip('* ') for b in branches]
            result.data['current'] = current
        return result

def git_log(limit: int = 10, oneline: bool = True) -> HelperResult:
    """커밋 로그 조회"""
    args = ['log', f'-{limit}']
    if oneline:
        args.append('--oneline')
    else:
        args.append('--pretty=format:%H|%an|%ae|%ad|%s')

    result = _run_git_command(args)

    if result.ok and not oneline:
        # 파싱하여 구조화된 데이터로 변환
        commits = []
        for line in result.data['stdout'].split('\n'):
            if line:
                parts = line.split('|')
                if len(parts) >= 5:
                    commits.append({
                        'hash': parts[0],
                        'author': parts[1],
                        'email': parts[2],
                        'date': parts[3],
                        'message': parts[4]
                    })
        result.data['commits'] = commits

    return result

def git_diff(staged: bool = False) -> HelperResult:
    """변경사항 확인"""
    args = ['diff']
    if staged:
        args.append('--staged')

    return _run_git_command(args)

def git_stash(message: Optional[str] = None) -> HelperResult:
    """변경사항 임시 저장"""
    args = ['stash', 'push']
    if message:
        args.extend(['-m', message])

    return _run_git_command(args)

def git_stash_pop() -> HelperResult:
    """임시 저장한 변경사항 복원"""
    return _run_git_command(['stash', 'pop'])

# 스마트 함수들 (기존 인터페이스 호환)
def git_commit_smart(message: Optional[str] = None) -> HelperResult:
    """스마트 커밋 - 자동으로 메시지 생성"""
    if not message:
        # 변경사항 확인
        status = git_status()
        if status.ok:
            modified = status.data.get('modified', [])
            if modified:
                message = f"Update {', '.join(modified[:3])}"
                if len(modified) > 3:
                    message += f" and {len(modified) - 3} more files"
            else:
                message = "Update files"

    # 모든 변경사항 add
    add_result = git_add(".")
    if not add_result.ok:
        return add_result

    return git_commit(message)

def git_branch_smart(name: str) -> HelperResult:
    """스마트 브랜치 - 생성하고 체크아웃"""
    return git_branch(name, checkout=True)

# Git 초기화 확인 함수
def is_git_repository() -> bool:
    """현재 디렉토리가 Git 저장소인지 확인"""
    return os.path.exists('.git')

def git_init() -> HelperResult:
    """Git 저장소 초기화"""
    return _run_git_command(['init'])

# Export할 함수들
__all__ = [
    'git_status', 'git_add', 'git_commit', 'git_push', 'git_pull',
    'git_branch', 'git_log', 'git_diff', 'git_stash', 'git_stash_pop',
    'git_commit_smart', 'git_branch_smart', 'is_git_repository', 'git_init',
    'GIT_AVAILABLE'
]
