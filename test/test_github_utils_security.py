#!/usr/bin/env python3
"""
GitHub 유틸리티 보안 테스트
"""

import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# 프로젝트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.github_utils_secure import GitHubUtils, GitHubSecurityError


class TestGitHubUtilsSecurity(unittest.TestCase):
    """GitHub 유틸리티 보안 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.github_utils = GitHubUtils()
    
    def test_command_injection_prevention(self):
        """커맨드 인젝션 방지 테스트"""
        # 악의적인 URL 패턴들
        malicious_urls = [
            "https://github.com/user/repo; rm -rf /",
            "https://github.com/user/repo && echo hacked",
            "https://github.com/user/repo || whoami",
            "https://github.com/user/repo`whoami`",
            "https://github.com/user/repo$(whoami)",
            "https://github.com/user/repo | cat /etc/passwd",
            "https://github.com/user/repo > /tmp/evil.sh",
            "https://github.com/user/repo < /etc/passwd",
        ]
        
        for url in malicious_urls:
            with self.subTest(url=url):
                # URL 검증이 실패하거나 보안 예외가 발생해야 함
                try:
                    result = self.github_utils.validate_github_url(url)
                    if result:
                        # validate_github_url이 True를 반환했다면 clone 시도
                        with self.assertRaises((ValueError, GitHubSecurityError)):
                            self.github_utils.clone_github_repo(url)
                except GitHubSecurityError:
                    # 보안 예외가 발생하면 테스트 통과
                    pass
    
    def test_valid_github_urls(self):
        """정상적인 GitHub URL 검증 테스트"""
        valid_urls = [
            "https://github.com/user/repo",
            "https://github.com/user/repo.git",
            "https://github.com/user-name/repo-name",
            "https://github.com/org123/project.name.git",
            "http://github.com/user/repo",
        ]
        
        for url in valid_urls:
            with self.subTest(url=url):
                result = self.github_utils.validate_github_url(url)
                self.assertTrue(result, f"Valid URL rejected: {url}")
    
    def test_invalid_github_urls(self):
        """잘못된 GitHub URL 검증 테스트"""
        invalid_urls = [
            "https://gitlab.com/user/repo",  # 다른 서비스
            "https://github.com/user",  # 저장소 이름 없음
            "https://github.com/",  # 경로 없음
            "ftp://github.com/user/repo",  # 잘못된 프로토콜
            "github.com/user/repo",  # 프로토콜 없음
            "",  # 빈 문자열
            None,  # None 값
        ]
        
        for url in invalid_urls:
            with self.subTest(url=url):
                result = self.github_utils.validate_github_url(url)
                self.assertFalse(result, f"Invalid URL accepted: {url}")
    
    def test_token_masking(self):
        """토큰 마스킹 테스트"""
        # 환경 변수에 테스트 토큰 설정
        test_token = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"
        with patch.dict(os.environ, {"GITHUB_TOKEN": test_token}):
            utils = GitHubUtils()
            # 토큰이 로드되었는지 확인
            self.assertEqual(utils.token, test_token)
            
            # 로그에서 토큰이 마스킹되는지는 로그 캡처로 확인 가능
    
    @patch('subprocess.run')
    def test_clone_with_timeout(self, mock_run):
        """타임아웃 처리 테스트"""
        # subprocess.run이 TimeoutExpired를 발생시키도록 설정
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=['git', 'clone'], 
            timeout=300
        )
        
        result = self.github_utils.clone_github_repo("https://github.com/user/repo")
        
        self.assertFalse(result['success'])
        self.assertIn('timed out', result['error'].lower())
    
    @patch('subprocess.run')
    def test_clone_error_handling(self, mock_run):
        """Git clone 오류 처리 테스트"""
        # Git 오류 시뮬레이션
        import subprocess
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=128,
            cmd=['git', 'clone'],
            stderr="fatal: repository not found"
        )
        
        result = self.github_utils.clone_github_repo("https://github.com/user/repo")
        
        self.assertFalse(result['success'])
        self.assertIn('repository not found', result['error'].lower())
    
    def test_empty_issue_title_validation(self):
        """빈 이슈 제목 검증 테스트"""
        result = self.github_utils.create_github_issue(
            "https://github.com/user/repo",
            "",  # 빈 제목
            "Issue body"
        )
        
        self.assertFalse(result['success'])
        self.assertIn('empty', result['error'].lower())
    
    def test_long_issue_title_validation(self):
        """너무 긴 이슈 제목 검증 테스트"""
        long_title = "A" * 300  # 300자
        result = self.github_utils.create_github_issue(
            "https://github.com/user/repo",
            long_title,
            "Issue body"
        )
        
        self.assertFalse(result['success'])
        self.assertIn('too long', result['error'].lower())


if __name__ == '__main__':
    unittest.main()
