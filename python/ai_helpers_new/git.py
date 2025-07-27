"""Git 작업 관련 함수들"""
import subprocess
import os
import platform
from typing import Dict, Any, List, Optional
from .util import ok, err

def find_git_executable() -> Optional[str]:
    """Git 실행 파일 찾기"""
    # Windows에서 직접 경로 확인
    if platform.system() == 'Windows':
        common_paths = [
            r"C:\Program Files\Git\bin\git.exe",
            r"C:\Program Files (x86)\Git\bin\git.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\Git\bin\git.exe")
        ]

        for path in common_paths:
            if os.path.exists(path):
                return path

    # where 명령 시도
    try:
        result = subprocess.run(['where', 'git'], 
                              capture_output=True, 
                              text=True)
        if result.returncode == 0:
            return result.stdout.strip().split('\n')[0]
    except:
        pass

    # 기본값
    return 'git'

def run_git_command(args: List[str], cwd: Optional[str] = None) -> Dict[str, Any]:
    """Git 명령 실행"""
    try:
        git_exe = find_git_executable()
        cmd = [git_exe] + args

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=False,  # bytes로 받기
            cwd=cwd or os.getcwd()
        )

        # 출력 디코딩
        if result.returncode == 0:
            try:
                stdout = result.stdout.decode('utf-8')
            except UnicodeDecodeError:
                # Windows 한글 환경 대응
                stdout = result.stdout.decode('cp949', errors='replace')

            try:
                stderr = result.stderr.decode('utf-8') if result.stderr else ''
            except UnicodeDecodeError:
                stderr = result.stderr.decode('cp949', errors='replace') if result.stderr else ''

            return ok(stdout, stderr=stderr)
        else:
            try:
                stderr = result.stderr.decode('utf-8')
            except UnicodeDecodeError:
                stderr = result.stderr.decode('cp949', errors='replace')
            return err(f"Git command failed: {stderr}")

        if result.returncode == 0:
            return ok(result.stdout, stderr=result.stderr)
        else:
            return err(f"Git command failed: {result.stderr}")

    except Exception as e:
        return err(f"Git command error: {str(e)}")

def git_status(include_log: bool = False) -> Dict[str, Any]:
    """Git 상태 확인 (개선됨 - 브랜치 정보 포함)

    Args:
        include_log: 최근 커밋 정보 포함 여부

    Returns:
        {
            'ok': True,
            'data': {
                'files': [...],      # 변경된 파일 목록
                'count': 0,          # 변경된 파일 수
                'branch': 'master',  # 현재 브랜치 (신규)
                'clean': True,       # 깨끗한 상태 여부 (신규)
                'latest_commit': {}  # 최근 커밋 (include_log=True인 경우)
            }
        }
    """
    # 파일 상태 (기존 로직)
    result = run_git_command(['status', '--porcelain'])
    if not result['ok']:
        return result

    files = result['data'].strip().split('\n') if result['data'].strip() else []

    # 브랜치 정보 추가
    branch_info = git_current_branch()
    branch = branch_info['data'] if branch_info['ok'] else 'unknown'

    # 결과 구성
    data = {
        'files': files,
        'count': len(files),
        'branch': branch,         # 신규 추가
        'clean': len(files) == 0  # 신규 추가
    }

    # 최근 커밋 정보 (옵션)
    if include_log:
        log_info = git_log(limit=1)
        if log_info['ok'] and log_info['data']:
            latest = log_info['data'][0]
            data['latest_commit'] = {
                'hash': latest.get('hash', '')[:7],
                'message': latest.get('message', ''),
                'author': latest.get('author', ''),
                'date': latest.get('date', '')
            }

    return ok(data)
def git_add(files: List[str]) -> Dict[str, Any]:
    """파일을 스테이징 영역에 추가"""
    if not files:
        return err("No files specified")

    result = run_git_command(['add'] + files)
    return result

def git_commit(message: str) -> Dict[str, Any]:
    """커밋 생성"""
    if not message:
        return err("Commit message required")

    result = run_git_command(['commit', '-m', message])
    return result

def git_push(remote: str = 'origin', branch: Optional[str] = None) -> Dict[str, Any]:
    """원격 저장소에 푸시"""
    args = ['push', remote]
    if branch:
        args.append(branch)

    result = run_git_command(args)
    return result

def git_pull(remote: str = 'origin', branch: Optional[str] = None) -> Dict[str, Any]:
    """원격 저장소에서 풀"""
    args = ['pull', remote]
    if branch:
        args.append(branch)

    result = run_git_command(args)
    return result

def git_branch(branch_name: Optional[str] = None) -> Dict[str, Any]:
    """브랜치 목록 또는 생성"""
    if branch_name:
        # 브랜치 생성
        result = run_git_command(['checkout', '-b', branch_name])
    else:
        # 브랜치 목록
        result = run_git_command(['branch'])

    return result

def git_current_branch() -> Dict[str, Any]:
    """현재 브랜치 확인"""
    result = run_git_command(['branch', '--show-current'])
    if result['ok']:
        return ok(result['data'].strip())
    return result





# DEPRECATED: git_status() 함수가 이제 모든 기능을 포함합니다.
# 이 함수는 하위 호환성을 위해 유지되지만 git_status()를 사용하세요.
def git_log(limit: int = 10, format: str = "oneline", cwd: str = ".") -> Dict[str, Any]:
    """Git 커밋 히스토리 조회

    Args:
        limit: 조회할 커밋 수
        format: 출력 형식 (oneline, short, medium, full)
        cwd: 작업 디렉토리

    Returns:
        Dict with commits list
    """
    args = ['log', f'--max-count={limit}']

    if format == "oneline":
        args.append('--oneline')
    else:
        args.append(f'--format={format}')

    result = run_git_command(args, cwd)

    if result.get('ok') and result.get('data'):
        commits = []
        for line in result.get('data', '').strip().split('\n'):
            if line:
                if format == "oneline":
                    parts = line.split(' ', 1)
                    if len(parts) == 2:
                        commits.append({
                            'hash': parts[0],
                            'message': parts[1]
                        })
                else:
                    commits.append(line)

        return ok(commits, count=len(commits))

    return err(result['error'] or "Failed to get git log")


def git_diff(file: str = None, staged: bool = False, cwd: str = ".") -> Dict[str, Any]:
    """변경사항 확인

    Args:
        file: 특정 파일만 확인 (None이면 전체)
        staged: 스테이징된 변경사항 확인
        cwd: 작업 디렉토리

    Returns:
        Dict with diff output
    """
    args = ['diff']

    if staged:
        args.append('--staged')

    if file:
        args.append('--')
        args.append(file)

    return run_git_command(args, cwd)
