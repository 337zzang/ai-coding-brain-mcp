"""
Enhanced Git Operations - 표준화된 API와 에러 핸들링 적용
"""
import subprocess
import os
import re
from typing import Dict, List, Any, Optional, Union, Literal
from pathlib import Path

import base_api_fixed
import error_handler
import helper_result

# Git 작업 타입 정의
GitOperation = Literal['add', 'commit', 'push', 'pull', 'branch', 'checkout', 'merge', 'rebase']
CommitType = Literal['feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore']

class EnhancedGitAPI(base_api_fixed.BaseAPI):
    """표준화된 Git API 클래스"""

    def __init__(self):
        # Git 설정을 먼저 초기화
        self.git_executable = self._find_git_executable()
        self.verbose = False

        # Git 특화 재시도 정책
        self.git_retry_policy = error_handler.RetryPolicy(
            max_attempts=3,
            base_delay=0.5,
            retry_on_categories=[error_handler.ErrorCategory.NETWORK, error_handler.ErrorCategory.GIT]
        )

        # 부모 클래스 초기화 (operations 등록됨)
        super().__init__("GitAPI")

    def _initialize_operations(self):
        """Git 작업들 등록"""

        # Status 작업
        self.register_operation(base_api_fixed.APIOperation(
            name="status",
            operation_type=base_api_fixed.OperationType.READ,
            parameters=[
                base_api_fixed.ParameterSpec("porcelain", bool, False, False, "Machine-readable format"),
                base_api_fixed.ParameterSpec("cwd", str, False, None, "Working directory")
            ],
            description="Get Git repository status",
            examples=["status()", "status(porcelain=True)"],
            retry_policy=None  # 나중에 설정
        ))

        # Add 작업
        self.register_operation(base_api_fixed.APIOperation(
            name="add",
            operation_type=base_api_fixed.OperationType.WRITE,
            parameters=[
                base_api_fixed.ParameterSpec("files", Union[str, List[str]], False, ".", "Files to add"),
                base_api_fixed.ParameterSpec("update", bool, False, False, "Add only modified files"),
                base_api_fixed.ParameterSpec("force", bool, False, False, "Force add ignored files")
            ],
            description="Add files to staging area",
            examples=["add()", "add('file.py')", "add(['file1.py', 'file2.py'])"]
        ))

        # Commit 작업
        self.register_operation(base_api_fixed.APIOperation(
            name="commit",
            operation_type=base_api_fixed.OperationType.WRITE,
            parameters=[
                base_api_fixed.ParameterSpec("message", str, False, None, "Commit message"),
                base_api_fixed.ParameterSpec("smart_mode", bool, False, False, "Auto-generate message")
            ],
            description="Create a commit",
            examples=["commit('Add feature')", "commit(smart_mode=True)"]
        ))

    def _find_git_executable(self) -> Optional[str]:
        """Git 실행 파일 찾기"""
        # Windows에서 일반적인 Git 위치들
        possible_paths = [
            r"C:\Program Files\Git\bin\git.exe",
            r"C:\Program Files (x86)\Git\bin\git.exe",
        ]

        # PATH에서 git 찾기
        try:
            result = subprocess.run(['where', 'git'], capture_output=True, text=True)
            if result.returncode == 0:
                git_path = result.stdout.strip().split('\n')[0]
                if os.path.exists(git_path):
                    return git_path
        except:
            pass

        # 일반적인 경로에서 찾기
        for path in possible_paths:
            if os.path.exists(path):
                return path

        return 'git'  # 기본값

    def _run_git_command(self, args: List[str], cwd: Optional[str] = None) -> helper_result.HelperResult:
        """Git 명령 실행"""
        if not self.git_executable:
            raise RuntimeError("Git executable not found")

        cmd = [self.git_executable] + args

        if self.verbose:
            print(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=cwd or os.getcwd(),
                encoding='utf-8',
                errors='replace'
            )

            if result.returncode == 0:
                return helper_result.HelperResult(True, data={
                    'output': result.stdout,
                    'command': ' '.join(args)
                })
            else:
                # Git 특화 에러 처리
                error_msg = result.stderr or result.stdout
                if "not a git repository" in error_msg.lower():
                    raise RuntimeError(f"Not a git repository: {cwd or os.getcwd()}")
                elif "permission denied" in error_msg.lower():
                    raise PermissionError(f"Git permission denied: {error_msg}")
                else:
                    raise RuntimeError(f"Git command failed: {error_msg}")
        except Exception as e:
            raise e

    def _execute_core_operation(self, operation_name: str, params: Dict[str, Any]) -> Any:
        """핵심 Git 작업 실행"""
        if operation_name == "status":
            return self._execute_status(**params)
        elif operation_name == "add":
            return self._execute_add(**params)
        elif operation_name == "commit":
            return self._execute_commit(**params)
        else:
            raise ValueError(f"Unknown operation: {operation_name}")

    def _execute_status(self, porcelain: bool = False, cwd: Optional[str] = None) -> Dict[str, Any]:
        """Git 상태 확인"""
        args = ['status']
        if porcelain:
            args.append('--porcelain')

        result = self._run_git_command(args, cwd)
        if not result.ok:
            raise RuntimeError(result.error)

        output = result.data['output']
        status_data = {
            'modified': [],
            'added': [],
            'deleted': [],
            'untracked': [],
            'raw_output': output,
            'is_clean': not output.strip()
        }

        if porcelain and output.strip():
            for line in output.strip().split('\n'):
                if not line:
                    continue
                status = line[:2]
                filename = line[3:]

                if status == ' M' or status == 'M ':
                    status_data['modified'].append(filename)
                elif status == 'A ':
                    status_data['added'].append(filename)
                elif status == 'D ':
                    status_data['deleted'].append(filename)
                elif status == '??':
                    status_data['untracked'].append(filename)

        return status_data

    def _execute_add(self, files: Union[str, List[str]] = ".", 
                    update: bool = False, force: bool = False) -> Dict[str, Any]:
        """파일을 스테이징 영역에 추가"""
        args = ['add']

        if update:
            args.append('-u')
        if force:
            args.append('-f')

        if isinstance(files, str):
            args.append(files)
        else:
            args.extend(files)

        result = self._run_git_command(args)
        if not result.ok:
            raise RuntimeError(result.error)

        return {
            'files_added': files,
            'command': result.data['command']
        }

    def _execute_commit(self, message: Optional[str] = None, smart_mode: bool = False) -> Dict[str, Any]:
        """커밋 생성"""
        # 스마트 모드 또는 메시지 없을 때 자동 생성
        if smart_mode or not message:
            message = self._generate_commit_message()

        args = ['commit', '-m', message]

        result = self._run_git_command(args)
        if not result.ok:
            raise RuntimeError(result.error)

        return {
            'message': message,
            'command': result.data['command']
        }

    def _generate_commit_message(self) -> str:
        """커밋 메시지 자동 생성"""
        try:
            status_result = self._execute_status(porcelain=True)

            modified = status_result.get('modified', [])
            added = status_result.get('added', [])
            deleted = status_result.get('deleted', [])

            # 커밋 타입 결정
            if added and not modified and not deleted:
                commit_type = 'feat'
            elif deleted and not added and not modified:
                commit_type = 'chore'
            else:
                commit_type = 'fix' if modified else 'chore'

            # 메시지 생성
            if added:
                return f"{commit_type}: Add {', '.join(added[:3])}"
            elif modified:
                return f"{commit_type}: Update {', '.join(modified[:3])}"
            elif deleted:
                return f"{commit_type}: Remove {', '.join(deleted[:3])}"
            else:
                return f"{commit_type}: Update files"

        except Exception:
            return "chore: Update files"

    def is_repository(self) -> bool:
        """현재 디렉토리가 Git 저장소인지 확인"""
        try:
            result = self._run_git_command(['rev-parse', '--git-dir'])
            return result.ok
        except:
            return False

# 편의 함수들
def git_status() -> helper_result.HelperResult:
    """Git 상태 확인"""
    api = EnhancedGitAPI()
    return api.execute_operation("status", porcelain=True)

def git_add(files: Union[str, List[str]] = ".") -> helper_result.HelperResult:
    """파일을 스테이징 영역에 추가"""
    api = EnhancedGitAPI()
    return api.execute_operation("add", files=files)

def git_commit(message: str) -> helper_result.HelperResult:
    """커밋 생성"""
    api = EnhancedGitAPI()
    return api.execute_operation("commit", message=message)

def git_commit_smart() -> helper_result.HelperResult:
    """스마트 커밋"""
    api = EnhancedGitAPI()
    return api.execute_operation("commit", smart_mode=True)
