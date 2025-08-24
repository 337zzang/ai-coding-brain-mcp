"""
Background System Enhancements
백그라운드 시스템 추가 기능

Version: 1.0.0
Author: Claude Code
Created: 2025-08-24

우선순위, 의존성, 스케줄링 등 고급 기능 추가
"""

from typing import Dict, Any, Optional, Callable, List, Set
import time
import threading
from datetime import datetime, timedelta
from .background_facade import BackgroundFacade
from .message import message_facade
from .api_response import ok, err

class EnhancedBackgroundFacade(BackgroundFacade):
    """
    향상된 백그라운드 Facade
    
    추가 기능:
    - 작업 우선순위 관리
    - 일시정지/재개
    - 의존성 관리
    - 스케줄링
    - 실시간 로그
    """
    
    def __init__(self):
        super().__init__()
        self.priorities = {}  # task_id -> priority (0-10)
        self.paused_tasks = set()  # 일시정지된 작업들
        self.dependencies = {}  # task_id -> [dependency_ids]
        self.scheduled_tasks = []  # 예약된 작업들
        self.task_logs = {}  # task_id -> [log_entries]
        
    # ========== 우선순위 관리 ==========
    
    def run_priority(self, func: Callable, priority: int = 5, *args, **kwargs) -> Dict[str, Any]:
        """
        우선순위를 지정한 백그라운드 실행
        
        Args:
            func: 실행할 함수
            priority: 우선순위 (0=낮음, 10=높음)
        
        Examples:
            >>> h.bg.run_priority(critical_task, priority=10)
            >>> h.bg.run_priority(background_task, priority=2)
        """
        import uuid
        task_id = f"pri_{priority}_{uuid.uuid4().hex[:6]}"
        
        self.priorities[task_id] = priority
        self.manager.register_task(task_id, func, *args, **kwargs)
        
        # 우선순위에 따라 실행 조정
        if priority >= 8:
            # 높은 우선순위는 즉시 실행
            self.message.task(f"🔴 고우선순위 작업: {task_id}")
            return self.manager.run_async(task_id)
        else:
            # 낮은 우선순위는 대기
            self.message.task(f"🔵 일반 작업 대기: {task_id}")
            threading.Timer(0.5, lambda: self.manager.run_async(task_id)).start()
            return ok({'task_id': task_id, 'priority': priority})
    
    # ========== 일시정지/재개 ==========
    
    def pause(self, task_id: str) -> Dict[str, Any]:
        """
        작업 일시정지 (플래그만 설정, 실제 중단은 작업이 체크해야 함)
        
        Examples:
            >>> h.bg.pause("task_123")
        """
        if task_id not in self.manager.tasks:
            return err(f"작업을 찾을 수 없음: {task_id}")
        
        self.paused_tasks.add(task_id)
        self.message.task(f"⏸️ 일시정지: {task_id}", level="WARNING")
        return ok({'paused': task_id})
    
    def resume(self, task_id: str) -> Dict[str, Any]:
        """
        작업 재개
        
        Examples:
            >>> h.bg.resume("task_123")
        """
        if task_id not in self.paused_tasks:
            return err(f"일시정지된 작업이 아님: {task_id}")
        
        self.paused_tasks.remove(task_id)
        self.message.task(f"▶️ 재개: {task_id}", level="SUCCESS")
        return ok({'resumed': task_id})
    
    def is_paused(self, task_id: str) -> bool:
        """작업이 일시정지 상태인지 확인"""
        return task_id in self.paused_tasks
    
    # ========== 의존성 관리 ==========
    
    def run_with_deps(self, func: Callable, depends_on: List[str], 
                      *args, **kwargs) -> Dict[str, Any]:
        """
        의존성이 있는 작업 실행 (의존 작업이 완료되면 실행)
        
        Args:
            func: 실행할 함수
            depends_on: 먼저 완료되어야 할 작업 ID 리스트
        
        Examples:
            >>> task1 = h.bg.run(preprocess)
            >>> task2 = h.bg.run_with_deps(
            ...     process,
            ...     depends_on=[task1['data']['task_id']]
            ... )
        """
        import uuid
        task_id = f"dep_{uuid.uuid4().hex[:6]}"
        
        self.dependencies[task_id] = depends_on
        
        def wrapper():
            # 의존성 대기
            for dep_id in depends_on:
                self.message.task(f"⏳ {task_id}: {dep_id} 대기 중")
                result = self.manager.wait_for(dep_id, timeout=60)
                if not result['ok']:
                    return err(f"의존성 실패: {dep_id}")
            
            # 실제 작업 실행
            self.message.task(f"✅ {task_id}: 의존성 충족, 실행 시작")
            return func(*args, **kwargs)
        
        self.manager.register_task(task_id, wrapper)
        self.manager.run_async(task_id)
        
        return ok({
            'task_id': task_id,
            'depends_on': depends_on
        })
    
    # ========== 스케줄링 ==========
    
    def schedule(self, func: Callable, delay: float = None, 
                 at_time: datetime = None, *args, **kwargs) -> Dict[str, Any]:
        """
        작업 예약 실행
        
        Args:
            func: 실행할 함수
            delay: 지연 시간 (초) 또는
            at_time: 실행 시각
        
        Examples:
            >>> h.bg.schedule(backup_data, delay=3600)  # 1시간 후
            >>> h.bg.schedule(daily_report, at_time=tomorrow_9am)
        """
        import uuid
        task_id = f"sched_{uuid.uuid4().hex[:6]}"
        
        if at_time:
            delay = (at_time - datetime.now()).total_seconds()
            if delay < 0:
                return err("예약 시간이 과거입니다")
        elif delay is None:
            return err("delay 또는 at_time이 필요합니다")
        
        def scheduled_wrapper():
            time.sleep(delay)
            self.message.task(f"⏰ 예약 작업 시작: {task_id}")
            return func(*args, **kwargs)
        
        self.manager.register_task(task_id, scheduled_wrapper)
        self.manager.run_async(task_id)
        
        run_time = datetime.now() + timedelta(seconds=delay)
        self.scheduled_tasks.append({
            'task_id': task_id,
            'run_time': run_time.isoformat()
        })
        
        self.message.task(
            f"📅 예약됨: {task_id} → {run_time.strftime('%H:%M:%S')}"
        )
        
        return ok({
            'task_id': task_id,
            'scheduled_for': run_time.isoformat()
        })
    
    def cron(self, func: Callable, interval: float, max_runs: int = None) -> Dict[str, Any]:
        """
        반복 작업 실행
        
        Args:
            func: 실행할 함수
            interval: 실행 간격 (초)
            max_runs: 최대 실행 횟수 (None이면 무한)
        
        Examples:
            >>> h.bg.cron(check_status, interval=60, max_runs=10)
        """
        import uuid
        cron_id = f"cron_{uuid.uuid4().hex[:6]}"
        runs = [0]  # 실행 횟수 (리스트로 만들어 클로저에서 수정 가능)
        
        def cron_wrapper():
            while max_runs is None or runs[0] < max_runs:
                if cron_id in self.paused_tasks:
                    time.sleep(1)
                    continue
                
                runs[0] += 1
                self.message.task(f"🔄 반복 실행 {cron_id}: {runs[0]}회")
                
                try:
                    func()
                except Exception as e:
                    self.message.task(f"❌ 반복 작업 에러: {e}", level="ERROR")
                
                time.sleep(interval)
            
            self.message.task(f"✅ 반복 작업 완료: {cron_id}", level="SUCCESS")
        
        self.manager.register_task(cron_id, cron_wrapper)
        self.manager.run_async(cron_id)
        
        return ok({
            'cron_id': cron_id,
            'interval': interval,
            'max_runs': max_runs
        })
    
    # ========== 실시간 로그 ==========
    
    def log(self, task_id: str, message: str) -> None:
        """
        작업 로그 추가
        
        Examples:
            >>> h.bg.log("task_123", "처리 중: 50%")
        """
        if task_id not in self.task_logs:
            self.task_logs[task_id] = []
        
        entry = {
            'time': datetime.now().isoformat(),
            'message': message
        }
        self.task_logs[task_id].append(entry)
        
        # 실시간 출력 옵션
        if self.get("show_logs"):
            print(f"[LOG {task_id}] {message}")
    
    def get_logs(self, task_id: str, last_n: int = None) -> List[Dict[str, str]]:
        """
        작업 로그 가져오기
        
        Args:
            task_id: 작업 ID
            last_n: 최근 N개만 가져오기
        
        Examples:
            >>> h.bg.get_logs("task_123", last_n=10)
        """
        logs = self.task_logs.get(task_id, [])
        
        if last_n:
            return logs[-last_n:]
        return logs
    
    def stream_logs(self, task_id: str, callback: Callable = None):
        """
        로그 스트리밍 (새 로그가 추가되면 콜백 호출)
        
        Examples:
            >>> h.bg.stream_logs("task_123", print)
        """
        if callback is None:
            callback = print
        
        last_index = 0
        
        def streamer():
            nonlocal last_index
            while task_id in self.manager.tasks:
                logs = self.task_logs.get(task_id, [])
                
                # 새 로그만 출력
                for log in logs[last_index:]:
                    callback(f"[{log['time']}] {log['message']}")
                
                last_index = len(logs)
                time.sleep(0.5)
        
        # 스트리밍을 별도 스레드로
        thread = threading.Thread(target=streamer, daemon=True)
        thread.start()
        
        return ok({'streaming': task_id})
    
    # ========== 고급 상태 관리 ==========
    
    def get_queue_status(self) -> Dict[str, Any]:
        """
        작업 큐 상태 (우선순위별)
        """
        by_priority = {}
        
        for task_id, priority in self.priorities.items():
            if priority not in by_priority:
                by_priority[priority] = []
            by_priority[priority].append(task_id)
        
        return ok({
            'by_priority': by_priority,
            'paused': list(self.paused_tasks),
            'scheduled': self.scheduled_tasks,
            'with_dependencies': list(self.dependencies.keys())
        })
    
    def clear_all(self) -> Dict[str, Any]:
        """
        모든 작업 및 상태 초기화
        """
        count = len(self.manager.tasks)
        
        # 모든 상태 초기화
        self.manager.tasks.clear()
        self.manager.results.clear()
        self.manager.threads.clear()
        self.priorities.clear()
        self.paused_tasks.clear()
        self.dependencies.clear()
        self.scheduled_tasks.clear()
        self.task_logs.clear()
        self.persistent_vars.clear()
        
        self.message.task(f"🗑️ 모든 작업 초기화: {count}개", level="WARNING")
        
        return ok({'cleared': count})

# 싱글톤 인스턴스
enhanced_bg = EnhancedBackgroundFacade()