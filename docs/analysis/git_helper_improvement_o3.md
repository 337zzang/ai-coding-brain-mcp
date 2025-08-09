# Git Helper 개선 분석 (O3 + Claude)
생성일: 2025-08-09

## O3 분석 결과

아래 예시는 “한 ​파일로 복-붙” 해도 바로 동작하도록 작성된 git.py 의 핵심 부분입니다.  
(typing-hint, 에러클래스, docstring 을 모두 넣어 두었으니 그대로 써도 되고, 필요 없는 부분은 삭제해도 됩니다)

```python
# git.py
from __future__ import annotations

import os
import sys
import shutil
import subprocess
import locale
from pathlib import Path
from typing import List, Dict, Optional

# --------------------------------------------------------------------------- #
# 내부-전용 예외
# --------------------------------------------------------------------------- #
class GitError(RuntimeError):
    """git 명령이 비정상 종료되었을 때 발생"""

class GitTimeoutError(GitError):
    """timeout 으로 git 이 강제 종료됐을 때 발생"""

# --------------------------------------------------------------------------- #
# git 실행 파일 탐색 – Cross-Platform
# --------------------------------------------------------------------------- #
def find_git_executable() -> str:
    """
    PATH 를 우선 탐색하고, Windows 의 보편적인 설치 경로까지
    fallback 하는 크로스플랫폼 버전.
    """
    git = shutil.which("git")
    if git:                             # Linux / macOS / PATH 에 등록된 Windows
        return git

    # ── Windows: PATH 에 없다면 기본 설치 위치 탐색
    if sys.platform.startswith("win"):
        for root in (
            r"C:\Program Files\Git",
            r"C:\Program Files (x86)\Git",
        ):
            exe = Path(root, "cmd", "git.exe")
            if exe.exists():
                return str(exe)

    raise FileNotFoundError(
        "Git executable not found. "
        "Please install Git and/or put it on your PATH."
    )

# --------------------------------------------------------------------------- #
# 환경변수 및 공통 옵션
# --------------------------------------------------------------------------- #
def _base_env() -> dict:
    """
    출력 안정성과 비대화 실행을 위해 필요한 git 환경변수를 세팅한다.
    모든 플랫폼에서 문제없이 동작하도록 값은 무조건 문자열("") 로 지정.
    """
    env = os.environ.copy()
    env.update(
        {
            # 언어를 고정해 파싱 난수를 방지
            "LANG": "C",
            "LC_ALL": "C",
            # 불필요한 pager 나 프롬프트 제거
            "GIT_PAGER": "",              # '' 로 두면 Windows 도 안전
            "GIT_TERMINAL_PROMPT": "0",   # 자격 증명 입력방지
            # 잠금 최소화(옵션)
            "GIT_OPTIONAL_LOCKS": "0",
        }
    )
    return env

# --------------------------------------------------------------------------- #
# git 명령 실행 래퍼
# --------------------------------------------------------------------------- #
def run_git_command(
    args: List[str],
    cwd: Optional[str] = None,
    *,
    timeout: float = 30.0,
    encoding: str | None = "utf-8",
    raise_on_error: bool = True,
) -> subprocess.CompletedProcess[str]:
    """
    subprocess.run 의 thin-wrapper.
    - timeout 이 지나면 GitTimeoutError 발생
    - text=True 로 받아 바로 str 로 디코딩
    - encoding 을 명시하되, 실패 시 locale.getpreferredencoding 사용
    """
    git_exe = find_git_executable()
    cmd = [git_exe, *args]

    if encoding is None:                     # 사용자가 None 을 주면 locale 사용
        encoding = locale.getpreferredencoding(False)

    try:
        cp = subprocess.run(
            cmd,
            cwd=cwd or os.getcwd(),
            capture_output=True,
            text=True,               # str 로 직접 반환
            encoding=encoding,
            errors="replace",        # 깨진 글자는 � 로 대체
            env=_base_env(),
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise GitTimeoutError(
            f"Git command timed-out after {timeout}s: {' '.join(cmd)}"
        ) from exc

    if raise_on_error and cp.returncode != 0:
        raise GitError(
            f"Git command failed (exit {cp.returncode}): {' '.join(cmd)}\n"
            f"stderr: {cp.stderr.strip()}"
        )

    return cp

# --------------------------------------------------------------------------- #
# git status --porcelain 파싱
# --------------------------------------------------------------------------- #
def git_status(cwd: str | Path | None = None) -> List[Dict[str, str]]:
    """
    git status --porcelain 출력을
    [{'status': ' M', 'path': 'file.py'}, …] 형태로 변환
    (앞 한 칸은 index, 뒤 한 칸은 working-tree 상태)
    """
    cp = run_git_command(["status", "--porcelain"], cwd=str(cwd) if cwd else None)
    items: list[dict[str, str]] = []

    for line in cp.stdout.splitlines():
        if not line or len(line) < 3:
            continue
        status = line[:2]               # 두 글자 (예: " M", "M ", "A ")
        path = line[3:] if line[2] == " " else line[2:].lstrip()
        items.append({"status": status, "path": path})

    return items

# --------------------------------------------------------------------------- #
# git log 파싱
# --------------------------------------------------------------------------- #
_FIELD_SEP = "\x1f"    # Unit Separator (FS)
_RECORD_SEP = "\x1e"   # Record Separator (RS)


def git_log(
    cwd: str | Path | None = None,
    *,
    limit: int = 10,
) -> List[Dict[str, str]]:
    """
    git log --pretty=format 를 이용해
    [{'hash': …, 'author': …, 'date': …, 'message': …}, …] 반환
    """
    fmt = f"%H%x1f%an%x1f%ad%x1f%s%x1e"
    args = ["log", f"-n{limit}", f"--pretty=format:{fmt}", "--date=iso"]

    cp = run_git_command(args, cwd=str(cwd) if cwd else None)

    records = cp.stdout.rstrip(_RECORD_SEP).split(_RECORD_SEP)
    parsed: list[dict[str, str]] = []

    for rec in records:
        if not rec:
            continue
        h, author, date, msg = rec.split(_FIELD_SEP)
        parsed.append(
            {"hash": h, "author": author, "date": date, "message": msg}
        )

    return parsed
```

──────────────────────────────────────────────────────────────────────────────
설명 및 개선 포인트 정리
──────────────────────────────────────────────────────────────────────────────
1. run_git_command 개선  
   • shutil.which 로 git 탐색 후, Windows 기본 설치 위치 두 곳을 fallback  
   • text=True + encoding 으로 `stdout/err` 를 바로 str 로 받아 수동 디코딩 삭제  
   • 기본 30 초 timeout, 초과 시 GitTimeoutError 발생  
   • LANG/LC_ALL/GIT_PAGER/GIT_TERMINAL_PROMPT 등 환경변수 고정 → 파싱 안정화  
   • 오류 코드(≠0) 일 때 GitError 로 예외 발생 → Dead-code 제거  
2. git_status 구조화  
   • `git status --porcelain` 은 항상 ‘XY path’ 형태의 고정폭 출력  
   • 두 문자(X·Y)를 그대로 살려 `{'status': 'M ', 'path': 'foo.py'}` 형태 반환  
3. git_log 구조화  
   • 구분 문자를 0x1f/0x1e 로 지정해 “필드/레코드” 충돌 위험 제거  
   • `--date=iso` 로 플랫폼 독립적인 날짜 형식 확보  
4. 크로스플랫폼 호환성  
   • pathlib 로 경로 처리, shutil.which 사용  
   • ‘LANG=C’ 지정으로 로케일 차단, pager ‑off 로 REPL 과 CI 모두 안전  
   • Windows 도 cat/less 없이 동작하도록 GIT_PAGER = "" 설정  
   • text=True 로 CRLF 문제 자동 처리  

위 코드를 기준으로 하면 REPL·스크립트·CI 어느 곳에서도 “타임아웃 없이 멈추거나,  
로케일/인코딩 때문에 깨지는” 상황을 상당 부분 예방할 수 있습니다.

## Claude 추가 개선 코드

### 1. run_git_command 개선

import subprocess
import shutil
import os
from typing import List, Dict, Any, Optional

def find_git_executable() -> Optional[str]:
    """Git 실행 파일 찾기 (개선됨 - 크로스플랫폼)"""
    # shutil.which를 사용하여 플랫폼 독립적으로 Git 찾기
    git_path = shutil.which('git')
    if not git_path:
        raise FileNotFoundError("Git executable not found in PATH")
    return git_path

def run_git_command(
    args: List[str], 
    cwd: Optional[str] = None,
    timeout: int = 30,
    check: bool = True
) -> Dict[str, Any]:
    """개선된 Git 명령 실행

    Args:
        args: Git 명령어 인자 리스트
        cwd: 작업 디렉토리 (None이면 현재 디렉토리)
        timeout: 최대 실행 시간 (초)
        check: 에러 시 예외 발생 여부

    Returns:
        표준 응답 형식 딕셔너리
    """
    try:
        git_exe = find_git_executable()
        cmd = [git_exe] + args

        # 환경변수 설정 (출력 표준화)
        env = os.environ.copy()
        env['GIT_PAGER'] = 'cat'  # 페이징 비활성화
        env['LC_ALL'] = 'C'       # 영어 출력 강제
        env['LANG'] = 'C'

        # subprocess 실행 (개선됨)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,              # ✅ 텍스트 모드 사용
            encoding='utf-8',       # ✅ UTF-8 인코딩 명시
            cwd=cwd or os.getcwd(),
            timeout=timeout,        # ✅ 타임아웃 설정
            env=env,               # ✅ 환경변수 전달
            errors='replace'       # 디코딩 에러 시 대체 문자 사용
        )

        if result.returncode == 0:
            return {
                'ok': True,
                'data': result.stdout.strip(),
                'stderr': result.stderr.strip() if result.stderr else None,
                'returncode': result.returncode
            }
        else:
            error_msg = result.stderr.strip() if result.stderr else f"Command failed with code {result.returncode}"
            if check:
                return {'ok': False, 'error': error_msg, 'returncode': result.returncode}
            else:
                # check=False인 경우 에러여도 데이터 반환
                return {
                    'ok': False,
                    'data': result.stdout.strip(),
                    'error': error_msg,
                    'returncode': result.returncode
                }

    except subprocess.TimeoutExpired as e:
        return {'ok': False, 'error': f"Git command timed out after {timeout} seconds"}
    except FileNotFoundError as e:
        return {'ok': False, 'error': str(e)}
    except Exception as e:
        return {'ok': False, 'error': f"Git command error: {str(e)}"}


### 2. git_status 구조화

@safe_execution
def git_status(cwd: Optional[str] = None, include_branch: bool = True) -> Dict[str, Any]:
    """개선된 Git 상태 확인 - 구조화된 데이터 반환

    Returns:
        {
            'ok': True,
            'data': {
                'branch': 'main',
                'files': [
                    {'status': 'M ', 'path': 'modified_file.py'},
                    {'status': 'A ', 'path': 'new_file.txt'},
                    {'status': '??', 'path': 'untracked.md'}
                ],
                'summary': {
                    'modified': 1,
                    'added': 1,
                    'deleted': 0,
                    'untracked': 1
                }
            }
        }
    """
    # 현재 브랜치 가져오기
    branch_result = None
    if include_branch:
        branch_cmd = run_git_command(['branch', '--show-current'], cwd=cwd)
        if branch_cmd['ok']:
            branch_result = branch_cmd['data'].strip()

    # porcelain 형식으로 상태 가져오기
    status_result = run_git_command(['status', '--porcelain'], cwd=cwd)

    if not status_result['ok']:
        return status_result

    # 파일 상태 파싱
    files = []
    summary = {'modified': 0, 'added': 0, 'deleted': 0, 'untracked': 0, 'renamed': 0}

    for line in status_result['data'].split('\n'):
        if not line.strip():
            continue

        # porcelain 형식: XY filename
        # X = index 상태, Y = working tree 상태
        if len(line) >= 3:
            status_code = line[:2]
            filepath = line[3:].strip()

            files.append({
                'status': status_code,
                'path': filepath,
                'index': status_code[0],    # staged 상태
                'worktree': status_code[1]  # working tree 상태
            })

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

    return ok({
        'branch': branch_result,
        'files': files,
        'summary': summary,
        'clean': len(files) == 0
    })


### 3. git_log 구조화

@safe_execution
def git_log(
    limit: int = 10,
    cwd: Optional[str] = None,
    format_type: str = 'full'
) -> Dict[str, Any]:
    """개선된 Git 로그 조회 - 구조화된 데이터 반환

    Args:
        limit: 조회할 커밋 수
        cwd: 작업 디렉토리
        format_type: 'full', 'oneline', 'stats'

    Returns:
        {
            'ok': True,
            'data': [
                {
                    'hash': 'abc123...',
                    'short_hash': 'abc123',
                    'author': 'John Doe',
                    'author_email': 'john@example.com',
                    'date': '2025-08-09T10:00:00+09:00',
                    'message': 'feat: Add new feature',
                    'subject': 'Add new feature',
                    'body': 'Detailed description...'
                }
            ]
        }
    """
    # 구조화된 포맷 정의 (구분자 사용)
    # %H: full hash, %h: short hash, %an: author name, %ae: author email
    # %aI: author date (ISO), %s: subject, %b: body
    delimiter = '|||'

    if format_type == 'full':
        pretty_format = f"%H{delimiter}%h{delimiter}%an{delimiter}%ae{delimiter}%aI{delimiter}%s{delimiter}%b"
        end_marker = '---END---'
        args = [
            'log',
            f'--max-count={limit}',
            f'--pretty=format:{pretty_format}{end_marker}'
        ]
    elif format_type == 'oneline':
        args = ['log', f'--max-count={limit}', '--oneline']
    else:  # stats
        args = ['log', f'--max-count={limit}', '--stat', '--oneline']

    result = run_git_command(args, cwd=cwd)

    if not result['ok']:
        return result

    # 결과 파싱
    commits = []

    if format_type == 'full':
        # 구조화된 파싱
        raw_output = result['data']
        if not raw_output:
            return ok([])

        # END 마커로 각 커밋 분리
        commit_chunks = raw_output.split(end_marker)

        for chunk in commit_chunks:
            chunk = chunk.strip()
            if not chunk:
                continue

            parts = chunk.split(delimiter)
            if len(parts) >= 6:
                commit_data = {
                    'hash': parts[0],
                    'short_hash': parts[1],
                    'author': parts[2],
                    'author_email': parts[3],
                    'date': parts[4],
                    'subject': parts[5],
                    'body': parts[6] if len(parts) > 6 else ''
                }

                # 메시지 전체 (subject + body)
                commit_data['message'] = commit_data['subject']
                if commit_data['body']:
                    commit_data['message'] += '\n\n' + commit_data['body']

                commits.append(commit_data)

    else:
        # 간단한 형식은 라인별로 반환
        for line in result['data'].split('\n'):
            if line.strip():
                if format_type == 'oneline':
                    # oneline 형식: "hash message"
                    parts = line.split(' ', 1)
                    if len(parts) == 2:
                        commits.append({
                            'short_hash': parts[0],
                            'subject': parts[1]
                        })
                else:
                    commits.append({'line': line})

    return ok(commits)

