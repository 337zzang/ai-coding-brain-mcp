import sys
import os
import time

# python 디렉토리로 이동
os.chdir(r'C:\Users\82106\Desktop\ai-coding-brain-mcp\python')

# JSON REPL 실행
print("Starting JSON REPL test...")
os.system('echo {"jsonrpc":"2.0","id":1,"method":"execute","params":{"code":"print(123)"}} | python -u json_repl_session.py > test_output.txt 2>&1')

time.sleep(2)

# 결과 확인
print("\nReading output...")
with open('test_output.txt', 'r', encoding='utf-8') as f:
    content = f.read()
    print(content)

# JSON 응답 찾기
import json
for line in content.split('\n'):
    if line.strip() and line.startswith('{'):
        try:
            data = json.loads(line)
            print(f"\nJSON Response found: {json.dumps(data, indent=2)}")
        except:
            pass
