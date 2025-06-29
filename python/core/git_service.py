"""
Git Service Module
플랫폼 독립적인 Git 명령어 실행을 위한 서비스 모듈
"""
import subprocess
import os
import platform
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import tempfile
import json


class GitService:
    """Git 명령어 실행을 추상화한 서비스 클래스"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        self.is_windows = platform.system() == "Windows"
        self._validate_git_repo()
    
    def _validate_git_repo(self) -> None:
        """Git 저장소 유효성 검증"""
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            raise ValueError(f"{self.repo_path} is not a valid git repository")
    
    def _execute(self, cmd: List[str], **kwargs) -> subprocess.CompletedProcess:
        """
        Git 명령어 실행 (플랫폼 독립적)
        
        Args:
            cmd: 실행할 명령어 리스트 (예: ['git', 'status'])
            **kwargs: subprocess.run에 전달할 추가 옵션
        
        Returns:
            subprocess.CompletedProcess 객체
        """
        # 기본 옵션 설정
        default_kwargs = {
            'capture_output': True,
            'text': True,
            'cwd': str(self.repo_path),
            'encoding': 'utf-8',
            'errors': 'ignore'
        }
        
        # Windows에서는 shell=True 사용
        if self.is_windows:
            default_kwargs['shell'] = True
        
        # 사용자 옵션으로 덮어쓰기
        default_kwargs.update(kwargs)
        
        try:
            result = subprocess.run(cmd, **default_kwargs)
            return result
        except Exception as e:
            # 상세한 오류 정보 포함
            raise RuntimeError(f"Git command failed: {' '.join(cmd)}\nError: {str(e)}")
    
    def status(self, short: bool = False) -> Dict[str, any]:
        """Git 상태 확인"""
        cmd = ['git', 'status']
        if short:
            cmd.append('-s')
        
        result = self._execute(cmd)
        
        if result.returncode != 0:
            raise RuntimeError(f"git status failed: {result.stderr}")
        
        # 결과 파싱
        if short:
            lines = result.stdout.strip().split('\n') if result.stdout else []
            modified = []
            untracked = []
            
            for line in lines:
                if line.startswith(' M'):
                    modified.append(line[3:])
                elif line.startswith('??'):
                    untracked.append(line[3:])
            
            return {
                'modified': modified,
                'untracked': untracked,
                'branch': self.get_current_branch()
            }
        
        return {'output': result.stdout}
    
    def get_current_branch(self) -> str:
        """현재 브랜치 이름 가져오기"""
        result = self._execute(['git', 'branch', '--show-current'])
        return result.stdout.strip() if result.returncode == 0 else 'unknown'
    
    def add(self, files: Optional[List[str]] = None) -> bool:
        """파일 스테이징"""
        cmd = ['git', 'add']
        
        if files:
            cmd.extend(files)
        else:
            cmd.append('-A')  # 모든 파일
        
        result = self._execute(cmd)
        return result.returncode == 0
    
    def commit(self, message: str) -> bool:
        """
        커밋 실행 (인코딩 안전)
        
        Args:
            message: 커밋 메시지
        
        Returns:
            성공 여부
        """
        # 인코딩 문제 방지를 위해 임시 파일 사용
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', 
                                        suffix='.txt', delete=False) as f:
            f.write(message)
            temp_file = f.name
        
        try:
            result = self._execute(['git', 'commit', '-F', temp_file])
            return result.returncode == 0
        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def push(self, remote: str = 'origin', branch: Optional[str] = None) -> Tuple[bool, str]:
        """
        원격 저장소로 푸시
        
        Args:
            remote: 원격 저장소 이름
            branch: 브랜치 이름 (None이면 현재 브랜치)
        
        Returns:
            (성공여부, 출력메시지) 튜플
        """
        if branch is None:
            branch = self.get_current_branch()
        
        result = self._execute(['git', 'push', remote, branch])
        
        # Git은 종종 정보를 stderr로 출력
        output = result.stdout + result.stderr
        
        return (result.returncode == 0, output)
    
    def fetch(self, remote: str = 'origin') -> bool:
        """원격 저장소에서 가져오기"""
        result = self._execute(['git', 'fetch', remote])
        return result.returncode == 0
    
    def log(self, n: int = 5, oneline: bool = True) -> List[str]:
        """커밋 로그 조회"""
        cmd = ['git', 'log']
        
        if oneline:
            cmd.append('--oneline')
        
        cmd.extend(['-n', str(n)])
        
        result = self._execute(cmd)
        
        if result.returncode != 0:
            return []
        
        return result.stdout.strip().split('\n') if result.stdout else []
    
    def get_remote_url(self, remote: str = 'origin') -> Optional[str]:
        """원격 저장소 URL 가져오기"""
        result = self._execute(['git', 'remote', 'get-url', remote])
        return result.stdout.strip() if result.returncode == 0 else None


# 싱글톤 인스턴스
_git_service = None

def get_git_service(repo_path: str = ".") -> GitService:
    """GitService 싱글톤 인스턴스 반환"""
    global _git_service
    if _git_service is None:
        _git_service = GitService(repo_path)
    return _git_service
