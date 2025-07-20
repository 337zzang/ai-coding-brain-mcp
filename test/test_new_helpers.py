
# 새 모듈 테스트
import sys
sys.path.insert(0, '.')
import ai_helpers_new as h

# 파일 쓰기
result = h.w('test_new.txt', 'Hello, simplified world!')
print(f"Write: {result}")

# 파일 읽기
result = h.r('test_new.txt')
print(f"Read: {result}")

# JSON 테스트
data = {'name': 'test', 'version': '2.0'}
result = h.wj('test_new.json', data)
print(f"Write JSON: {result}")

result = h.rj('test_new.json')
print(f"Read JSON: {result}")

# 정리
import os
os.remove('test_new.txt')
os.remove('test_new.json')
