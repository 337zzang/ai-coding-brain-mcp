#!/usr/bin/env python3
"""
보안이 강화된 GitHub 유틸리티
- 커맨드 인젝션 방지
- 강화된 오류 처리
- 토큰 보안 관리
"""

import os
import re
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from urllib.parse import urlparse

# 로깅 설정
logger = logging.getLogger(__name__)

# 상수 정의
GITHUB_API_BASE = "https://api.github.com"
VALID_GITHUB_URL_PATTERN = re.compile(
    r'^https?://github\.com/[\w\-]+/[\w\-\.]+(?:\.git)?$'
)


class GitHubSecurityError(Exception):
    """GitHub 보안 관련 예외"""
    pass


class GitHubUtils:
    """보안이 강화된 GitHub 유틸리티 클래스"""
    
    def __init__(self):
        self.token = self._get_github_token()
    
    def _get_github_token(self) -> Optional[str]:
        """환경 변수에서 GitHub 토큰을 안전하게 가져옴"""
        token = os.environ.get('GITHUB_TOKEN')
        if token:
            # 토큰이 로그에 노출되지 않도록 마스킹
            masked_token = token[:4] + '*' * (len(token) - 8) + token[-4:]
            logger.debug(f"GitHub token loaded: {masked_token}")
        return token
    
    def validate_github_url(self, url: str) -> bool:
        """GitHub URL 유효성 검증"""
        if not url or not isinstance(url, str):
            return False
        
        # URL 패턴 검증
        if not VALID_GITHUB_URL_PATTERN.match(url):
            logger.warning(f"Invalid GitHub URL pattern: {url}")
            return False
        
        # 추가 보안 검증: 특수 문자 체크
        dangerous_chars = [';', '&&', '||', '`', '$', '(', ')', '{', '}', '<', '>', '|', '&']
        if any(char in url for char in dangerous_chars):
            logger.error(f"Dangerous characters detected in URL: {url}")
            raise GitHubSecurityError(f"URL contains potentially dangerous characters")
        
        return True
    
    def get_github_repo_info(self, repo_url: str) -> Tuple[str, str]:
        """GitHub 저장소 URL에서 소유자와 저장소 이름 추출"""
        if not self.validate_github_url(repo_url):
            raise ValueError(f"Invalid GitHub URL: {repo_url}")
        
        # URL 파싱
        parsed = urlparse(repo_url)
        path_parts = parsed.path.strip('/').split('/')
        
        if len(path_parts) < 2:
            raise ValueError(f"Cannot extract owner/repo from URL: {repo_url}")
        
        owner = path_parts[0]
        repo = path_parts[1].replace('.git', '')
        
        return owner, repo
    
    def clone_github_repo(self, repo_url: str, local_path: Optional[str] = None) -> Dict[str, Any]:
        """안전하게 GitHub 저장소 복제"""
        # URL 검증
        if not self.validate_github_url(repo_url):
            raise ValueError(f"Invalid GitHub URL: {repo_url}")
        
        # 로컬 경로 설정 및 검증
        if local_path is None:
            owner, repo = self.get_github_repo_info(repo_url)
            local_path = os.path.join("repos", owner, repo)
        
        # 경로 정규화 및 검증
        local_path = os.path.abspath(local_path)
        
        # 이미 존재하는 디렉토리인지 확인
        if os.path.exists(local_path):
            return {
                'success': False,
                'error': f"Directory already exists: {local_path}",
                'path': local_path
            }
        
        # 부모 디렉토리 생성
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        try:
            # 안전한 subprocess 호출 (리스트 형태로 인자 전달)
            result = subprocess.run(
                ['git', 'clone', repo_url, local_path],
                capture_output=True,
                text=True,
                timeout=300,  # 5분 타임아웃
                check=True
            )
            
            logger.info(f"Successfully cloned {repo_url} to {local_path}")
            return {
                'success': True,
                'path': local_path,
                'message': f"Repository cloned successfully"
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout while cloning {repo_url}")
            return {
                'success': False,
                'error': "Clone operation timed out after 5 minutes",
                'path': local_path
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Git clone failed: {e.stderr}")
            return {
                'success': False,
                'error': f"Git clone failed: {e.stderr}",
                'path': local_path
            }
        except Exception as e:
            logger.error(f"Unexpected error during clone: {str(e)}")
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}",
                'path': local_path
            }
    
    def create_github_issue(self, repo_url: str, title: str, body: str) -> Dict[str, Any]:
        """GitHub 이슈 생성 (구현 예정)"""
        # URL 검증
        if not self.validate_github_url(repo_url):
            raise ValueError(f"Invalid GitHub URL: {repo_url}")
        
        if not self.token:
            return {
                'success': False,
                'error': "GitHub token not found in environment variables"
            }
        
        # 제목과 본문 검증
        if not title or len(title.strip()) == 0:
            return {
                'success': False,
                'error': "Issue title cannot be empty"
            }
        
        if len(title) > 256:
            return {
                'success': False,
                'error': "Issue title too long (max 256 characters)"
            }
        
        try:
            import requests
            
            owner, repo = self.get_github_repo_info(repo_url)
            api_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues"
            
            headers = {
                'Authorization': f'token {self.token}',
                'Accept': 'application/vnd.github.v3+json',
                'Content-Type': 'application/json'
            }
            
            data = {
                'title': title.strip(),
                'body': body.strip() if body else ''
            }
            
            response = requests.post(
                api_url,
                json=data,
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            
            issue_data = response.json()
            return {
                'success': True,
                'issue_number': issue_data.get('number'),
                'issue_url': issue_data.get('html_url'),
                'message': f"Issue #{issue_data.get('number')} created successfully"
            }
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                error_msg = "Authentication failed. Please check your GitHub token"
            elif e.response.status_code == 404:
                error_msg = "Repository not found or you don't have access"
            else:
                error_msg = f"HTTP error {e.response.status_code}: {e.response.text}"
            
            logger.error(f"GitHub API error: {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
            
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': "Request timed out after 30 seconds"
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return {
                'success': False,
                'error': f"Network error: {str(e)}"
            }
            
        except ImportError:
            return {
                'success': False,
                'error': "requests library not installed"
            }


# 싱글톤 인스턴스
_github_utils = None

def get_github_utils() -> GitHubUtils:
    """GitHubUtils 싱글톤 인스턴스 반환"""
    global _github_utils
    if _github_utils is None:
        _github_utils = GitHubUtils()
    return _github_utils
