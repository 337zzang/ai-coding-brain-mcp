#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
새 프로젝트 생성 테스트 스크립트
"""
import sys
import os
from pathlib import Path

# Python 경로 설정
current_dir = Path(__file__).parent.resolve()
python_dir = current_dir / 'python'
sys.path.insert(0, str(python_dir))

# enhanced_flow 모듈 import
from enhanced_flow import _create_new_project
from utils.path_utils import is_git_available

def test_create_project():
    """새 프로젝트 생성 테스트"""
    # 테스트 프로젝트 경로
    test_project_path = Path.home() / "Desktop" / "test-new-project-20250704"
    
    print(f"=== 새 프로젝트 생성 테스트 ===")
    print(f"프로젝트 경로: {test_project_path}")
    print(f"Git 사용 가능: {is_git_available()}")
    
    # 프로젝트 생성
    try:
        _create_new_project(test_project_path, init_git=True)
        print("\n[OK] 프로젝트 생성 완료!")
        
        # 생성된 파일 확인
        print("\n=== 생성된 파일 확인 ===")
        for item in test_project_path.rglob("*"):
            if item.is_file():
                print(f"[FILE] {item.relative_to(test_project_path)}")
            else:
                print(f"[DIR] {item.relative_to(test_project_path)}/")
                
        # Git 상태 확인
        if (test_project_path / ".git").exists():
            print("\n[OK] Git 저장소 초기화됨")
            # git log 확인
            import subprocess
            result = subprocess.run(
                ["git", "log", "--oneline", "-n", "1"],
                cwd=test_project_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"첫 커밋: {result.stdout.strip()}")
        else:
            print("\n[WARN]  Git 저장소가 초기화되지 않음")
            
    except Exception as e:
        print(f"\n[ERROR] 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_create_project()
