#!/usr/bin/env python
"""Git MCP 도구 직접 테스트"""

import os
import sys

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

try:
    # Git 관련 모듈 임포트
    from git_version_manager import GitVersionManager
    from gitignore_manager import GitignoreManager
    
    print("✅ 모듈 임포트 성공!")
    
    # Git 상태 테스트
    git_manager = GitVersionManager()
    status = git_manager.git_status()
    print(f"\n현재 브랜치: {status['branch']}")
    print(f"클린 상태: {status['clean']}")
    
    # Gitignore 테스트
    gitignore_manager = GitignoreManager()
    analysis = gitignore_manager.analyze_gitignore()
    print(f"\n.gitignore 카테고리 수: {len(analysis)}")
    
except Exception as e:
    print(f"❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
