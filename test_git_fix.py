import os
import sys
import subprocess

# Git 직접 테스트
print("=== Git 직접 테스트 ===")
try:
    result = subprocess.run(['git', '--version'], capture_output=True, text=True)
    print(f"Git 버전: {result.stdout}")
    print(f"리턴 코드: {result.returncode}")
except Exception as e:
    print(f"오류: {e}")

# 수정된 git_ops 테스트
print("\n=== 수정된 git_ops 테스트 ===")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'python'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'python', 'ai_helpers_v2'))

try:
    from python.ai_helpers_v2 import git_ops
    
    # Git 찾기 테스트
    git_exe = git_ops.find_git_executable()
    print(f"찾은 Git 경로: {git_exe}")
    
    # git_status 테스트
    result = git_ops.git_status()
    print(f"\ngit_status 결과:")
    print(f"- 성공: {result.get('success')}")
    print(f"- 메시지: {result.get('stderr') if not result.get('success') else 'OK'}")
    
    if result.get('success'):
        print("\n✅ Git 기능이 정상 작동합니다!")
    else:
        print("\n❌ Git 기능 오류")
        
except Exception as e:
    print(f"모듈 로드 오류: {e}")
    import traceback
    traceback.print_exc()
