
import sys
print(f"Python 실행 파일: {sys.executable}")
print(f"Python 버전: {sys.version}")

# Git 테스트
try:
    from git_version_manager import GitVersionManager
    git_manager = GitVersionManager()
    status = git_manager.git_status()
    print(f"\nGit 상태 테스트 성공!")
    print(f"브랜치: {status['branch']}")
except Exception as e:
    print(f"Git 테스트 실패: {e}")
