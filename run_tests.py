#!/usr/bin/env python
"""테스트 실행 스크립트"""
import subprocess
import sys

print("🧪 테스트 실행 중...")
result = subprocess.run([sys.executable, "-m", "pytest", "test/", "-v"], 
                       capture_output=True, text=True)

print(result.stdout)
if result.stderr:
    print(result.stderr)

if result.returncode == 0:
    print("\n✅ 모든 테스트 통과!")
else:
    print("\n❌ 테스트 실패!")
    sys.exit(1)
