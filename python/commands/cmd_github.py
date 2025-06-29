#!/usr/bin/env python3
"""
MCP GitHub 도구 - 보안이 강화된 GitHub 작업 명령어
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# 프로젝트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.github_utils_secure import get_github_utils, GitHubSecurityError
from core.error_handler import StandardResponse, ErrorType


def cmd_github_clone(repo_url: str, local_path: Optional[str] = None) -> StandardResponse:
    """GitHub 저장소를 안전하게 복제
    
    Args:
        repo_url: GitHub 저장소 URL
        local_path: 로컬 저장 경로 (선택사항)
        
    Returns:
        StandardResponse: 작업 결과
    """
    try:
        github_utils = get_github_utils()
        
        # 저장소 복제
        result = github_utils.clone_github_repo(repo_url, local_path)
        
        if result['success']:
            print(f"✅ 저장소 복제 완료: {result['path']}")
            return StandardResponse.success(result)
        else:
            print(f"❌ 복제 실패: {result['error']}")
            return StandardResponse.error(
                ErrorType.EXTERNAL_SERVICE_ERROR,
                result['error']
            )
            
    except GitHubSecurityError as e:
        print(f"🔒 보안 오류: {str(e)}")
        return StandardResponse.error(
            ErrorType.VALIDATION_ERROR,
            f"보안 검증 실패: {str(e)}"
        )
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {str(e)}")
        return StandardResponse.error(
            ErrorType.UNKNOWN_ERROR,
            f"저장소 복제 중 오류 발생: {str(e)}"
        )


def cmd_github_create_issue(
    repo_url: str,
    title: str,
    body: Optional[str] = None
) -> StandardResponse:
    """GitHub 저장소에 이슈 생성
    
    Args:
        repo_url: GitHub 저장소 URL
        title: 이슈 제목
        body: 이슈 본문 (선택사항)
        
    Returns:
        StandardResponse: 작업 결과
    """
    try:
        github_utils = get_github_utils()
        
        # 이슈 생성
        result = github_utils.create_github_issue(
            repo_url, 
            title, 
            body or ""
        )
        
        if result['success']:
            print(f"✅ 이슈 생성 완료: {result.get('issue_url', 'N/A')}")
            return StandardResponse.success(result)
        else:
            print(f"❌ 이슈 생성 실패: {result['error']}")
            return StandardResponse.error(
                ErrorType.EXTERNAL_SERVICE_ERROR,
                result['error']
            )
            
    except GitHubSecurityError as e:
        print(f"🔒 보안 오류: {str(e)}")
        return StandardResponse.error(
            ErrorType.VALIDATION_ERROR,
            f"보안 검증 실패: {str(e)}"
        )
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {str(e)}")
        return StandardResponse.error(
            ErrorType.UNKNOWN_ERROR,
            f"이슈 생성 중 오류 발생: {str(e)}"
        )


def cmd_github_validate_url(repo_url: str) -> StandardResponse:
    """GitHub URL 유효성 검증
    
    Args:
        repo_url: 검증할 GitHub URL
        
    Returns:
        StandardResponse: 검증 결과
    """
    try:
        github_utils = get_github_utils()
        
        is_valid = github_utils.validate_github_url(repo_url)
        
        if is_valid:
            owner, repo = github_utils.get_github_repo_info(repo_url)
            print(f"✅ 유효한 GitHub URL: {owner}/{repo}")
            return StandardResponse.success({
                'valid': True,
                'owner': owner,
                'repo': repo,
                'url': repo_url
            })
        else:
            print(f"❌ 유효하지 않은 GitHub URL: {repo_url}")
            return StandardResponse.success({
                'valid': False,
                'url': repo_url,
                'message': "Invalid GitHub URL format"
            })
            
    except Exception as e:
        print(f"❌ URL 검증 중 오류: {str(e)}")
        return StandardResponse.error(
            ErrorType.VALIDATION_ERROR,
            f"URL 검증 실패: {str(e)}"
        )


# 명령줄 인터페이스
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="GitHub 도구 명령어")
    subparsers = parser.add_subparsers(dest='command', help='사용 가능한 명령어')
    
    # clone 명령어
    clone_parser = subparsers.add_parser('clone', help='저장소 복제')
    clone_parser.add_argument('repo_url', help='GitHub 저장소 URL')
    clone_parser.add_argument('--path', help='로컬 경로', default=None)
    
    # issue 명령어
    issue_parser = subparsers.add_parser('issue', help='이슈 생성')
    issue_parser.add_argument('repo_url', help='GitHub 저장소 URL')
    issue_parser.add_argument('title', help='이슈 제목')
    issue_parser.add_argument('--body', help='이슈 본문', default='')
    
    # validate 명령어
    validate_parser = subparsers.add_parser('validate', help='URL 검증')
    validate_parser.add_argument('repo_url', help='검증할 URL')
    
    args = parser.parse_args()
    
    if args.command == 'clone':
        cmd_github_clone(args.repo_url, args.path)
    elif args.command == 'issue':
        cmd_github_create_issue(args.repo_url, args.title, args.body)
    elif args.command == 'validate':
        cmd_github_validate_url(args.repo_url)
    else:
        parser.print_help()
