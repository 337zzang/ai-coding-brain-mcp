"""
GitHub MCP를 사용한 백업 기능 구현
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List

class GitHubBackupManager:
    """GitHub MCP를 사용한 백업 관리자"""
    
    def __init__(self, owner: str = "337zzang", repo: str = "ai-coding-brain-mcp"):
        self.owner = owner
        self.repo = repo
        self.branch = "main"
        
    def backup_file(self, file_path: str, reason: str = "backup") -> Dict[str, Any]:
        """
        파일을 GitHub에 백업 (커밋)
        
        Args:
            file_path: 백업할 파일 경로
            reason: 백업 이유
            
        Returns:
            Dict: 백업 결과 정보
        """
        try:
            # 파일 내용 읽기
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 커밋 메시지 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = os.path.basename(file_path)
            commit_message = f"[Backup] {file_name} - {reason} ({timestamp})"
            
            # GitHub MCP 호출을 위한 정보 반환
            return {
                "success": True,
                "action": "github:create_or_update_file",
                "params": {
                    "owner": self.owner,
                    "repo": self.repo,
                    "path": file_path,
                    "content": content,
                    "message": commit_message,
                    "branch": self.branch
                },
                "backup_info": {
                    "file": file_path,
                    "reason": reason,
                    "timestamp": timestamp,
                    "message": commit_message
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def restore_backup(self, file_path: str, commit_sha: Optional[str] = None) -> Dict[str, Any]:
        """
        GitHub에서 파일 복원
        
        Args:
            file_path: 복원할 파일 경로
            commit_sha: 특정 커밋 SHA (없으면 최신)
            
        Returns:
            Dict: 복원 정보
        """
        return {
            "success": True,
            "action": "github:get_file_contents",
            "params": {
                "owner": self.owner,
                "repo": self.repo,
                "path": file_path,
                "ref": commit_sha or self.branch
            },
            "restore_info": {
                "file": file_path,
                "from_commit": commit_sha or "latest"
            }
        }
    
    def list_backups(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        백업 목록 조회 (커밋 히스토리)
        
        Args:
            file_path: 특정 파일의 백업만 조회
            
        Returns:
            Dict: 백업 목록 조회 정보
        """
        params = {
            "owner": self.owner,
            "repo": self.repo,
            "sha": self.branch
        }
        
        if file_path:
            params["path"] = file_path
            
        return {
            "success": True,
            "action": "github:list_commits",
            "params": params,
            "info": "Use GitHub web interface for detailed history"
        }

# 싱글톤 인스턴스
_github_backup = GitHubBackupManager()

def get_github_backup_manager() -> GitHubBackupManager:
    """GitHub 백업 관리자 싱글톤 인스턴스"""
    return _github_backup
