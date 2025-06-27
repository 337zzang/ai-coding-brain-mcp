#!/usr/bin/env python
"""
Git 기능 통합 테스트 스크립트
Git 관련 모든 기능을 테스트합니다.
"""

import os
import sys
from pathlib import Path

# Python 경로 설정
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from git_version_manager import GitVersionManager
from gitignore_manager import GitignoreManager

def test_git_features():
    """Git 기능 테스트"""
    print("🚀 Git 기능 통합 테스트\n")
    
    # 1. GitVersionManager 테스트
    print("=" * 50)
    print("1️⃣ GitVersionManager 테스트")
    print("=" * 50)
    
    git_manager = GitVersionManager()
    
    # Git 상태 확인
    print("\n📊 Git 상태 확인:")
    status = git_manager.git_status()
    print(f"  - 현재 브랜치: {status['branch']}")
    print(f"  - 수정된 파일: {len(status['modified'])}개")
    print(f"  - 추적되지 않은 파일: {len(status['untracked'])}개")
    print(f"  - 스테이징된 파일: {len(status['staged'])}개")
    
    # 최근 커밋 확인
    print("\n📝 최근 커밋:")
    try:
        # git log를 직접 실행
        import subprocess
        result = subprocess.run(
            ['git', 'log', '--oneline', '-3'],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                print(f"  - {line}")
    except Exception as e:
        print(f"  ❌ 커밋 로그 조회 실패: {e}")
    
    # 브랜치 목록
    print("\n🌿 브랜치 목록:")
    try:
        result = subprocess.run(
            ['git', 'branch', '-a'],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    print(f"  {line}")
    except Exception as e:
        print(f"  ❌ 브랜치 목록 조회 실패: {e}")
    
    # 2. GitignoreManager 테스트
    print("\n" + "=" * 50)
    print("2️⃣ GitignoreManager 테스트")
    print("=" * 50)
    
    gitignore_manager = GitignoreManager()
    
    # .gitignore 분석
    print("\n📄 .gitignore 분석:")
    suggestions = gitignore_manager.analyze_project()
    
    # 현재 .gitignore 내용 확인
    existing_patterns = gitignore_manager.read_gitignore()
    
    print(f"\n현재 .gitignore 패턴 수: {len(existing_patterns)}")
    print(f"제안된 추가 패턴 수: {sum(len(patterns) for patterns in suggestions.values())}")
    
    if suggestions:
        print("\n💡 제안 사항:")
        for category, patterns in suggestions.items():
            if patterns:
                print(f"\n  [{category}]")
                for pattern in patterns[:3]:  # 각 카테고리별로 최대 3개만 표시
                    print(f"    - {pattern}")
    
    # 3. 테스트용 변경사항 생성
    print("\n" + "=" * 50)
    print("3️⃣ 테스트용 변경사항 생성")
    print("=" * 50)
    
    test_file = "test_git_feature.txt"
    print(f"\n📝 테스트 파일 생성: {test_file}")
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("Git 테스트를 위한 임시 파일입니다.\n")
        f.write("이 파일은 Git 기능 테스트 후 삭제됩니다.\n")
    
    # 변경사항 확인
    print("\n📊 변경사항 확인:")
    status = git_manager.git_status()
    print(f"  - 수정된 파일: {status['modified']}")
    print(f"  - 추적되지 않은 파일: {status['untracked']}")
    
    # 4. Git 백업 테스트
    print("\n" + "=" * 50)
    print("4️⃣ Git 백업 기능 테스트")
    print("=" * 50)
    
    # Stash 테스트
    print("\n💾 Git Stash 테스트:")
    try:
        # 현재 변경사항 stash
        result = subprocess.run(
            ['git', 'stash', 'save', 'Git 기능 테스트 백업'],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        if result.returncode == 0:
            print("  ✅ Stash 저장 성공")
            
            # Stash 목록 확인
            result = subprocess.run(
                ['git', 'stash', 'list'],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            if result.stdout:
                print("  📋 Stash 목록:")
                for line in result.stdout.strip().split('\n')[:3]:
                    print(f"    - {line}")
            
            # Stash 복원
            result = subprocess.run(
                ['git', 'stash', 'pop'],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            if result.returncode == 0:
                print("  ✅ Stash 복원 성공")
    except Exception as e:
        print(f"  ❌ Stash 테스트 실패: {e}")
    
    # 5. 정리
    print("\n🧹 테스트 파일 정리...")
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"  ✅ {test_file} 삭제 완료")
    
    # 6. 최종 상태 확인
    print("\n" + "=" * 50)
    print("📊 최종 Git 상태")
    print("=" * 50)
    
    final_status = git_manager.git_status()
    print(f"  - 현재 브랜치: {final_status['branch']}")
    print(f"  - 작업 트리 상태: {'깨끗함' if not final_status['modified'] and not final_status['untracked'] else '변경사항 있음'}")
    
    print("\n✅ Git 기능 테스트 완료!")

if __name__ == "__main__":
    test_git_features()
