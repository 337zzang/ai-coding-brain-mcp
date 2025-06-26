#!/usr/bin/env python
"""
AI Coding Brain - 테스트 실행 스크립트
"""
import subprocess
import sys
import os

def run_tests():
    """모든 테스트 실행"""
    print("🧪 AI Coding Brain 테스트 실행")
    print("=" * 50)
    
    # pytest가 설치되어 있는지 확인
    try:
        import pytest
    except ImportError:
        print("❌ pytest가 설치되어 있지 않습니다.")
        print("   pip install pytest 를 실행해주세요.")
        return False
    
    # 테스트 실행
    test_args = [
        '-v',  # verbose
        '--tb=short',  # 짧은 traceback
        'test/',  # 테스트 디렉토리
    ]
    
    # 커버리지 옵션 (pytest-cov 필요)
    try:
        import pytest_cov
        test_args.extend(['--cov=python', '--cov-report=term-missing'])
    except ImportError:
        print("💡 커버리지 측정을 위해 pytest-cov 설치를 권장합니다.")
    
    result = pytest.main(test_args)
    
    if result == 0:
        print("\n✅ 모든 테스트 통과!")
    else:
        print(f"\n❌ 테스트 실패 (코드: {result})")
    
    return result == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
