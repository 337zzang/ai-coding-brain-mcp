#!/usr/bin/env python
"""들여쓰기 테스트 실행"""
import subprocess
import sys

print("🧪 들여쓰기 오류 처리 테스트 실행\n")

# 테스트 실행
result = subprocess.run([
    sys.executable, "-m", "pytest", 
    "python/test_indentation_handling.py", 
    "-v", "--tb=short"
], capture_output=True, text=True)

print(result.stdout)
if result.stderr:
    print("오류:", result.stderr)

# 간단한 단위 테스트도 실행
print("\n단위 테스트 실행:")
result = subprocess.run([
    sys.executable, 
    "python/test_indentation_handling.py"
], capture_output=True, text=True)

print(result.stdout)
