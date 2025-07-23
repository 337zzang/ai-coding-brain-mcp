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

def git_status() -> Dict[str, Any]:
    """Git 상태 확인"""
    result = run_git_command(['status', '--porcelain', '-b'])
    if not result['ok']:
        return result

    # result['data']는 stdout과 stderr를 포함한 dict
    output = result['data'].get('stdout', '') if isinstance(result['data'], dict) else result['data']
    lines = output.strip().split('\n') if output.strip() else []

    # 브랜치 정보 추출
    branch = None
    changes = []

    for line in lines:
        if line.startswith('## '):
            # 브랜치 정보
            branch_info = line[3:]
            if '...' in branch_info:
                branch = branch_info.split('...')[0]
            else:
                branch = branch_info
        elif line.strip():
            # 변경된 파일
            changes.append(line)

    return ok({
        'branch': branch,
        'changes': changes,
        'files': changes,  # 호환성을 위해 유지
        'count': len(changes)
    })
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



# git_status 호환성 래퍼
def git_status_string() -> str:
    """
    git_status의 결과를 문자열로 반환 (레거시 호환용)
    """
    result = git_status()
    if result['ok'] and isinstance(result['data'], dict):
        # dict 형태의 data를 문자열로 변환
        data = result['data']
        if 'files' in data:
            # 파일 리스트를 git status 형식의 문자열로 변환
            output_lines = []
            for file in data['files']:
                output_lines.append(file)
            return '\n'.join(output_lines)
        else:
            return str(data)
    elif result['ok']:
        return str(result['data'])
    else:
        return f"Error: {result.get('error', 'Unknown error')}"

# 별칭 추가 (기존 코드 호환성)
git_status_str = git_status_string
