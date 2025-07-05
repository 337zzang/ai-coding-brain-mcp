"""
Improved Git Version Manager with Auto Upstream Detection
Based on the provided guide for fixing Git push issues
"""
import os
import sys
from pathlib import Path
from typing import Dict, Optional, Any, Union
from functools import wraps

# GitPython 가용성 확인
try:
    from git import Repo, GitCommandError
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    Repo = None
    GitCommandError = Exception

# 프로젝트 utils 사용
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from utils import verify_git_root, open_text
except ImportError:
    # Fallback 정의
    def verify_git_root(path):
        if not Path(path).joinpath('.git').exists():
            raise ValueError(f"Not a git repository: {path}")
        return Path(path).resolve()

    def open_text(path, mode='r', encoding=None):
        encoding = encoding or os.getenv('PYTHONIOENCODING', 'utf-8')
        return open(path, mode, encoding=encoding, errors='replace')


def _git_command(func):
    """Git 명령 실행 데코레이터 - 개선된 예외 처리"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            # None 반환 시 명시적 오류 처리
            if result is None:
                return {'ok': False, 'error': 'No data returned'}
            return {'ok': True, 'data': result}
        except GitCommandError as e:
            return {'ok': False, 'error': f"Git error: {str(e)}"}
        except Exception as e:
            return {'ok': False, 'error': f"Unexpected error: {str(e)}"}
    return wrapper


class GitVersionManager:
    """개선된 Git 버전 관리자 - 자동 upstream 감지"""

    def __init__(self, repo_path: Union[str, Path] = None):
        """
        Args:
            repo_path: Git 저장소 경로 (None이면 현재 디렉토리)
        """
        self.repo_path = Path(repo_path or Path.cwd()).resolve()
        self.repo = None
        self.disabled = False

        if not GIT_AVAILABLE:
            print("⚠️ GitPython not available - Git operations disabled")
            self.disabled = True
            return

        try:
            self.repo_path = verify_git_root(self.repo_path)
            self.repo = Repo(str(self.repo_path))
        except Exception as e:
            print(f"⚠️ Git initialization failed: {e}")
            self.disabled = True

    def _ensure_available(self) -> bool:
        """Git 사용 가능 여부 확인"""
        return not self.disabled and self.repo is not None

    @_git_command
    def status(self) -> Dict[str, Any]:
        """Git 상태 조회 - 개선된 반환값"""
        if not self._ensure_available():
            return None

        repo = self.repo
        return {
            'branch': repo.active_branch.name if not repo.head.is_detached else 'HEAD detached',
            'modified': [item.a_path for item in repo.index.diff(None)],
            'untracked': repo.untracked_files,
            'staged': [item.a_path for item in repo.index.diff('HEAD')] if repo.head.is_valid() else [],
            'clean': not repo.is_dirty(untracked_files=True)
        }

    @_git_command
    def add(self, files: Union[str, list] = '.') -> bool:
        """파일 스테이징"""
        if not self._ensure_available():
            return False

        if isinstance(files, str):
            files = [files]
        self.repo.index.add(files)
        return True

    @_git_command
    def commit(self, message: str) -> Optional[str]:
        """커밋 생성"""
        if not self._ensure_available():
            return None

        commit = self.repo.index.commit(message)
        return commit.hexsha[:8]

    @_git_command
    def stash_save(self, message: Optional[str] = None) -> bool:
        """변경사항 stash"""
        if not self._ensure_available():
            return False

        self.repo.git.stash('save', message or 'Auto stash')
        return True

    @_git_command
    def stash_pop(self) -> bool:
        """최근 stash 복원"""
        if not self._ensure_available():
            return False

        self.repo.git.stash('pop')
        return True

    @_git_command
    def create_branch(self, branch_name: str, checkout: bool = True) -> bool:
        """브랜치 생성"""
        if not self._ensure_available():
            return False

        new_branch = self.repo.create_head(branch_name)
        if checkout:
            new_branch.checkout()
        return True

    @_git_command
    def switch_branch(self, branch_name: str) -> bool:
        """브랜치 전환"""
        if not self._ensure_available():
            return False

        self.repo.git.checkout(branch_name)
        return True

    @_git_command
    def get_log(self, max_count: int = 10) -> list:
        """커밋 로그 조회"""
        if not self._ensure_available():
            return []

        commits = []
        for commit in self.repo.iter_commits(max_count=max_count):
            commits.append({
                'hash': commit.hexsha[:8],
                'message': commit.message.strip(),
                'author': str(commit.author),
                'date': commit.committed_datetime.strftime('%Y-%m-%d %H:%M:%S')
            })
        return commits

    def get_current_branch(self) -> Optional[str]:
        """현재 브랜치명 반환 - 개선된 구현"""
        # _run 메서드 사용하여 정확한 브랜치 정보 가져오기
        result = self._run("symbolic-ref", "--short", "HEAD")
        if result.get('ok'):
            return result['stdout'].strip()

        # Fallback to GitPython
        if self._ensure_available():
            try:
                return self.repo.active_branch.name
            except:
                return None
        return None

    def is_repo_clean(self) -> bool:
        """저장소 상태가 깨끗한지 확인"""
        if not self._ensure_available():
            return True

        try:
            return not self.repo.is_dirty(untracked_files=True)
        except:
            return True

    def _run(self, *args: str, cwd: str | Path | None = None) -> Dict[str, Any]:
        """공통 셸 실행 래퍼"""
        import subprocess
        import platform
        import os

        # Windows에서 git.exe 경로 찾기
        git_cmd = "git"
        if platform.system() == "Windows":
            # 일반적인 Git 설치 경로들
            possible_paths = [
                r"C:\Program Files\Git\cmd\git.exe",
                r"C:\Program Files (x86)\Git\cmd\git.exe",
                r"C:\Git\cmd\git.exe",
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    git_cmd = path
                    break

        result = subprocess.run(
            [git_cmd, *args],
            cwd=cwd or self.repo_path,
            capture_output=True,
            text=True,
        )
        return {
            "ok": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "code": result.returncode,
            "data": result.stdout.strip() if result.returncode == 0 else None
        }

    def push(self, remote: str = "origin", branch: str | None = None,
             set_upstream: bool | None = None) -> Dict[str, Any]:
        """
        개선된 push 메서드 - 자동 upstream 감지

        Args:
            remote: 원격 저장소 이름 (기본: origin)
            branch: 브랜치 이름 (None이면 현재 브랜치)
            set_upstream:
                - None: 자동 감지 (upstream 없으면 True)
                - True: 항상 -u 사용
                - False: 기존 로직 유지
        """
        # 1) 현재 브랜치 결정
        current_branch = branch or self.get_current_branch()
        if not current_branch:
            return {'ok': False, 'stderr': '현재 브랜치를 알 수 없습니다.', 'code': 1}

        # 2) upstream 여부 확인 (set_upstream이 None일 때만)
        if set_upstream is None:
            # git rev-parse --symbolic-full-name @{u} 실행
            upstream_check = self._run("rev-parse", "--symbolic-full-name", "@{u}")
            # exitcode 0 → upstream 이미 존재
            # exitcode != 0 → upstream 없음 → set_upstream = True
            set_upstream = not upstream_check.get('ok', False)

            if set_upstream:
                print(f"📌 Upstream이 설정되지 않은 브랜치입니다. 자동으로 -u 옵션을 추가합니다.")

        # 3) push 명령 구성
        args = ["push"]
        if set_upstream:
            args.append("-u")
        args.append(remote)
        args.append(current_branch)

        # 4) push 실행
        result = self._run(*args)

        # 디버그 정보 추가
        if result['ok']:
            print(f"✅ Push 성공: {current_branch} → {remote}")
        else:
            print(f"❌ Push 실패: {result.get('stderr', 'Unknown error')}")

        return result

    def pull(self, remote: str = "origin", branch: str | None = None,
             rebase: bool = False) -> Dict[str, Any]:
        """
        git pull [--rebase] remote [branch]
        """
        args = ["pull"]
        if rebase:
            args.append("--rebase")
        args.append(remote)
        if branch:
            args.append(branch)
        return self._run(*args)

# 편의 함수들 - 간단한 래퍼
def git_status(repo_path: Optional[str] = None) -> Dict[str, Any]:
    """Git 상태 조회"""
    mgr = GitVersionManager(repo_path)
    result = mgr.status()
    return result.get('data', {}) if result.get('ok') else {}

def git_push(remote: str = "origin", branch: str = None,
             repo_path: Optional[str] = None) -> bool:
    """개선된 push 함수 - 자동 upstream 처리"""
    mgr = GitVersionManager(repo_path)
    result = mgr.push(remote, branch)  # set_upstream은 자동 감지
    return result.get('ok', False)

def git_commit_smart(message: str, repo_path: Optional[str] = None) -> bool:
    """스마트 커밋 - 변경사항이 있을 때만"""
    mgr = GitVersionManager(repo_path)

    status = mgr.status()
    if not status.get('ok') or not status.get('data'):
        return False

    data = status['data']
    if not data['modified'] and not data['untracked']:
        return False

    # 모든 변경사항 추가 및 커밋
    if mgr.add('.').get('ok'):
        commit_result = mgr.commit(message)
        return commit_result.get('ok', False)

    return False

def git_stash_save(message: Optional[str] = None, repo_path: Optional[str] = None) -> bool:
    """Stash 저장"""
    mgr = GitVersionManager(repo_path)
    result = mgr.stash_save(message)
    return result.get('ok', False)

def git_branch_smart(branch_name: str, repo_path: Optional[str] = None) -> bool:
    """브랜치 생성 및 전환"""
    mgr = GitVersionManager(repo_path)
    result = mgr.create_branch(branch_name)
    return result.get('ok', False)


# 테스트 및 데모
if __name__ == "__main__":
    print("🔍 Git Version Manager 개선 버전 테스트")
    print("=" * 60)

    mgr = GitVersionManager()

    # 현재 브랜치 확인
    current = mgr.get_current_branch()
    print(f"현재 브랜치: {current}")

    # 상태 확인
    status = mgr.status()
    if status['ok']:
        print(f"상태: {status['data']['branch']} - {'깨끗함' if status['data']['clean'] else '변경사항 있음'}")

    # Push 테스트 (자동 upstream 감지)
    print("\n📤 Push 테스트 (자동 upstream 감지):")
    push_result = mgr.push()
    print(f"결과: {'성공' if push_result['ok'] else '실패'}")
