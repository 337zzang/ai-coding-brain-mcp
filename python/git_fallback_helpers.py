"""
Git Version Manager Fallback 개선
"""
from typing import Dict, Any, Optional
import subprocess
import os

try:
    from helper_result import HelperResult
except ImportError:
    from helper_result import HelperResult


class GitFallbackHelpers:
    """Git 명령 실행을 위한 Fallback 헬퍼"""
    
    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.getcwd()
        self._disabled = False
        
    def _run_git_command(self, args: list) -> HelperResult:
        """Git 명령 실행"""
        if self._disabled:
            return HelperResult.failure("Git helpers disabled")
            
        try:
            result = subprocess.run(
                ['git'] + args,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                return HelperResult.success(result.stdout.strip())
            else:
                return HelperResult.failure(result.stderr.strip())
                
        except FileNotFoundError:
            self._disabled = True
            return HelperResult.failure("Git not found in PATH")
        except Exception as e:
            return HelperResult.failure(f"Git command error: {str(e)}")
    
    def git_status(self) -> HelperResult:
        """Git 상태 확인"""
        status_result = self._run_git_command(['status', '--porcelain'])
        if not status_result.ok:
            return status_result
            
        branch_result = self._run_git_command(['branch', '--show-current'])
        
        # 상태 파싱
        modified = []
        untracked = []
        
        if status_result.data:
            for line in status_result.data.split('\n'):
                if line.startswith(' M'):
                    modified.append(line[3:])
                elif line.startswith('??'):
                    untracked.append(line[3:])
        
        return HelperResult.success({
            'branch': branch_result.data if branch_result.ok else 'unknown',
            'modified': modified,
            'untracked': untracked,
            'clean': len(modified) == 0 and len(untracked) == 0
        })
    
    def git_add(self, files: list) -> HelperResult:
        """파일 추가"""
        return self._run_git_command(['add'] + files)
    
    def git_commit(self, message: str) -> HelperResult:
        """커밋"""
        return self._run_git_command(['commit', '-m', message])
    
    def git_stash(self, message: str = None) -> HelperResult:
        """Stash 생성"""
        args = ['stash', 'save']
        if message:
            args.append(message)
        return self._run_git_command(args)
    
    def git_stash_pop(self) -> HelperResult:
        """Stash pop"""
        return self._run_git_command(['stash', 'pop'])