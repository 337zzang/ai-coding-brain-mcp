"""
Background Task Manager for REPL
REPL용 백그라운드 태스크 매니저

Version: 1.0.0
Author: Claude Code
Created: 2025-08-24

백그라운드 실행, 비동기 처리, 진행 상황 추적을 위한 통합 모듈
"""

import threading
import queue
import time
from typing import Dict, Any, Optional, Callable, List, Tuple
from datetime import datetime
from .api_response import ok, err
from .message import message_facade

class BackgroundTaskManager:
    """
    동기/비동기 백그라운드 태스크 관리자

    주요 기능:
    - 백그라운드 태스크 등록 및 실행
    - 진행 상황 실시간 추적
    - 결과 캐싱 및 관리
    - 오류 처리 및 복구
    """

    def __init__(self):
        self.tasks = {}
        self.results = {}
        self.threads = {}
        self.queue = queue.Queue()
        self.message = message_facade

    def register_task(self, task_id: str, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        태스크 등록

        Args:
            task_id: 태스크 고유 ID
            func: 실행할 함수
            *args: 함수 인자
            **kwargs: 함수 키워드 인자

        Returns:
            {'ok': True, 'data': task_id}
        """
        try:
            self.tasks[task_id] = {
                'func': func,
                'args': args,
                'kwargs': kwargs,
                'status': 'pending',
                'start_time': None,
                'end_time': None,
                'result': None,
                'error': None
            }

            self.message.share(f"태스크 등록: {task_id}", {
                'id': task_id,
                'func': func.__name__ if hasattr(func, '__name__') else str(func)
            })

            return ok(task_id)

        except Exception as e:
            return err(f"태스크 등록 실패: {str(e)}")

    def run_sync(self, task_id: str) -> Dict[str, Any]:
        """
        동기 실행 (현재 스레드에서 실행)

        Args:
            task_id: 실행할 태스크 ID

        Returns:
            {'ok': True, 'data': result} or {'ok': False, 'error': msg}
        """
        if task_id not in self.tasks:
            return err(f"태스크 {task_id} 없음")

        task = self.tasks[task_id]
        task['status'] = 'running'
        task['start_time'] = datetime.now()

        self.message.task(f"태스크 시작: {task_id}")

        try:
            result = task['func'](*task['args'], **task['kwargs'])

            task['status'] = 'completed'
            task['result'] = result
            task['end_time'] = datetime.now()
            elapsed = (task['end_time'] - task['start_time']).total_seconds()

            self.results[task_id] = result
            self.message.task(f"태스크 완료: {task_id} ({elapsed:.2f}초)", level="SUCCESS")

            return ok(result)

        except Exception as e:
            task['status'] = 'failed'
            task['error'] = str(e)
            task['end_time'] = datetime.now()

            self.message.task(f"태스크 실패: {task_id} - {e}", level="ERROR")
            return err(str(e))

    def run_async(self, task_id: str) -> Dict[str, Any]:
        """
        비동기 실행 (백그라운드 스레드에서 실행)

        Args:
            task_id: 실행할 태스크 ID

        Returns:
            {'ok': True, 'data': {'task_id': task_id, 'thread': thread_name}}
        """
        if task_id not in self.tasks:
            return err(f"태스크 {task_id} 없음")

        def worker():
            task = self.tasks[task_id]
            task['status'] = 'running'
            task['start_time'] = datetime.now()

            self.message.task(f"🚀 백그라운드 시작: {task_id}")

            try:
                result = task['func'](*task['args'], **task['kwargs'])

                task['status'] = 'completed'
                task['result'] = result
                task['end_time'] = datetime.now()
                elapsed = (task['end_time'] - task['start_time']).total_seconds()

                self.results[task_id] = result
                self.queue.put({
                    'task_id': task_id,
                    'status': 'completed',
                    'result': result,
                    'elapsed': elapsed
                })

                self.message.task(
                    f"✅ 백그라운드 완료: {task_id} ({elapsed:.2f}초)",
                    level="SUCCESS"
                )

            except Exception as e:
                task['status'] = 'failed'
                task['error'] = str(e)
                task['end_time'] = datetime.now()

                self.queue.put({
                    'task_id': task_id,
                    'status': 'failed',
                    'error': str(e)
                })

                self.message.task(
                    f"❌ 백그라운드 실패: {task_id} - {e}",
                    level="ERROR"
                )

        thread = threading.Thread(target=worker, name=f"worker-{task_id}")
        thread.daemon = True
        self.threads[task_id] = thread
        thread.start()

        return ok({
            'task_id': task_id,
            'thread': thread.name
        })

    def check_results(self) -> Dict[str, Any]:
        """
        완료된 백그라운드 작업 결과 확인

        Returns:
            {'ok': True, 'data': [results]}
        """
        results = []
        while not self.queue.empty():
            try:
                result = self.queue.get_nowait()
                results.append(result)
            except queue.Empty:
                break

        return ok(results)

    def get_status(self, task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        태스크 상태 확인

        Args:
            task_id: 특정 태스크 ID (None이면 전체)

        Returns:
            {'ok': True, 'data': status_info}
        """
        if task_id:
            if task_id not in self.tasks:
                return err(f"태스크 {task_id} 없음")

            task = self.tasks[task_id]
            return ok({
                'id': task_id,
                'status': task['status'],
                'start_time': task['start_time'].isoformat() if task['start_time'] else None,
                'end_time': task['end_time'].isoformat() if task['end_time'] else None,
                'has_result': task_id in self.results,
                'has_error': task['error'] is not None
            })
        else:
            # 전체 상태
            status = {
                'pending': [],
                'running': [],
                'completed': [],
                'failed': []
            }

            for tid, task in self.tasks.items():
                status[task['status']].append(tid)

            return ok(status)

    def get_active_threads(self) -> Dict[str, Any]:
        """
        활성 스레드 목록

        Returns:
            {'ok': True, 'data': [active_task_ids]}
        """
        active = []
        for task_id, thread in self.threads.items():
            if thread.is_alive():
                active.append(task_id)

        return ok(active)

    def get_result(self, task_id: str) -> Dict[str, Any]:
        """
        특정 태스크 결과 가져오기

        Args:
            task_id: 태스크 ID

        Returns:
            {'ok': True, 'data': result} or {'ok': False, 'error': msg}
        """
        if task_id not in self.results:
            return err(f"결과 없음: {task_id}")

        return ok(self.results[task_id])

    def clear_completed(self) -> Dict[str, Any]:
        """
        완료된 태스크 정리

        Returns:
            {'ok': True, 'data': {'cleared': count}}
        """
        completed = [tid for tid, task in self.tasks.items() 
                    if task['status'] in ['completed', 'failed']]

        for task_id in completed:
            if task_id in self.tasks:
                del self.tasks[task_id]
            if task_id in self.threads:
                del self.threads[task_id]

        return ok({'cleared': len(completed)})

    def wait_for(self, task_id: str, timeout: float = 10.0) -> Dict[str, Any]:
        """
        특정 태스크 완료 대기

        Args:
            task_id: 대기할 태스크 ID
            timeout: 최대 대기 시간 (초)

        Returns:
            {'ok': True, 'data': result} or {'ok': False, 'error': msg}
        """
        if task_id not in self.threads:
            return err(f"백그라운드 태스크 아님: {task_id}")

        thread = self.threads[task_id]
        thread.join(timeout)

        if thread.is_alive():
            return err(f"타임아웃: {task_id}")

        return self.get_result(task_id)

# 전역 인스턴스 생성
background_manager = BackgroundTaskManager()

# 간편 함수들
def run_in_background(func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """
    함수를 백그라운드로 실행 (간편 API)

    Examples:
        >>> run_in_background(heavy_calculation, 1000)
        >>> run_in_background(lambda x: x**2, 10)
    """
    import uuid
    task_id = f"bg_{uuid.uuid4().hex[:8]}"

    result = background_manager.register_task(task_id, func, *args, **kwargs)
    if not result['ok']:
        return result

    return background_manager.run_async(task_id)

def get_background_results() -> Dict[str, Any]:
    """백그라운드 결과 확인 (간편 API)"""
    return background_manager.check_results()

def get_background_status() -> Dict[str, Any]:
    """백그라운드 상태 확인 (간편 API)"""
    return background_manager.get_status()

def wait_for_all(timeout: float = 30.0) -> Dict[str, Any]:
    """
    모든 백그라운드 작업 완료 대기

    Args:
        timeout: 최대 대기 시간

    Returns:
        {'ok': True, 'data': {'completed': count}}
    """
    start = time.time()

    while time.time() - start < timeout:
        active = background_manager.get_active_threads()['data']
        if not active:
            break
        time.sleep(0.5)

    results = background_manager.check_results()['data']
    return ok({'completed': len(results), 'results': results})
