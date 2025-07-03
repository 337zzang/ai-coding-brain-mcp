"""
Git operations for AI Helpers - Simplified version using GitVersionManager
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# GitVersionManager 임포트
try:
    from git_version_manager import (
        GitVersionManager,
        git_status as _git_status,
        git_commit_smart as _git_commit_smart,
        git_stash_save as _git_stash_save,
        git_branch_smart as _git_branch_smart
    )
except ImportError:
    GitVersionManager = None
    _git_status = lambda path=None: {}
    _git_commit_smart = lambda msg, path=None: False
    _git_stash_save = lambda msg=None, path=None: False
    _git_branch_smart = lambda name, path=None: False

# 로깅
import logging
logger = logging.getLogger(__name__)


def git_status() -> Dict[str, Any]:
    """Git 상태 조회 - GitVersionManager 사용"""
    try:
        return _git_status()
    except Exception as e:
        logger.error(f"Git status error: {e}")
        return {
            'branch': 'unknown',
            'modified': [],
            'untracked': [],
            'staged': [],
            'clean': True
        }


def git_add(files: str = '.') -> bool:
    """파일 스테이징"""
    try:
        mgr = GitVersionManager()
        result = mgr.add(files)
        return result.get('ok', False)
    except Exception as e:
        logger.error(f"Git add error: {e}")
        return False


def git_commit(message: str) -> bool:
    """커밋 생성"""
    try:
        mgr = GitVersionManager()
        result = mgr.commit(message)
        return result.get('ok', False)
    except Exception as e:
        logger.error(f"Git commit error: {e}")
        return False


def git_commit_smart(message: str) -> bool:
    """스마트 커밋 - 변경사항이 있을 때만"""
    try:
        return _git_commit_smart(message)
    except Exception as e:
        logger.error(f"Git smart commit error: {e}")
        return False


def git_stash(message: Optional[str] = None) -> bool:
    """변경사항 stash"""
    try:
        return _git_stash_save(message)
    except Exception as e:
        logger.error(f"Git stash error: {e}")
        return False


def git_stash_pop() -> bool:
    """최근 stash 복원"""
    try:
        mgr = GitVersionManager()
        result = mgr.stash_pop()
        return result.get('ok', False)
    except Exception as e:
        logger.error(f"Git stash pop error: {e}")
        return False


def git_branch(branch_name: str = None) -> Any:
    """브랜치 조회 또는 생성"""
    try:
        mgr = GitVersionManager()
        if branch_name:
            # 브랜치 생성
            result = mgr.create_branch(branch_name)
            return result.get('ok', False)
        else:
            # 현재 브랜치 조회
            return mgr.get_current_branch()
    except Exception as e:
        logger.error(f"Git branch error: {e}")
        return "unknown" if not branch_name else False


def git_branch_smart(branch_name: str) -> bool:
    """브랜치 생성 및 전환"""
    try:
        return _git_branch_smart(branch_name)
    except Exception as e:
        logger.error(f"Git smart branch error: {e}")
        return False


def git_log(max_count: int = 10) -> List[Dict[str, Any]]:
    """커밋 로그 조회"""
    try:
        mgr = GitVersionManager()
        result = mgr.get_log(max_count)
        if result.get('ok'):
            return result.get('data', [])
        return []
    except Exception as e:
        logger.error(f"Git log error: {e}")
        return []


def git_push(remote: str = 'origin', branch: str = None) -> bool:
    """원격 저장소에 푸시 (구현 필요 시 추가)"""
    logger.warning("git_push is not implemented yet")
    return False


def git_rollback_smart(target: str = 'HEAD~1') -> bool:
    """스마트 롤백 (구현 필요 시 추가)"""
    logger.warning("git_rollback_smart is not implemented yet")
    return False


# Gitignore 관련 함수들
def read_gitignore() -> List[str]:
    """gitignore 파일 읽기"""
    gitignore_path = Path('.gitignore')
    if gitignore_path.exists():
        try:
            from utils import open_text
            with open_text(gitignore_path, 'r') as f:
                return [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except:
            pass
    return []


def update_gitignore(patterns: List[str]) -> bool:
    """gitignore 패턴 추가"""
    try:
        current = set(read_gitignore())
        new_patterns = set(patterns) - current
        
        if new_patterns:
            from utils import append_text
            content = '\n' + '\n'.join(sorted(new_patterns)) + '\n'
            append_text('.gitignore', content)
            logger.info(f"Added {len(new_patterns)} patterns to .gitignore")
            return True
        return False
    except Exception as e:
        logger.error(f"Update gitignore error: {e}")
        return False


def create_gitignore(template: str = 'python') -> bool:
    """gitignore 파일 생성"""
    templates = {
        'python': [
            '__pycache__/', '*.py[cod]', '*$py.class', '*.so',
            '.Python', 'env/', 'venv/', '.env', '.venv',
            '*.log', '.DS_Store', '.coverage', '.pytest_cache/',
            'dist/', 'build/', '*.egg-info/'
        ],
        'node': [
            'node_modules/', 'npm-debug.log*', 'yarn-debug.log*',
            'yarn-error.log*', '.npm', '.yarn-integrity'
        ]
    }
    
    patterns = templates.get(template, templates['python'])
    
    try:
        from utils import write_text
        content = '# Generated by AI Coding Brain\n\n'
        content += '\n'.join(patterns) + '\n'
        write_text('.gitignore', content)
        logger.info(f"Created .gitignore with {template} template")
        return True
    except Exception as e:
        logger.error(f"Create gitignore error: {e}")
        return False


# 프로젝트 분석 (간소화)
def analyze_project() -> Dict[str, Any]:
    """프로젝트 Git 상태 분석"""
    try:
        status = git_status()
        log = git_log(5)
        
        return {
            'status': status,
            'recent_commits': log,
            'has_changes': bool(status.get('modified') or status.get('untracked')),
            'branch': status.get('branch', 'unknown'),
            'is_clean': status.get('clean', True)
        }
    except Exception as e:
        logger.error(f"Project analysis error: {e}")
        return {
            'status': {},
            'recent_commits': [],
            'has_changes': False,
            'branch': 'unknown',
            'is_clean': True
        }


# GitignoreManager는 더 이상 필요하지 않음
def get_gitignore_manager():
    """Deprecated - use gitignore functions directly"""
    logger.warning("get_gitignore_manager is deprecated")
    return None