"""
Git 작업 - 프로토콜 추적 포함
"""
import subprocess
import os
import platform
import shutil
import winreg
from typing import List, Dict, Any, Optional, Union
from .core import track_execution


def find_git_executable() -> Optional[str]:
    """Git 실행 파일을 스마트하게 찾는 함수"""
    
    # 1. shutil.which 사용 (PATH에 있는 경우)
    git_path = shutil.which('git')
    if git_path:
        return git_path
    
    # 2. Windows인 경우 추가 검색
    if platform.system() == 'Windows':
        # 일반적인 Git 설치 경로들
        common_paths = [
            r"C:\Program Files\Git\bin\git.exe",
            r"C:\Program Files\Git\cmd\git.exe",
            r"C:\Program Files (x86)\Git\bin\git.exe",
            r"C:\Program Files (x86)\Git\cmd\git.exe",
            r"C:\Users\%USERNAME%\AppData\Local\Programs\Git\bin\git.exe",
            r"C:\Users\%USERNAME%\AppData\Local\Programs\Git\cmd\git.exe",
        ]
        
        # 환경변수 확장
        import os
        for path in common_paths:
            expanded_path = os.path.expandvars(path)
            if os.path.exists(expanded_path):
                return expanded_path
        
        # 3. 레지스트리에서 Git 찾기
        try:
            # Git for Windows 레지스트리 위치들
            registry_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\GitForWindows"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\GitForWindows"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\GitForWindows"),
            ]
            
            for hkey, subkey in registry_paths:
                try:
                    with winreg.OpenKey(hkey, subkey) as key:
                        install_path = winreg.QueryValueEx(key, "InstallPath")[0]
                        git_exe = os.path.join(install_path, "bin", "git.exe")
                        if os.path.exists(git_exe):
                            return git_exe
                        git_exe = os.path.join(install_path, "cmd", "git.exe")
                        if os.path.exists(git_exe):
                            return git_exe
                except:
                    continue
        except:
            pass
        
        # 4. where 명령 사용 (Windows)
        try:
            result = subprocess.run(['where', 'git'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                paths = result.stdout.strip().split('\n')
                for path in paths:
                    if os.path.exists(path):
                        return path
        except:
            pass
    
    # 5. Unix/Linux/Mac에서 which 명령 사용
    else:
        try:
            result = subprocess.run(['which', 'git'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except:
            pass
    
    return None

def run_git_command(args: List[str], cwd: str = ".") -> Dict[str, Any]:
    """Git 명령 실행 헬퍼 (개선된 버전)"""
    
    # Git 실행 파일 찾기
    git_cmd = find_git_executable()
    
    if not git_cmd:
        return {
            'success': False,
            'stdout': '',
            'stderr': 'Git을 찾을 수 없습니다. Git이 설치되어 있는지 확인하세요. (https://git-scm.com/downloads)',
            'returncode': -1
        }
    
    try:
        result = subprocess.run(
            [git_cmd] + args,
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
    except FileNotFoundError:
        return {
            'success': False,
            'stdout': '',
            'stderr': f'Git 실행 파일을 찾았지만 실행할 수 없습니다: {git_cmd}',
            'returncode': -1
        }
    except Exception as e:
        return {
            'success': False,
            'stdout': '',
            'stderr': f'Git 명령 실행 중 오류 발생: {str(e)}',
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
        elif 'M' in status:
            if status[0] == 'M':
                staged.append(filepath)
            if status[1] == 'M':
                modified.append(filepath)
        elif 'A' in status:
            staged.append(filepath)

    return {
        'success': True,
        'stdout': result['stdout'],
        'stderr': result['stderr'],
        'modified': modified,
        'untracked': untracked,
        'staged': staged,
        'clean': not (modified or untracked or staged)
    }


@track_execution
def git_add(files: Union[str, List[str]] = None, all: bool = False, cwd: str = ".") -> Dict[str, Any]:
    """파일을 스테이징"""
    if all:
        args = ['add', '-A']
    elif files:
        # 문자열이면 리스트로 변환
        if isinstance(files, str):
            files = [files]
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