"""
Git 서비스 통합 테스트
"""
import pytest
from core.git_service import GitService, get_git_service
from git_version_manager import get_git_manager


def test_git_service_initialization():
    """Git 서비스 초기화 테스트"""
    git = get_git_service()
    assert git is not None
    assert isinstance(git, GitService)


def test_git_status():
    """Git 상태 확인 테스트"""
    git = get_git_service()
    status = git.status(short=True)
    
    assert 'branch' in status
    assert 'modified' in status
    assert 'untracked' in status
    assert isinstance(status['modified'], list)
    assert isinstance(status['untracked'], list)


def test_git_current_branch():
    """현재 브랜치 확인 테스트"""
    git = get_git_service()
    branch = git.get_current_branch()
    
    assert branch is not None
    assert len(branch) > 0
    assert branch != 'unknown'


def test_git_remote_url():
    """원격 저장소 URL 확인 테스트"""
    git = get_git_service()
    url = git.get_remote_url()
    
    assert url is not None
    assert 'github.com' in url


def test_git_manager_integration():
    """GitVersionManager 통합 테스트"""
    manager = get_git_manager()
    
    # 상태 확인
    status = manager.git_status()
    assert 'branch' in status
    
    # 최근 커밋 조회
    commits = manager.get_recent_commits(3)
    assert isinstance(commits, list)


if __name__ == "__main__":
    # 직접 실행 시 간단한 테스트
    print("Git 서비스 통합 테스트 시작...")
    
    try:
        test_git_service_initialization()
        print("✅ 초기화 테스트 통과")
        
        test_git_status()
        print("✅ 상태 확인 테스트 통과")
        
        test_git_current_branch()
        print("✅ 브랜치 확인 테스트 통과")
        
        test_git_remote_url()
        print("✅ 원격 저장소 테스트 통과")
        
        test_git_manager_integration()
        print("✅ GitManager 통합 테스트 통과")
        
        print("\n🎉 모든 테스트 통과!")
        
    except AssertionError as e:
        print(f"❌ 테스트 실패: {e}")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
