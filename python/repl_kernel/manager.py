"""
Subprocess Worker Manager - Windows 호환
"""
import subprocess
import json
import threading
import queue
import time
import sys
import os
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger('WorkerManager')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class SubprocessWorkerManager:
    def __init__(self, worker_script_path: str = 'python/repl_kernel/worker.py'):
        self.worker_script_path = worker_script_path
        self.worker: Optional[subprocess.Popen] = None
        self.request_id = 0
        self.response_queue = queue.Queue()
        self.stderr_queue = queue.Queue()
        self.active_request = None
        self.start_worker()

    def start_worker(self):
        """워커 프로세스 시작"""
        if self.worker and self.worker.poll() is None:
            logger.info("Terminating existing worker...")
            self.worker.terminate()
            try:
                self.worker.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Worker didn't terminate, killing...")
                self.worker.kill()
                self.worker.wait()

        # 환경 변수 준비
        env = os.environ.copy()

        # PYTHONPATH 설정 - AI helpers를 위한 python 디렉토리 추가
        python_dir = os.path.join(os.getcwd(), 'python')
        current_paths = sys.path.copy()
        if python_dir not in current_paths:
            current_paths.insert(0, python_dir)
        env['PYTHONPATH'] = os.pathsep.join(current_paths)

        # UTF-8 강제
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUTF8'] = '1'

        # 워커 프로세스 시작
        logger.info(f"Starting worker: {self.worker_script_path}")
        self.worker = subprocess.Popen(
            [sys.executable, '-u', self.worker_script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0,
            cwd=os.getcwd(),
            env=env
        )

        # stdout 읽기 스레드
        self.stdout_thread = threading.Thread(
            target=self._read_stdout,
            daemon=True
        )
        self.stdout_thread.start()

        # stderr 읽기 스레드
        self.stderr_thread = threading.Thread(
            target=self._read_stderr,
            daemon=True
        )
        self.stderr_thread.start()

        # 워커 시작 확인
        time.sleep(0.1)
        if self.worker.poll() is None:
            logger.info("Worker started successfully")
        else:
            raise RuntimeError("Worker failed to start")

    def _read_stdout(self):
        """stdout에서 응답 읽기"""
        while True:
            if not self.worker or self.worker.poll() is not None:
                break

            try:
                line = self.worker.stdout.readline()
                if not line:
                    break

                line = line.strip()
                if line.startswith('{') and line.endswith('}'):
                    try:
                        response = json.loads(line)
                        self.response_queue.put(response)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON from worker: {line}")
            except Exception as e:
                logger.error(f"Error reading stdout: {e}")
                break

    def _read_stderr(self):
        """stderr 모니터링"""
        while True:
            if not self.worker or self.worker.poll() is not None:
                break

            try:
                line = self.worker.stderr.readline()
                if not line:
                    break

                line = line.strip()
                if line:
                    self.stderr_queue.put(line)
                    logger.debug(f"Worker stderr: {line}")
            except Exception as e:
                logger.error(f"Error reading stderr: {e}")
                break

    def execute(self, code: str, timeout: float = 30.0) -> Dict[str, Any]:
        """코드 실행"""
        if not self.worker or self.worker.poll() is not None:
            logger.warning("Worker not running, restarting...")
            self.start_worker()

        # 요청 생성
        self.request_id += 1
        request = {
            'id': f'req_{self.request_id}',
            'code': code
        }

        # 기존 응답 큐 비우기
        while not self.response_queue.empty():
            self.response_queue.get_nowait()

        # 요청 전송
        try:
            self.worker.stdin.write(json.dumps(request) + '\n')
            self.worker.stdin.flush()
        except Exception as e:
            logger.error(f"Failed to send request: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }

        # 타임아웃 타이머
        timer = threading.Timer(timeout, self._handle_timeout, args=[request['id']])
        timer.start()
        self.active_request = request['id']

        try:
            # 응답 대기
            response = self.response_queue.get(timeout=timeout)
            timer.cancel()

            # stderr 메시지 수집
            stderr_messages = []
            while not self.stderr_queue.empty():
                stderr_messages.append(self.stderr_queue.get_nowait())

            if stderr_messages:
                response['stderr_messages'] = stderr_messages

            return response

        except queue.Empty:
            timer.cancel()
            return {
                'success': False,
                'error': f'Timeout after {timeout}s',
                'error_type': 'TimeoutError'
            }
        finally:
            self.active_request = None

    def _handle_timeout(self, request_id: str):
        """타임아웃 처리"""
        if self.active_request == request_id:
            logger.warning(f"Request {request_id} timed out")
            logger.info("Killing worker due to timeout...")
            self.worker.kill()
            self.worker.wait()
            self.start_worker()

    def shutdown(self):
        """종료"""
        if self.worker and self.worker.poll() is None:
            self.worker.terminate()
            try:
                self.worker.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.worker.kill()
                self.worker.wait()
            logger.info("Worker shut down")
