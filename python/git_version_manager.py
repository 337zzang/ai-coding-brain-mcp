"""
Git Version Manager - GitService 기반으로 개선
자동 백업, 버전 관리, 브랜치 관리 기능 제공
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from core.git_service import get_git_service


class GitVersionManager:
    """Git 기반 버전 관리 및 백업 시스템"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.git_service = get_git_service(str(self.project_root))
        self.config_file = self.project_root / ".git" / "ai_brain_config.json"
        self._load_config()
    
    def _load_config(self) -> None:
        """설정 파일 로드"""
        self.config = {
            "auto_backup": True,
            "backup_interval": 300,  # 5분
            "branch_prefix": "work/",
            "last_backup": None
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    self.config.update(saved_config)
            except:
                pass
    
    def _save_config(self) -> None:
        """설정 파일 저장"""
        self.config_file.parent.mkdir(exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def git_status(self) -> Dict[str, any]:
        """Git 상태 확인"""
        try:
            return self.git_service.status(short=True)
        except Exception as e:
            print(f"⚠️ Git 상태 확인 실패: {e}")
            return {
                'branch': 'unknown',
                'modified': [],
                'untracked': []
            }
    
    def git_commit_smart(self, message: str = None) -> Dict[str, any]:
        """
        스마트 커밋 - 자동 메시지 생성 및 한글 지원
        
        Args:
            message: 커밋 메시지 (없으면 자동 생성)
        
        Returns:
            실행 결과
        """
        try:
            # 변경사항 확인
            status = self.git_status()
            
            if not status['modified'] and not status['untracked']:
                return {
                    'success': False,
                    'message': '커밋할 변경사항이 없습니다.'
                }
            
            # 메시지 자동 생성
            if not message:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
                file_count = len(status['modified']) + len(status['untracked'])
                message = f"자동 커밋: {file_count}개 파일 변경 ({timestamp})"
            
            # 모든 파일 스테이징
            self.git_service.add()
            
            # 커밋
            success = self.git_service.commit(message)
            
            if success:
                print(f"✅ 커밋 성공: {message}")
                self.config['last_backup'] = datetime.now().isoformat()
                self._save_config()
            
            return {
                'success': success,
                'message': message
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def git_branch_smart(self, branch_name: str = None) -> Dict[str, any]:
        """
        스마트 브랜치 생성
        
        Args:
            branch_name: 브랜치 이름 (없으면 자동 생성)
        
        Returns:
            실행 결과
        """
        try:
            if not branch_name:
                # 자동 브랜치 이름 생성
                timestamp = datetime.now().strftime('%Y%m%d_%H%M')
                branch_name = f"{self.config['branch_prefix']}{timestamp}"
            
            # 브랜치 생성 및 체크아웃
            result = self.git_service._execute(['git', 'checkout', '-b', branch_name])
            
            return {
                'success': result.returncode == 0,
                'branch': branch_name,
                'output': result.stdout + result.stderr
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def git_push(self, remote: str = 'origin', branch: str = None) -> Dict[str, any]:
        """안전한 Git Push"""
        try:
            success, output = self.git_service.push(remote, branch)
            
            return {
                'success': success,
                'output': output,
                'remote': remote,
                'branch': branch or self.git_service.get_current_branch()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def git_stash_save(self, message: str = None) -> Dict[str, any]:
        """작업 내용 임시 저장"""
        try:
            if not message:
                message = f"Auto stash: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            result = self.git_service._execute(['git', 'stash', 'save', message])
            
            return {
                'success': result.returncode == 0,
                'message': message,
                'output': result.stdout
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_recent_commits(self, n: int = 5) -> List[str]:
        """최근 커밋 조회"""
        return self.git_service.log(n=n, oneline=True)


# 전역 인스턴스
_git_manager = None

def get_git_manager() -> GitVersionManager:
    """GitVersionManager 싱글톤 인스턴스 반환"""
    global _git_manager
    if _git_manager is None:
        _git_manager = GitVersionManager()
    return _git_manager


# 기존 코드와의 호환성을 위한 전역 변수
git_manager = get_git_manager()
