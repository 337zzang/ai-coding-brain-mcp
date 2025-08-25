#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🔧 JSON REPL Session 메모리 문제 긴급 패치
"""

import sys
import os
import json
import time
import gc
import threading
import signal
from typing import Dict, Any, Optional
from pathlib import Path

# 기존 모듈 import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from repl_core import EnhancedREPLSession, ExecutionMode

# 메모리 제한 설정
MAX_SHARED_VARS_SIZE = 100  # 최대 100개 변수
MAX_VAR_SIZE = 10 * 1024 * 1024  # 변수당 최대 10MB
EXECUTION_TIMEOUT = 30  # 30초 타임아웃

class MemoryLimitedPool:
    """메모리 제한이 있는 세션 풀"""

    def __init__(self):
        self.shared_variables = {}
        self.lock = threading.RLock()
        self.last_cleanup = time.time()

    def set_variable(self, key: str, value: Any):
        """메모리 제한을 적용한 변수 저장"""
        with self.lock:
            # 크기 체크
            import sys
            size = sys.getsizeof(value)
            if size > MAX_VAR_SIZE:
                raise MemoryError(f"Variable too large: {size} bytes")

            # 개수 제한
            if len(self.shared_variables) >= MAX_SHARED_VARS_SIZE:
                # 가장 오래된 변수 삭제
                oldest = min(self.shared_variables.keys())
                del self.shared_variables[oldest]
                gc.collect()

            self.shared_variables[key] = value

    def cleanup_if_needed(self):
        """주기적 메모리 정리"""
        current = time.time()
        if current - self.last_cleanup > 300:  # 5분마다
            with self.lock:
                # 큰 객체 정리
                for key in list(self.shared_variables.keys()):
                    if sys.getsizeof(self.shared_variables[key]) > MAX_VAR_SIZE / 2:
                        del self.shared_variables[key]
                gc.collect()
                self.last_cleanup = current

# 타임아웃 실행 함수
def execute_with_timeout(code: str, timeout: int = EXECUTION_TIMEOUT):
    """타임아웃이 있는 코드 실행"""
    import queue
    result_queue = queue.Queue()

    def worker():
        try:
            namespace = {}
            exec(code, namespace)
            result_queue.put(("success", namespace))
        except Exception as e:
            result_queue.put(("error", str(e)))

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        return {"error": f"Timeout after {timeout} seconds"}

    try:
        status, result = result_queue.get_nowait()
        return {"status": status, "result": result}
    except queue.Empty:
        return {"error": "No result"}

# 비블로킹 입력 읽기
def read_input_nonblocking(timeout: float = 1.0):
    """비블로킹 입력 읽기"""
    import select
    import sys

    if sys.platform == "win32":
        # Windows: threading 사용
        import queue
        import threading

        q = queue.Queue()
        def reader():
            try:
                line = sys.stdin.readline()
                q.put(line)
            except:
                q.put(None)

        t = threading.Thread(target=reader, daemon=True)
        t.start()

        try:
            return q.get(timeout=timeout)
        except queue.Empty:
            return None
    else:
        # Unix: select 사용
        ready, _, _ = select.select([sys.stdin], [], [], timeout)
        if ready:
            return sys.stdin.readline()
        return None

print("✅ 메모리 문제 패치 코드 준비 완료!")
