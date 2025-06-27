#!/usr/bin/env python
"""
Git MCP 도구 테스트 스크립트
MCP의 Git 관련 도구들을 테스트합니다.
"""

import os
import sys
from pathlib import Path

# Python 경로 설정
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# MCP Git 도구들 import
from mcp_git_tools import (
    git_status,
    git_commit_smart,
    git_branch_smart,
    git_rollback_smart,
    git_push
)

from gitignore_manager import GitignoreManager

def test_mcp_git_tools():
    """MCP Git 도구 테스트"""
    print("🚀 MCP Git 도구 테스트\n")
    
    # 1. git_status 테스트
    print("=" * 50)
    print("1️⃣ git_status 테스트")
    print("=" * 50)
    
    try:
        status = git_status()
        print("\n✅ git_status 결과:")
        print(f"  - 현재 브랜치: {status.get('branch', 'N/A')}")
        print(f"  - 수정된 파일: {len(status.get('modified', []))}개")
        print(f"  - 추적되지 않은 파일: {len(status.get('untracked', []))}개")
        print(f"  - 스테이징된 파일: {len(status.get('staged', []))}개")
        
        if status.get('untracked'):
            print("\n  추적되지 않은 파일 목록:")
            for file in status['untracked'][:5]:  # 최대 5개만 표시
                print(f"    - {file}")
    except Exception as e:
        print(f"❌ git_status 실패: {e}")
    
    # 2. gitignore 분석 및 업데이트
    print("\n" + "=" * 50)
    print("2️⃣ gitignore 분석 및 업데이트")
    print("=" * 50)
    
    try:
        gitignore_manager = GitignoreManager()
        
        # 현재 .gitignore 읽기
        existing = gitignore_manager.read_gitignore()
        print(f"\n현재 .gitignore 패턴 수: {len(existing)}")
        
        # 제안사항 확인
        suggestions = gitignore_manager.analyze_project()
        total_suggestions = sum(len(patterns) for patterns in suggestions.values())
        print(f"제안된 패턴 수: {total_suggestions}")
        
        if suggestions:
            print("\n제안된 패턴 카테고리:")
            for category in suggestions.keys():
                print(f"  - {category}: {len(suggestions[category])}개")
    except Exception as e:
        print(f"❌ gitignore 분석 실패: {e}")
    
    # 3. 브랜치 관리 테스트
    print("\n" + "=" * 50)
    print("3️⃣ 브랜치 관리 기능")
    print("=" * 50)
    
    try:
        # 현재 브랜치 확인
        import subprocess
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        current_branch = result.stdout.strip()
        print(f"\n현재 브랜치: {current_branch}")
        
        # 모든 브랜치 목록
        result = subprocess.run(
            ['git', 'branch', '-a'],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        print("\n브랜치 목록:")
        for line in result.stdout.strip().split('\n'):
            print(f"  {line}")
    except Exception as e:
        print(f"❌ 브랜치 확인 실패: {e}")
    
    # 4. 커밋 로그 확인
    print("\n" + "=" * 50)
    print("4️⃣ 커밋 히스토리")
    print("=" * 50)
    
    try:
        result = subprocess.run(
            ['git', 'log', '--oneline', '-5', '--decorate', '--graph'],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        print("\n최근 5개 커밋:")
        print(result.stdout)
    except Exception as e:
        print(f"❌ 커밋 로그 확인 실패: {e}")
    
    # 5. 원격 저장소 정보
    print("\n" + "=" * 50)
    print("5️⃣ 원격 저장소 정보")
    print("=" * 50)
    
    try:
        result = subprocess.run(
            ['git', 'remote', '-v'],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        if result.stdout:
            print("\n원격 저장소:")
            print(result.stdout)
        else:
            print("\n원격 저장소가 설정되지 않았습니다.")
    except Exception as e:
        print(f"❌ 원격 저장소 확인 실패: {e}")
    
    print("\n✅ Git 도구 테스트 완료!")

if __name__ == "__main__":
    # 올바른 디렉토리에서 실행되는지 확인
    current_dir = os.getcwd()
    if "python" in current_dir:
        os.chdir("..")  # 프로젝트 루트로 이동
    
    print(f"📁 현재 디렉토리: {os.getcwd()}\n")
    test_mcp_git_tools()
