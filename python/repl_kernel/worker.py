#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Subprocess Worker - Windows 호환 버전
시니어 피드백 반영:
# 1. signal.alarm 제거 (Windows 비호환)
2. resource 모듈 제거 (Windows 비호환)
3. 상태 복구 제거 (MVP에서는 stateless restart)
4. AI helpers 자동 로드
"""
import sys
import json
import traceback
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
import os

class WorkerProcess:
    def __init__(self):
        self.globals = {'__builtins__': __builtins__}
        self.locals = {}
        self.setup_environment()

    def setup_environment(self):
        """실행 환경 초기화 - Windows 호환"""
        # 기본 imports
        exec("import sys\nimport os", self.globals, self.locals)

        # AI helpers 로드 시도
        try:
            # 시니어 조언: 헬퍼를 워커 환경에 주입
            exec("import ai_helpers_new as h; helpers = h", self.globals, self.locals)
            print("[OK] AI helpers loaded in worker", file=sys.stderr)
        except ImportError as e:
            print(f"[WARNING] Failed to load AI helpers: {e}", file=sys.stderr)
        except Exception as e:
            print(f"[ERROR] Unexpected error loading helpers: {e}", file=sys.stderr)

    def execute_code(self, code, timeout=None):
        """코드 실행 - 타임아웃은 Manager가 처리"""
        stdout_capture = StringIO()
        stderr_capture = StringIO()

        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, self.globals, self.locals)

            # 변수 정보 수집
            variables = self.get_variable_info()

            return {
                "success": True,
                "stdout": stdout_capture.getvalue(),
                "stderr": stderr_capture.getvalue(),
                "variables": variables
            }

        except Exception as e:
            return {
                "success": False,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc(),
                "stdout": stdout_capture.getvalue(),
                "stderr": stderr_capture.getvalue()
            }

    def get_variable_info(self):
        """현재 변수 정보 수집"""
        variables = {}
        for name, value in self.locals.items():
            if not name.startswith('_'):
                try:
                    variables[name] = {
                        "type": type(value).__name__,
                        "repr": repr(value)[:100]  # 처음 100자만
                    }
                except:
                    variables[name] = {
                        "type": type(value).__name__,
                        "repr": "[Cannot represent]"
                    }
        return variables

    def send_response(self, response):
        """응답 전송"""
        json_response = json.dumps(response, ensure_ascii=False)
        sys.stdout.write(json_response + '\n')
        sys.stdout.flush()

    def run(self):
        """메인 루프"""
        print("[OK] Worker started", file=sys.stderr)

        while True:
            try:
                # 요청 읽기
                line = sys.stdin.readline()
                if not line:
                    break

                request = json.loads(line.strip())
                request_id = request.get('id', 'unknown')
                request_type = request.get('type', 'execute')

                response = {"id": request_id}

                if request_type == 'execute':
                    code = request.get('code', '')
                    timeout = request.get('timeout')  # Manager가 처리
                    result = self.execute_code(code, timeout)
                    response.update(result)

                elif request_type == 'ping':
                    response.update({
                        "type": "pong",
                        "status": "alive"
                    })

                elif request_type == 'shutdown':
                    response.update({
                        "type": "shutdown_ack",
                        "status": "shutting_down"
                    })
                    self.send_response(response)
                    break

                self.send_response(response)

            except Exception as e:
                error_response = {
                    "id": request_id if 'request_id' in locals() else 'unknown',
                    "type": "error",
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
                self.send_response(error_response)

if __name__ == "__main__":
    # 시니어 조언: unbuffered mode
    worker = WorkerProcess()
    worker.run()
