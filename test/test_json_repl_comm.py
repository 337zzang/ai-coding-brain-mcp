#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for JSON REPL communication
"""

import subprocess
import json
import time
import sys
import os

def test_json_repl():
    """JSON REPL 통신 테스트"""
    print("== JSON REPL Communication Test ==")
    
    # JSON REPL 프로세스 시작
    proc = subprocess.Popen(
        [sys.executable, '-u', 'json_repl_session.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8',  # UTF-8 인코딩 명시
        bufsize=0,  # 버퍼링 비활성화
        env={**os.environ, 'PYTHONUNBUFFERED': '1'}
    )
    
    # __READY__ 신호 대기
    print("Waiting for __READY__ signal...")
    start_time = time.time()
    ready = False
    
    while time.time() - start_time < 5:
        line = proc.stdout.readline()
        print(f"  stdout: {line.strip()}")
        if '__READY__' in line:
            ready = True
            print("REPL is ready!")
            break
    
    # stderr 확인
    try:
        stderr_data = proc.stderr.read(1024)
        if stderr_data:
            print(f"  stderr: {stderr_data}")
    except:
        pass
    
    if not ready:
        print("ERROR: REPL initialization failed")
        proc.terminate()
        return
    
    # 테스트 요청 전송
    test_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "execute",
        "params": {
            "code": "print('Hello from test!')"
        }
    }
    
    print(f"Sending request: {json.dumps(test_request)}")
    proc.stdin.write(json.dumps(test_request) + '\n')
    proc.stdin.flush()
    
    # 응답 대기
    print("Waiting for response...")
    response_line = proc.stdout.readline()
    
    if response_line:
        print(f"Response received: {response_line.strip()}")
        try:
            response = json.loads(response_line)
            if response.get('result'):
                print("SUCCESS: Test passed!")
                result = response['result']
                print(f"  stdout: {result.get('stdout', '').strip()}")
                print(f"  success: {result.get('success')}")
            else:
                print("ERROR: No result in response")
        except json.JSONDecodeError as e:
            print(f"ERROR: JSON parsing failed: {e}")
    else:
        print("ERROR: No response (timeout)")
    
    # 프로세스 종료
    proc.terminate()
    proc.wait()
    print("Test completed")

if __name__ == '__main__':
    os.chdir(r'C:\Users\82106\Desktop\ai-coding-brain-mcp\python')
    test_json_repl()
