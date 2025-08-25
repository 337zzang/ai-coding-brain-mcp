"""
비블로킹 버전의 JSON REPL 세션
타임아웃과 함께 입력을 대기하여 Claude Code에서도 작동
"""

import sys
import json
import select
import time
import os

def check_stdin_with_timeout(timeout=0.1):
    """stdin에서 입력 가능한지 확인 (타임아웃 포함)"""
    if sys.platform == 'win32':
        # Windows에서는 select가 파일에 작동하지 않음
        # 대신 threading 사용
        import threading
        import queue
        
        q = queue.Queue()
        
        def read_input():
            try:
                line = sys.stdin.readline()
                q.put(line)
            except:
                q.put(None)
        
        thread = threading.Thread(target=read_input)
        thread.daemon = True
        thread.start()
        
        try:
            return q.get(timeout=timeout)
        except queue.Empty:
            return None
    else:
        # Unix/Linux에서는 select 사용
        if select.select([sys.stdin], [], [], timeout)[0]:
            return sys.stdin.readline()
        return None

def run_nonblocking_repl(process_func, max_idle_time=60):
    """
    비블로킹 REPL 실행
    
    Args:
        process_func: 요청 처리 함수
        max_idle_time: 최대 대기 시간 (초)
    """
    print("비블로킹 REPL 시작...", file=sys.stderr)
    idle_time = 0
    
    while idle_time < max_idle_time:
        line = check_stdin_with_timeout(0.5)
        
        if line:
            idle_time = 0  # 입력 받으면 idle 시간 리셋
            try:
                request = json.loads(line.strip())
                response = process_func(request)
                print(json.dumps(response, ensure_ascii=False))
                sys.stdout.flush()
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
        else:
            idle_time += 0.5
            # 주기적으로 상태 체크 가능
            if int(idle_time) % 10 == 0 and idle_time > 0:
                print(f"Idle for {int(idle_time)} seconds...", file=sys.stderr)
    
    print(f"Max idle time ({max_idle_time}s) reached. Exiting.", file=sys.stderr)

# Claude Code 환경에서 사용 예시
if __name__ == "__main__":
    # 기존 process_json_request 함수를 import하거나 정의
    from json_repl_session import process_json_request
    
    # Claude Code 모드일 때는 짧은 타임아웃
    if os.environ.get('CLAUDE_CODE_ENV'):
        run_nonblocking_repl(process_json_request, max_idle_time=5)
    else:
        run_nonblocking_repl(process_json_request, max_idle_time=3600)