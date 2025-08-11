"""Git 작업 관련 함수들"""
import subprocess
import os
import platform
import shutil  # Phase 2: 크로스플랫폼 Git 탐색
from typing import Dict, Any, List, Optional
from .util import ok, err
from .wrappers import safe_execution, wrap_output


# ============================================================
# Phase 2: Git 전용 예외 클래스
# ============================================================
class GitError(Exception):
    """Git 명령 실행 중 발생하는 일반 오류"""
    pass

class GitTimeoutError(GitError):
    """Git 명령 타임아웃 오류"""
    pass

# ============================================================
# Phase 2: 환경변수 설정 함수
# ============================================================
def get_git_env() -> Dict[str, str]:
    """Git 실행을 위한 표준화된 환경변수 반환"""
    env = os.environ.copy()
    env['GIT_PAGER'] = 'cat'          # 페이징 비활성화
    env['LC_ALL'] = 'C'                # 영어 출력 강제
    env['LANG'] = 'C'
    env['GIT_TERMINAL_PROMPT'] = '0'   # 인증 프롬프트 비활성화
    env['GIT_OPTIONAL_LOCKS'] = '0'    # Git 잠금 최소화
    return env

def find_git_executable() -> Optional[str]:
    """Git 실행 파일 찾기 (Phase 2: 크로스플랫폼 개선)

    Returns:
        Git 실행 파일 경로 또는 None
    """
    # Phase 2: shutil.which()를 사용한 크로스플랫폼 탐색
    git_path = shutil.which('git')

    if git_path:
        return git_path

    # Windows fallback (PATH에 없는 경우)
    if platform.system() == 'Windows':
        common_paths = [
            r"C:\Program Files\Git\bin\git.exe",
            r"C:\Program Files\Git\cmd\git.exe",
            r"C:\Program Files (x86)\Git\bin\git.exe",
            r"C:\Program Files (x86)\Git\cmd\git.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\Git\bin\git.exe")
        ]

        for path in common_paths:
            if os.path.exists(path):
                return path

    # Git을 찾을 수 없음
    return None

def run_git_command(args: List[str], cwd: Optional[str] = None, timeout: int = 30) -> Dict[str, Any]:
    """Git 명령 실행 (Phase 2: 환경변수 적용)

    Args:
        args: Git 명령어 인자 리스트
        cwd: 작업 디렉토리 (None이면 현재 디렉토리)
        timeout: 최대 실행 시간 (초, 기본 30초)

    Returns:
        표준 응답 형식 {'ok': bool, 'data': Any, 'error': str}
    """
    try:
        git_exe = find_git_executable()
        if not git_exe:
            return err("Git executable not found in PATH or common locations")

        cmd = [git_exe] + args

        # Phase 2: 표준화된 환경변수 사용
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,              
            encoding='utf-8',       
            errors='replace',       
            cwd=cwd or os.getcwd(),
            timeout=timeout,
            env=get_git_env()       # ✅ Phase 2: 환경변수 적용
        )

        # 결과 처리
        if result.returncode == 0:
            return ok(result.stdout.strip())
        else:
            stderr = result.stderr.strip() if result.stderr else f"Command failed with code {result.returncode}"
            return err(f"Git command failed: {stderr}")

    except subprocess.TimeoutExpired:
        # Phase 2: 타임아웃 에러 메시지 개선
        return err(f"Git command timed out after {timeout} seconds: {' '.join(args)}")
    except Exception as e:
        return err(f"Git command error: {str(e)}")
@safe_execution
def git_status(cwd: Optional[str] = None, include_log: bool = False) -> Dict[str, Any]:
    """Git 상태 확인 (Phase 3: 구조화된 데이터 반환)

    Args:
        cwd: 작업 디렉토리 (Phase 3: 추가)
        include_log: 최근 커밋 정보 포함 여부

    Returns:
        {
            'ok': True,
            'data': {
                'branch': 'main',
                'files': [
                    {
                        'status': 'M ',      # 전체 상태 코드
                        'path': 'file.py',   # 파일 경로
                        'index': 'M',        # Staged 상태
                        'worktree': ' '      # Working tree 상태
                    }
                ],
                'summary': {
                    'modified': 1,
                    'added': 0,
                    'deleted': 0,
                    'renamed': 0,
                    'untracked': 1,
                    'total': 2
                },
                'clean': False,
                'latest_commit': {...}  # include_log=True일 때
            }
        }
    """
    # 브랜치 정보 가져오기
    branch_result = run_git_command(['branch', '--show-current'], cwd=cwd)
    current_branch = branch_result['data'].strip() if branch_result['ok'] else 'unknown'

    # 파일 상태 가져오기 (porcelain 형식)
    status_result = run_git_command(['status', '--porcelain'], cwd=cwd)

    if not status_result['ok']:
        return status_result

    # Phase 3: 구조화된 파싱
    files = []
    summary = {
        'modified': 0,
        'added': 0,
        'deleted': 0,
        'renamed': 0,
        'untracked': 0,
        'conflicted': 0,
        'total': 0
    }

    # Porcelain 형식 파싱
    # XY filename
    # X = index(staged) 상태, Y = worktree 상태
    for line in status_result['data'].split('\n'):
        if not line.strip():
            continue

        # 상태 코드와 파일 경로 분리
        if len(line) >= 3:
            status_code = line[:2]
            filepath = line[3:].strip()

            # 구조화된 파일 정보
            file_info = {
                'status': status_code,
                'path': filepath,
                'index': status_code[0],      # Staged 상태
                'worktree': status_code[1],   # Working tree 상태
                'type': _get_status_type(status_code)  # 상태 타입
            }
            files.append(file_info)

            # 통계 업데이트
            if 'M' in status_code:
                summary['modified'] += 1
            elif 'A' in status_code:
                summary['added'] += 1
            elif 'D' in status_code:
                summary['deleted'] += 1
            elif 'R' in status_code:
                summary['renamed'] += 1
            elif status_code == '??':
                summary['untracked'] += 1
            elif 'U' in status_code or 'D' in status_code == 'DD':
                summary['conflicted'] += 1

            summary['total'] += 1

    # 최근 커밋 정보 (옵션)
    latest_commit = None
    if include_log:
        log_result = git_log(limit=1, cwd=cwd, format_type='full')
        if log_result['ok'] and log_result['data']:
            latest_commit = log_result['data'][0] if isinstance(log_result['data'], list) else None

    return ok({
        'branch': current_branch,
        'files': files,
        'summary': summary,
        'clean': summary['total'] == 0,
        'latest_commit': latest_commit
    })

def _get_status_type(status_code: str) -> str:
    """상태 코드를 읽기 쉬운 타입으로 변환"""
    if status_code == '??':
        return 'untracked'
    elif 'M' in status_code:
        return 'modified'
    elif 'A' in status_code:
        return 'added'
    elif 'D' in status_code:
        return 'deleted'
    elif 'R' in status_code:
        return 'renamed'
    elif 'U' in status_code:
        return 'conflicted'
    else:
        return 'unknown'

def git_add(files: List[str], cwd: Optional[str] = None) -> Dict[str, Any]:
    """파일을 Git 스테이징 영역에 추가 (Phase 3: cwd 추가)

    Args:
        files: 추가할 파일 목록
        cwd: 작업 디렉토리
    """
    if isinstance(files, str):
        files = [files]

    result = run_git_command(['add'] + files, cwd=cwd)
    return result

@safe_execution
def git_commit(message: str) -> Dict[str, Any]:
    """커밋 생성"""
    if not message:
        return err("Commit message required")

    result = run_git_command(['commit', '-m', message])
    return result

@safe_execution
def git_push(remote: str = 'origin', branch: Optional[str] = None) -> Dict[str, Any]:
    """원격 저장소에 푸시"""
    args = ['push', remote]
    if branch:
        args.append(branch)

    result = run_git_command(args)
    return result

@safe_execution
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





# DEPRECATED: h.git_status() 함수가 이제 모든 기능을 포함합니다.
# 이 함수는 하위 호환성을 위해 유지되지만 h.git_status()를 사용하세요.
@safe_execution
def git_log(limit: int = 10, cwd: Optional[str] = None, format_type: str = 'full') -> Dict[str, Any]:
    """Git 로그 조회 (Phase 3: 구조화된 데이터 반환)

    Args:
        limit: 조회할 커밋 수
        cwd: 작업 디렉토리
        format_type: 'full', 'oneline', 'stats'

    Returns:
        {
            'ok': True,
            'data': [
                {
                    'hash': 'abc123...',           # 전체 해시
                    'short_hash': 'abc123',        # 짧은 해시
                    'author': 'John Doe',          # 작성자 이름
                    'author_email': 'john@ex.com', # 작성자 이메일
                    'date': '2025-01-01T10:00:00', # ISO 8601 날짜
                    'timestamp': 1704088800,       # Unix timestamp
                    'subject': 'Commit title',     # 커밋 제목
                    'body': 'Detailed desc...',    # 커밋 본문
                    'message': 'Full message',     # 전체 메시지
                    'files_changed': 5,            # 변경 파일 수 (stats일 때)
                    'insertions': 10,              # 추가 라인 (stats일 때)
                    'deletions': 3                 # 삭제 라인 (stats일 때)
                }
            ]
        }
    """
    commits = []

    if format_type == 'full':
        # Phase 3: 구조화된 포맷 정의
        # 구분자를 사용하여 안전한 파싱
        delimiter = '|||GITLOG|||'
        end_marker = '|||ENDCOMMIT|||'

        # %H: full hash, %h: short hash
        # %an: author name, %ae: author email
        # %aI: author date ISO 8601, %at: author timestamp
        # %s: subject, %b: body
        pretty_format = f'%H{delimiter}%h{delimiter}%an{delimiter}%ae{delimiter}%aI{delimiter}%at{delimiter}%s{delimiter}%b{end_marker}'

        result = run_git_command([
            'log',
            f'--max-count={limit}',
            f'--pretty=format:{pretty_format}'
        ], cwd=cwd)

        if not result['ok']:
            return result

        # 파싱
        raw_output = result['data']
        if raw_output:
            commit_chunks = raw_output.split(end_marker)

            for chunk in commit_chunks:
                chunk = chunk.strip()
                if not chunk:
                    continue

                parts = chunk.split(delimiter)
                if len(parts) >= 7:
                    commit_info = {
                        'hash': parts[0],
                        'short_hash': parts[1],
                        'author': parts[2],
                        'author_email': parts[3],
                        'date': parts[4],
                        'timestamp': int(parts[5]) if parts[5].isdigit() else 0,
                        'subject': parts[6],
                        'body': parts[7] if len(parts) > 7 else ''
                    }

                    # 전체 메시지 조합
                    commit_info['message'] = commit_info['subject']
                    if commit_info['body']:
                        commit_info['message'] += '\n\n' + commit_info['body']

                    commits.append(commit_info)

    elif format_type == 'oneline':
        result = run_git_command([
            'log',
            f'--max-count={limit}',
            '--oneline'
        ], cwd=cwd)

        if not result['ok']:
            return result

        for line in result['data'].split('\n'):
            if line.strip():
                parts = line.split(' ', 1)
                if len(parts) >= 2:
                    commits.append({
                        'short_hash': parts[0],
                        'subject': parts[1]
                    })

    elif format_type == 'stats':
        # 통계 포함 로그
        result = run_git_command([
            'log',
            f'--max-count={limit}',
            '--stat',
            '--pretty=format:%H|||%h|||%an|||%aI|||%s'
        ], cwd=cwd)

        if not result['ok']:
            return result

        # 통계 파싱 (간단한 버전)
        lines = result['data'].split('\n')
        current_commit = None

        for line in lines:
            if '|||' in line:
                # 새 커밋
                if current_commit:
                    commits.append(current_commit)

                parts = line.split('|||')
                if len(parts) >= 5:
                    current_commit = {
                        'hash': parts[0],
                        'short_hash': parts[1],
                        'author': parts[2],
                        'date': parts[3],
                        'subject': parts[4],
                        'files_changed': 0,
                        'insertions': 0,
                        'deletions': 0
                    }
            elif current_commit and 'files changed' in line:
                # 통계 라인 파싱
                import re
                # "5 files changed, 10 insertions(+), 3 deletions(-)"
                files_match = re.search(r'(\d+) files? changed', line)
                insertions_match = re.search(r'(\d+) insertions?', line)
                deletions_match = re.search(r'(\d+) deletions?', line)

                if files_match:
                    current_commit['files_changed'] = int(files_match.group(1))
                if insertions_match:
                    current_commit['insertions'] = int(insertions_match.group(1))
                if deletions_match:
                    current_commit['deletions'] = int(deletions_match.group(1))

        # 마지막 커밋 추가
        if current_commit:
            commits.append(current_commit)

    return ok(commits)
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


def git_checkout(branch_or_file: str) -> Dict[str, Any]:
    """브랜치 전환 또는 파일 복원

    Args:
        branch_or_file: 브랜치명 또는 파일 경로

    Returns:
        성공: {'ok': True, 'data': 출력 메시지}
        실패: {'ok': False, 'error': 에러 메시지}
    """
    result = run_git_command(['checkout', branch_or_file])
    if result['ok']:
        return ok(result['data'])
    return err(result['error'])


def git_checkout_b(branch_name: str) -> Dict[str, Any]:
    """새 브랜치 생성 및 전환

    Args:
        branch_name: 생성할 브랜치명

    Returns:
        성공: {'ok': True, 'data': 출력 메시지}
        실패: {'ok': False, 'error': 에러 메시지}
    """
    result = run_git_command(['checkout', '-b', branch_name])
    if result['ok']:
        return ok(result['data'])
    return err(result['error'])


def git_stash(message: str = None) -> Dict[str, Any]:
    """작업 내용 임시 저장

    Args:
        message: stash 메시지 (선택사항)

    Returns:
        성공: {'ok': True, 'data': 출력 메시지}
        실패: {'ok': False, 'error': 에러 메시지}
    """
    cmd = ['stash', 'push']
    if message:
        cmd.extend(['-m', message])
    result = run_git_command(cmd)
    if result['ok']:
        return ok(result['data'])
    return err(result['error'])


def git_stash_pop() -> Dict[str, Any]:
    """임시 저장된 작업 복원

    Returns:
        성공: {'ok': True, 'data': 출력 메시지}
        실패: {'ok': False, 'error': 에러 메시지}
    """
    result = run_git_command(['stash', 'pop'])
    if result['ok']:
        return ok(result['data'])
    return err(result['error'])


def git_stash_list() -> Dict[str, Any]:
    """stash 목록 조회

    Returns:
        성공: {'ok': True, 'data': stash 목록}
        실패: {'ok': False, 'error': 에러 메시지}
    """
    result = run_git_command(['stash', 'list'])
    if result['ok']:
        stashes = result['data'].strip().split('\n') if result['data'].strip() else []
        return ok(stashes)
    return err(result['error'])


def git_reset_hard(commit: str = "HEAD") -> Dict[str, Any]:
    """특정 커밋으로 강제 리셋

    Args:
        commit: 리셋할 커밋 (기본값: HEAD)

    Returns:
        성공: {'ok': True, 'data': 출력 메시지}
        실패: {'ok': False, 'error': 에러 메시지}
    """
    result = run_git_command(['reset', '--hard', commit])
    if result['ok']:
        return ok(result['data'])
    return err(result['error'])


def git_merge(branch: str, no_ff: bool = False) -> Dict[str, Any]:
    """브랜치 병합

    Args:
        branch: 병합할 브랜치명
        no_ff: fast-forward 비활성화 여부

    Returns:
        성공: {'ok': True, 'data': 출력 메시지}
        실패: {'ok': False, 'error': 에러 메시지}
    """
    cmd = ['merge']
    if no_ff:
        cmd.append('--no-ff')
    cmd.append(branch)

    result = run_git_command(cmd)
    if result['ok']:
        return ok(result['data'])
    return err(result['error'])


def git_branch_d(branch: str, force: bool = False) -> Dict[str, Any]:
    """브랜치 삭제

    Args:
        branch: 삭제할 브랜치명
        force: 강제 삭제 여부

    Returns:
        성공: {'ok': True, 'data': 출력 메시지}
        실패: {'ok': False, 'error': 에러 메시지}
    """
    flag = '-D' if force else '-d'
    result = run_git_command(['branch', flag, branch])
    if result['ok']:
        return ok(result['data'])
    return err(result['error'])


def git_rebase(branch: str) -> Dict[str, Any]:
    """리베이스 수행

    Args:
        branch: 리베이스할 대상 브랜치

    Returns:
        성공: {'ok': True, 'data': 출력 메시지}
        실패: {'ok': False, 'error': 에러 메시지}
    """
    result = run_git_command(['rebase', branch])
    if result['ok']:
        return ok(result['data'])
    return err(result['error'])



def current_branch() -> Dict[str, Any]:
    """현재 Git 브랜치 반환

    Returns:
        성공: {'ok': True, 'data': '브랜치명'}
        실패: {'ok': False, 'error': 에러 메시지}
    """
    # status에서 브랜치 정보 추출
    status_result = git_status()
    if not status_result['ok']:
        return status_result

    # status 결과에서 브랜치 추출
    if isinstance(status_result['data'], dict):
        branch = status_result['data'].get('branch')
        if branch:
            return ok(branch)

    # status가 문자열인 경우 파싱
    status_text = str(status_result['data'])
    lines = status_text.split('\n')
    for line in lines:
        if line.startswith('On branch'):
            branch_name = line.replace('On branch', '').strip()
            return ok(branch_name)
        elif 'branch' in line.lower():
            # 다른 형식 처리
            parts = line.split()
            for i, part in enumerate(parts):
                if part == 'branch' and i + 1 < len(parts):
                    return ok(parts[i + 1])

    # 브랜치를 찾지 못한 경우 HEAD 직접 확인
    result = run_git_command(['rev-parse', '--abbrev-ref', 'HEAD'])
    if result['ok']:
        return ok(result['data'].strip())

    return err("Could not determine current branch")


def git_status_normalized() -> Dict[str, Any]:
    """Git 상태를 확장된 형식으로 반환

    Returns:
        dict: {
            'branch': str,
            'modified_count': int,
            'untracked_count': int,
            'staged_count': int,
            'files': list,
            'clean': bool
        }
    """
    status = git_status()
    if not status.get('ok'):
        return status

    data = status.get('data', {})

    # 정규화된 형식으로 변환
    normalized = {
        'branch': data.get('branch', 'unknown'),
        'modified_count': len([f for f in data.get('files', []) if f.get('type') == 'modified']),
        'untracked_count': len([f for f in data.get('files', []) if f.get('type') == 'untracked']),
        'staged_count': len([f for f in data.get('files', []) if f.get('index') not in [' ', '?']]),
        'files': data.get('files', []),
        'clean': data.get('clean', False)
    }

    return ok(normalized)