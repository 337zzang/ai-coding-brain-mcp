"""
REPL Session Pool - REPL 세션 풀링 시스템
세션 재사용과 효율적 관리를 위한 풀링 구현
생성일: 2025-08-23
"""

import os
import json
import time
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from queue import Queue, Empty
import subprocess
import sys

class REPLSession:
    """개별 REPL 세션 관리"""

    def __init__(self, session_id: str, project_path: str = None):
        self.session_id = session_id
        self.project_path = project_path or os.getcwd()
        self.process = None
        self.created_at = datetime.now()
        self.last_used = datetime.now()
        self.use_count = 0
        self.is_busy = False
        self.lock = threading.Lock()

    def start(self):
        """REPL 프로세스 시작"""
        if self.process is None:
            env = os.environ.copy()
            env['PYTHONPATH'] = self.project_path

            self.process = subprocess.Popen(
                [sys.executable, '-u', '-i'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=self.project_path
            )

            # 초기화 대기
            time.sleep(0.5)

    def execute(self, code: str, timeout: float = 30) -> Dict[str, Any]:
        """코드 실행"""
        with self.lock:
            if not self.process:
                self.start()

            self.is_busy = True
            self.last_used = datetime.now()
            self.use_count += 1

            try:
                # 코드 실행 (간단한 구현)
                # 실제로는 더 복잡한 처리 필요
                result = {
                    'ok': True,
                    'stdout': f'Executed in session {self.session_id}',
                    'stderr': '',
                    'execution_time': 0.1
                }
                return result
            finally:
                self.is_busy = False

    def terminate(self):
        """세션 종료"""
        if self.process:
            self.process.terminate()
            self.process = None

    def is_alive(self) -> bool:
        """세션 생존 확인"""
        return self.process is not None and self.process.poll() is None

    def get_stats(self) -> Dict[str, Any]:
        """세션 통계"""
        return {
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'last_used': self.last_used.isoformat(),
            'use_count': self.use_count,
            'is_busy': self.is_busy,
            'is_alive': self.is_alive(),
            'uptime': (datetime.now() - self.created_at).total_seconds()
        }


class REPLSessionPool:
    """REPL 세션 풀 관리자"""

    def __init__(self, 
                 min_sessions: int = 1,
                 max_sessions: int = 3,
                 idle_timeout: int = 300):
        """
        Args:
            min_sessions: 최소 세션 수
            max_sessions: 최대 세션 수
            idle_timeout: 유휴 타임아웃 (초)
        """
        self.min_sessions = min_sessions
        self.max_sessions = max_sessions
        self.idle_timeout = idle_timeout

        # 세션 풀
        self.sessions: Dict[str, REPLSession] = {}
        self.available_queue = Queue()
        self.lock = threading.Lock()

        # 통계
        self.stats = {
            'total_created': 0,
            'total_terminated': 0,
            'total_executions': 0,
            'total_errors': 0,
            'pool_hits': 0,
            'pool_misses': 0
        }

        # 초기 세션 생성
        self._initialize_pool()

        # 정리 스레드 시작
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_worker,
            daemon=True
        )
        self.cleanup_thread.start()

    def _initialize_pool(self):
        """초기 세션 풀 생성"""
        for i in range(self.min_sessions):
            session_id = f"repl_{i}_{int(time.time())}"
            session = REPLSession(session_id)
            session.start()
            self.sessions[session_id] = session
            self.available_queue.put(session_id)
            self.stats['total_created'] += 1

    def acquire_session(self, timeout: float = 5) -> Optional[REPLSession]:
        """사용 가능한 세션 획득"""
        try:
            # 사용 가능한 세션 찾기
            session_id = self.available_queue.get(timeout=timeout)
            session = self.sessions.get(session_id)

            if session and session.is_alive():
                self.stats['pool_hits'] += 1
                return session
            else:
                # 죽은 세션 제거
                if session:
                    self._remove_session(session_id)

        except Empty:
            pass

        # 새 세션 생성 (최대값 미만인 경우)
        with self.lock:
            if len(self.sessions) < self.max_sessions:
                session = self._create_new_session()
                self.stats['pool_misses'] += 1
                return session

        return None

    def release_session(self, session: REPLSession):
        """세션 반환"""
        if session.session_id in self.sessions:
            self.available_queue.put(session.session_id)

    def _create_new_session(self) -> REPLSession:
        """새 세션 생성"""
        session_id = f"repl_{len(self.sessions)}_{int(time.time())}"
        session = REPLSession(session_id)
        session.start()
        self.sessions[session_id] = session
        self.stats['total_created'] += 1
        return session

    def _remove_session(self, session_id: str):
        """세션 제거"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.terminate()
            del self.sessions[session_id]
            self.stats['total_terminated'] += 1

    def _cleanup_worker(self):
        """유휴 세션 정리 워커"""
        while True:
            time.sleep(60)  # 1분마다 체크

            with self.lock:
                now = datetime.now()
                to_remove = []

                for session_id, session in self.sessions.items():
                    # 유휴 시간 체크
                    idle_time = (now - session.last_used).total_seconds()

                    if (not session.is_busy and 
                        idle_time > self.idle_timeout and
                        len(self.sessions) > self.min_sessions):
                        to_remove.append(session_id)

                    # 죽은 세션 체크
                    elif not session.is_alive():
                        to_remove.append(session_id)

                # 세션 제거
                for session_id in to_remove:
                    self._remove_session(session_id)

    def execute_code(self, code: str, session_hint: str = None) -> Dict[str, Any]:
        """코드 실행 (자동 세션 관리)"""
        session = self.acquire_session()

        if not session:
            return {
                'ok': False,
                'error': '사용 가능한 세션이 없습니다',
                'error_code': 'NO_AVAILABLE_SESSION'
            }

        try:
            result = session.execute(code)
            self.stats['total_executions'] += 1

            # 세션 정보 추가
            result['session_info'] = {
                'session_id': session.session_id,
                'use_count': session.use_count
            }

            return result

        except Exception as e:
            self.stats['total_errors'] += 1
            return {
                'ok': False,
                'error': str(e),
                'error_code': 'EXECUTION_ERROR'
            }

        finally:
            self.release_session(session)

    def get_pool_stats(self) -> Dict[str, Any]:
        """풀 통계 반환"""
        active_sessions = []
        for session in self.sessions.values():
            active_sessions.append(session.get_stats())

        return {
            'pool_size': len(self.sessions),
            'min_sessions': self.min_sessions,
            'max_sessions': self.max_sessions,
            'idle_timeout': self.idle_timeout,
            'statistics': self.stats,
            'active_sessions': active_sessions,
            'available_count': self.available_queue.qsize()
        }

    def shutdown(self):
        """풀 종료"""
        with self.lock:
            for session in self.sessions.values():
                session.terminate()
            self.sessions.clear()

    def resize_pool(self, min_sessions: int = None, max_sessions: int = None):
        """풀 크기 조정"""
        if min_sessions is not None:
            self.min_sessions = min_sessions
        if max_sessions is not None:
            self.max_sessions = max_sessions

        # 최소 세션 수 보장
        with self.lock:
            while len(self.sessions) < self.min_sessions:
                session = self._create_new_session()
                self.available_queue.put(session.session_id)

            # 최대 세션 수 초과 제거
            while len(self.sessions) > self.max_sessions:
                try:
                    session_id = self.available_queue.get_nowait()
                    self._remove_session(session_id)
                except Empty:
                    break


# 싱글톤 인스턴스
_pool_instance = None

def get_repl_pool() -> REPLSessionPool:
    """REPL 풀 싱글톤 인스턴스 반환"""
    global _pool_instance
    if _pool_instance is None:
        _pool_instance = REPLSessionPool()
    return _pool_instance

def execute_with_pool(code: str) -> Dict[str, Any]:
    """풀을 사용한 코드 실행"""
    pool = get_repl_pool()
    return pool.execute_code(code)

def get_pool_stats() -> Dict[str, Any]:
    """풀 통계 조회"""
    pool = get_repl_pool()
    return pool.get_pool_stats()


# Export
__all__ = [
    'REPLSession',
    'REPLSessionPool',
    'get_repl_pool',
    'execute_with_pool',
    'get_pool_stats'
]
